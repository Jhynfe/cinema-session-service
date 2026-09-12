import jwt
from jwt import InvalidTokenError

from app.core.config import settings


def decode_access_token(token: str) -> int:
    """Decodifica el JWT emitido por Community Service y devuelve el user_id.

    Este microservicio no tiene tabla de usuarios: confía en el token firmado
    por el mismo secreto compartido (JWT_SECRET_KEY) en lugar de volver a
    consultar una base de datos.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Token sin 'sub'")
    return int(user_id)
