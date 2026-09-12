import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


class SessionStatus(str, enum.Enum):
    WAITING = "WAITING"   # sala creada, esperando a que el host inicie
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    ENDED = "ENDED"


class ParticipantRole(str, enum.Enum):
    HOST = "HOST"
    GUEST = "GUEST"


@dataclass
class Participant:
    user_id: int
    role: ParticipantRole
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CinemaSession:
    """Sala virtual de cine en grupo.

    No se persiste en base de datos: vive en memoria mientras el proceso
    del microservicio está corriendo. `movie_id` referencia una película del
    Catalog Service (otro microservicio), aquí solo se guarda el id.
    """

    id: str = field(default_factory=lambda: uuid4().hex[:10])
    movie_id: int = 0
    title: str = ""
    host_id: int = 0
    status: SessionStatus = SessionStatus.WAITING
    is_playing: bool = False
    position_seconds: float = 0.0
    max_participants: int = 20
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    participants: dict[int, Participant] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
