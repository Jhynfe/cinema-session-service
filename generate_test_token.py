"""
Genera tokens JWT de prueba para probar el servicio en Postman
SIN necesitar levantar Community Service.

Usa el mismo JWT_SECRET_KEY que tienes en tu .env, así que el token
es válido para este microservicio exactamente igual que si lo hubiera
emitido Community Service.

Uso:
    python3 generate_test_token.py          # genera token para user_id=1
    python3 generate_test_token.py 5        # genera token para user_id=5
"""
import sys

import jwt

from app.core.config import settings

user_id = sys.argv[1] if len(sys.argv) > 1 else "1"

token = jwt.encode(
    {"sub": str(user_id)},
    settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)

print(f"user_id={user_id}")
print(f"token={token}")
