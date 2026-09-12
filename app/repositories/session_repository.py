import threading

from app.models.session import CinemaSession, SessionStatus


class SessionRepository:
    """Almacén en memoria de las salas de cine grupales.

    A diferencia de Community Service, este microservicio no requiere una
    base de datos: las sesiones son efímeras (duran lo que dura la
    "función" en vivo), así que un dict protegido por un lock es suficiente
    para el alcance del proyecto.
    """

    def __init__(self):
        self._sessions: dict[str, CinemaSession] = {}
        self._lock = threading.Lock()

    def add(self, session: CinemaSession) -> CinemaSession:
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> CinemaSession | None:
        return self._sessions.get(session_id)

    def list(
        self,
        status: SessionStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CinemaSession]:
        values = list(self._sessions.values())
        if status is not None:
            values = [s for s in values if s.status == status]
        values.sort(key=lambda s: s.created_at, reverse=True)
        return values[skip: skip + limit]

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
