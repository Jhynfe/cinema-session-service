import asyncio

from fastapi import WebSocket


class ConnectionManager:
    """Mantiene los WebSockets conectados a cada sala para difundir eventos:
    cambios de playback (play/pause/seek), chat, entradas/salidas de miembros.
    """

    def __init__(self):
        self._connections: dict[str, dict[int, WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(session_id, {})[user_id] = websocket

    async def disconnect(self, session_id: str, user_id: int) -> None:
        async with self._lock:
            room = self._connections.get(session_id)
            if room:
                room.pop(user_id, None)
                if not room:
                    self._connections.pop(session_id, None)

    async def broadcast(self, session_id: str, message: dict) -> None:
        room = self._connections.get(session_id, {})
        for websocket in list(room.values()):
            try:
                await websocket.send_json(message)
            except Exception:
                # Si un socket falló, se limpiará en su propio disconnect.
                continue
