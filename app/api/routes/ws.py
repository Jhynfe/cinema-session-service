from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
import requests
from app.core.config import settings

from app.api.deps import (
    get_connection_manager,
    get_current_user_id_ws,
    get_session_repository,
)
from app.services.connection_manager import ConnectionManager
from app.services.session_service import SessionService

router = APIRouter()


@router.websocket("/{session_id}/ws")
async def session_websocket(
    websocket: WebSocket,
    session_id: str,
    token: str | None = Query(default=None),
):
    """Canal en tiempo real de la sala: difunde play/pause/seek y chat a
    todos los participantes conectados. El token JWT llega como query param
    porque el navegador no permite headers personalizados en el handshake
    de WebSocket.
    """
    try:
        user_id = get_current_user_id_ws(token)
    except InvalidTokenError:
        await websocket.close(code=4401)
        return

    repository = get_session_repository()
    manager = get_connection_manager()
    service = SessionService(repository, manager)

    session = repository.get(session_id)
    if not session or user_id not in session.participants:
        await websocket.close(code=4403)
        return

    await manager.connect(session_id, user_id, websocket)
    
    # [Option B] Estadisticas Globales de Interaction Service
    try:
        stat_resp = requests.get(f"{settings.INTERACTION_SERVICE_URL}/api/v1/interactions/movies/{session.movie_id}/stats", timeout=2)
        if stat_resp.status_code == 200:
            stats = stat_resp.json()
            likes = stats.get("likes", 0)
            avg = stats.get("average_score") or "N/A"
            await websocket.send_json({
                "type": "CHAT_MESSAGE",
                "user_id": "🤖 Bot",
                "message": f"📊 Datos de la comunidad: Esta película tiene {likes} likes y un rating de {avg}/5.",
                "sent_at": "now"
            })
    except Exception:
        pass

    # [Option C] Alerta de Fan (si le dio like)
    try:
        like_resp = requests.get(f"{settings.INTERACTION_SERVICE_URL}/api/v1/interactions/users/{user_id}/likes", timeout=2)
        if like_resp.status_code == 200:
            likes_data = like_resp.json()
            if session.movie_id in likes_data.get("items", []):
                await manager.broadcast(session_id, {
                    "type": "CHAT_MESSAGE",
                    "user_id": "🤖 Bot",
                    "message": f"⭐ ¡El fanático {user_id} se ha unido a la órbita!",
                    "sent_at": "now"
                })
    except Exception:
        pass

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")

            try:
                if event_type == "CHAT_MESSAGE":
                    await service.send_chat_message(
                        session_id, user_id, data.get("message", "")
                    )
                elif event_type == "PLAYBACK_UPDATE":
                    await service.update_playback(
                        session_id,
                        user_id,
                        is_playing=bool(data.get("is_playing", False)),
                        position_seconds=float(data.get("position_seconds", 0)),
                    )
                # Otros tipos de evento se ignoran silenciosamente por ahora.
            except HTTPException as exc:
                await websocket.send_json({"type": "ERROR", "detail": exc.detail})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(session_id, user_id)
