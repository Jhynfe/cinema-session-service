from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.session import ParticipantRole, SessionStatus


class SessionCreate(BaseModel):
    movie_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=150)
    max_participants: int | None = Field(default=None, ge=2, le=100)


class ParticipantRead(BaseModel):
    user_id: int
    role: ParticipantRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionRead(BaseModel):
    id: str
    movie_id: int
    title: str
    host_id: int
    status: SessionStatus
    is_playing: bool
    position_seconds: float
    max_participants: int
    created_at: datetime
    updated_at: datetime
    participant_count: int

    model_config = ConfigDict(from_attributes=True)


class SessionDetailRead(SessionRead):
    participants: list[ParticipantRead]


class PlaybackUpdate(BaseModel):
    is_playing: bool
    position_seconds: float = Field(ge=0)


class ChatMessage(BaseModel):
    user_id: int
    message: str = Field(min_length=1, max_length=500)
    sent_at: datetime
