from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_session_service
from app.models.session import CinemaSession, SessionStatus
from app.schemas.session import (
    ParticipantRead,
    PlaybackUpdate,
    SessionCreate,
    SessionDetailRead,
    SessionRead,
)
from app.services.session_service import SessionService

router = APIRouter()


def _to_read(session: CinemaSession) -> SessionRead:
    return SessionRead(
        id=session.id,
        movie_id=session.movie_id,
        title=session.title,
        host_id=session.host_id,
        status=session.status,
        is_playing=session.is_playing,
        position_seconds=session.position_seconds,
        max_participants=session.max_participants,
        created_at=session.created_at,
        updated_at=session.updated_at,
        participant_count=len(session.participants),
    )


def _to_detail(session: CinemaSession) -> SessionDetailRead:
    return SessionDetailRead(
        **_to_read(session).model_dump(),
        participants=[ParticipantRead.model_validate(p) for p in session.participants.values()],
    )


@router.post("", response_model=SessionDetailRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    current_user_id: int = Depends(get_current_user_id),
    service: SessionService = Depends(get_session_service),
):
    session = service.create_session(payload, host_id=current_user_id)
    return _to_detail(session)


@router.get("", response_model=list[SessionRead])
def list_sessions(
    status_filter: SessionStatus | None = Query(default=None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: SessionService = Depends(get_session_service),
):
    sessions = service.list_sessions(status=status_filter, skip=skip, limit=limit)
    return [_to_read(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionDetailRead)
def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    return _to_detail(service.get_session(session_id))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(
    session_id: str,
    current_user_id: int = Depends(get_current_user_id),
    service: SessionService = Depends(get_session_service),
):
    await service.end_session(session_id, current_user_id)


@router.post("/{session_id}/members", response_model=SessionDetailRead, status_code=status.HTTP_201_CREATED)
async def join_session(
    session_id: str,
    current_user_id: int = Depends(get_current_user_id),
    service: SessionService = Depends(get_session_service),
):
    session = await service.join_session(session_id, current_user_id)
    return _to_detail(session)


@router.get("/{session_id}/members", response_model=list[ParticipantRead])
def list_members(
    session_id: str,
    service: SessionService = Depends(get_session_service),
):
    return [ParticipantRead.model_validate(p) for p in service.list_members(session_id)]


@router.delete("/{session_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_session(
    session_id: str,
    current_user_id: int = Depends(get_current_user_id),
    service: SessionService = Depends(get_session_service),
):
    await service.leave_session(session_id, current_user_id)


@router.patch("/{session_id}/playback", response_model=SessionRead)
async def update_playback(
    session_id: str,
    payload: PlaybackUpdate,
    current_user_id: int = Depends(get_current_user_id),
    service: SessionService = Depends(get_session_service),
):
    session = await service.update_playback(
        session_id, current_user_id, payload.is_playing, payload.position_seconds
    )
    return _to_read(session)
