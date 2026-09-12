from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError

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
