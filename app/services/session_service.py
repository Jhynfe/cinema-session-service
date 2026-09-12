from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.config import settings
from app.models.session import (
    CinemaSession,
    Participant,
    ParticipantRole,
    SessionStatus,
)
from app.repositories.session_repository import SessionRepository
from app.schemas.session import SessionCreate
from app.services.connection_manager import ConnectionManager


class SessionService:
    def __init__(self, repository: SessionRepository, manager: ConnectionManager):
        self.repository = repository
        self.manager = manager

    # ---- Sesiones -------------------------------------------------

    def create_session(self, payload: SessionCreate, host_id: int) -> CinemaSession:
        session = CinemaSession(
            movie_id=payload.movie_id,
            title=payload.title,
            host_id=host_id,
            max_participants=payload.max_participants or settings.MAX_PARTICIPANTS_PER_SESSION,
        )
        session.participants[host_id] = Participant(
            user_id=host_id, role=ParticipantRole.HOST
        )
        self.repository.add(session)
        return session

    def get_session(self, session_id: str) -> CinemaSession:
        session = self.repository.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        return session

    def list_sessions(
        self, status: SessionStatus | None, skip: int = 0, limit: int = 50
    ) -> list[CinemaSession]:
        return self.repository.list(status=status, skip=skip, limit=limit)

    async def end_session(self, session_id: str, user_id: int) -> None:
        session = self.get_session(session_id)
        self._require_host(session, user_id)
        session.status = SessionStatus.ENDED
        session.is_playing = False
        session.touch()
        await self.manager.broadcast(
            session_id, {"type": "SESSION_ENDED", "session_id": session_id}
        )
        self.repository.delete(session_id)

    # ---- Participantes ---------------------------------------------

    async def join_session(self, session_id: str, user_id: int) -> CinemaSession:
        session = self.get_session(session_id)
        if session.status == SessionStatus.ENDED:
            raise HTTPException(status_code=409, detail="La sesión ya terminó")
        if user_id in session.participants:
            raise HTTPException(status_code=409, detail="Ya estás en esta sesión")
        if len(session.participants) >= session.max_participants:
            raise HTTPException(status_code=409, detail="La sala está llena")

        session.participants[user_id] = Participant(
            user_id=user_id, role=ParticipantRole.GUEST
        )
        session.touch()
        await self.manager.broadcast(
            session_id, {"type": "MEMBER_JOINED", "user_id": user_id}
        )
        return session

    async def leave_session(self, session_id: str, user_id: int) -> None:
        session = self.get_session(session_id)
        participant = session.participants.get(user_id)
        if not participant:
            raise HTTPException(status_code=404, detail="No perteneces a esta sesión")
        if participant.role == ParticipantRole.HOST:
            raise HTTPException(
                status_code=400,
                detail="El HOST no puede salir; usa 'terminar sesión' en su lugar",
            )

        del session.participants[user_id]
        session.touch()
        await self.manager.broadcast(
            session_id, {"type": "MEMBER_LEFT", "user_id": user_id}
        )

    def list_members(self, session_id: str) -> list[Participant]:
        session = self.get_session(session_id)
        return list(session.participants.values())

    # ---- Playback (control del HOST) --------------------------------

    async def update_playback(
        self, session_id: str, user_id: int, is_playing: bool, position_seconds: float
    ) -> CinemaSession:
        session = self.get_session(session_id)
        self._require_host(session, user_id)

        session.is_playing = is_playing
        session.position_seconds = position_seconds
        session.status = SessionStatus.PLAYING if is_playing else SessionStatus.PAUSED
        session.touch()

        await self.manager.broadcast(
            session_id,
            {
                "type": "PLAYBACK_UPDATE",
                "is_playing": is_playing,
                "position_seconds": position_seconds,
                "updated_at": session.updated_at.isoformat(),
            },
        )
        return session

    async def send_chat_message(self, session_id: str, user_id: int, message: str) -> None:
        session = self.get_session(session_id)
        if user_id not in session.participants:
            raise HTTPException(status_code=403, detail="No perteneces a esta sesión")

        await self.manager.broadcast(
            session_id,
            {
                "type": "CHAT_MESSAGE",
                "user_id": user_id,
                "message": message,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    # ---- Helpers -----------------------------------------------------

    @staticmethod
    def _require_host(session: CinemaSession, user_id: int) -> None:
        if session.host_id != user_id:
            raise HTTPException(
                status_code=403, detail="Solo el HOST puede realizar esta acción"
            )
