from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError

from app.core.config import settings
from app.core.security import decode_access_token
from app.repositories.session_repository import SessionRepository
from app.services.connection_manager import ConnectionManager
from app.services.session_service import SessionService

# tokenUrl solo se usa para que Swagger muestre el botón "Authorize";
# el login real ocurre en Community Service (Auth Service).
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)

# Estado en memoria compartido por todo el proceso (no hay base de datos).
_repository = SessionRepository()
_connection_manager = ConnectionManager()


def get_session_repository() -> SessionRepository:
    return _repository


def get_connection_manager() -> ConnectionManager:
    return _connection_manager


def get_session_service(
    repository: SessionRepository = Depends(get_session_repository),
    manager: ConnectionManager = Depends(get_connection_manager),
) -> SessionService:
    return SessionService(repository, manager)


def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    try:
        return decode_access_token(token)
    except InvalidTokenError as exc:
        raise credentials_error from exc


def get_current_user_id_ws(token: str | None) -> int:
    """Igual que get_current_user_id pero para usar en el handshake del WebSocket,
    donde el token llega como query param en vez de header Authorization."""
    if not token:
        raise InvalidTokenError("Falta el token")
    return decode_access_token(token)
