# Cinema Session Service

Microservicio para **sesiones grupales de cine** (salas virtuales) del proyecto Cinema Club Online.

## Stack

- Python 3.12
- FastAPI (REST + WebSocket)
- Pydantic 2
- PyJWT (valida tokens emitidos por Community Service)
- Docker / Docker Compose
- Pytest

## ¿Por qué no tiene base de datos?

Este microservicio es responsable de las **salas de cine en vivo**: crear una
sala, unirse/salir, y sincronizar la reproducción (play/pause/seek) entre
todos los participantes en tiempo real. Ese estado es **efímero** — solo
importa mientras la sesión está activa — así que se guarda en memoria del
proceso (`SessionRepository`) en lugar de persistirlo. Cuando el host
termina la sesión, se elimina.

Si en el futuro se quisiera guardar historial de sesiones (para
estadísticas, por ejemplo), eso encajaría mejor en **Analytics Service**, no aquí.

## Arquitectura

Sigue el mismo patrón por capas que Community Service:

```text
API / Controllers (routes)
        |
        v
     Services            <-- lógica de negocio (roles, validaciones, broadcast)
        |
        v
   Repository            <-- almacén en memoria (dict + lock), no SQL
        |
        v
  Estado en memoria
```

Entidades principales (en memoria, no ORM):

- `CinemaSession`: sala (id, movie_id, host_id, status, is_playing, position_seconds, participantes)
- `Participant`: usuario dentro de una sala, con rol `HOST` o `GUEST`

## Autenticación

Este servicio **no tiene tabla de usuarios**. Recibe el JWT emitido por
Community Service (Auth) y solo lo valida con la misma clave compartida
(`JWT_SECRET_KEY` / `JWT_ALGORITHM` deben coincidir en ambos `.env`). Del
token solo se usa el campo `sub` (user_id) — no se vuelve a consultar
ninguna base de datos.

## Puesta en marcha con Docker

1. Copia el archivo de variables (y usa el **mismo** `JWT_SECRET_KEY` que Community Service):

```bash
cp .env.example .env
```

2. Levanta el proyecto:

```bash
docker compose up --build
```

3. Abre Swagger:

```text
http://localhost:8001/docs
```

Health check:

```text
GET http://localhost:8001/api/v1/health
```

> Nota: usa el puerto **8001** (Community Service usa 8000) para poder correr ambos al mismo tiempo.

## Flujo mínimo de prueba

Necesitas un JWT válido. Puedes obtenerlo haciendo login contra Community
Service (`POST /api/v1/auth/login`) — ambos servicios comparten el secreto.

### 1. Crear una sala (host)

```http
POST /api/v1/sessions
Authorization: Bearer <TOKEN_HOST>
Content-Type: application/json
```

```json
{
  "movie_id": 42,
  "title": "Noche de Ciencia Ficción",
  "max_participants": 10
}
```

El host queda unido automáticamente con rol `HOST`.

### 2. Unirse a la sala (invitado)

```http
POST /api/v1/sessions/{session_id}/members
Authorization: Bearer <TOKEN_GUEST>
```

### 3. Controlar la reproducción (solo el host)

```http
PATCH /api/v1/sessions/{session_id}/playback
Authorization: Bearer <TOKEN_HOST>
Content-Type: application/json
```

```json
{
  "is_playing": true,
  "position_seconds": 125.5
}
```

Esto difunde el nuevo estado a todos los conectados por WebSocket.

### 4. Conectarse por WebSocket (sincronía en tiempo real)

```text
ws://localhost:8001/api/v1/sessions/{session_id}/ws?token=<TOKEN>
```

Eventos que puedes enviar:

```json
{ "type": "PLAYBACK_UPDATE", "is_playing": true, "position_seconds": 130 }
{ "type": "CHAT_MESSAGE", "message": "¡Esta escena está increíble!" }
```

Eventos que puedes recibir (broadcast a toda la sala):

```json
{ "type": "MEMBER_JOINED", "user_id": 2 }
{ "type": "MEMBER_LEFT", "user_id": 2 }
{ "type": "PLAYBACK_UPDATE", "is_playing": true, "position_seconds": 130, "updated_at": "..." }
{ "type": "CHAT_MESSAGE", "user_id": 2, "message": "...", "sent_at": "..." }
{ "type": "SESSION_ENDED", "session_id": "..." }
{ "type": "ERROR", "detail": "Solo el HOST puede realizar esta acción" }
```

### 5. Salir / terminar la sesión

```http
DELETE /api/v1/sessions/{session_id}/members/me
Authorization: Bearer <TOKEN_GUEST>
```

```http
DELETE /api/v1/sessions/{session_id}
Authorization: Bearer <TOKEN_HOST>
```

Terminar la sesión la elimina del almacén en memoria y notifica a todos por WebSocket.

## Endpoints principales

### Sesiones

- `POST /api/v1/sessions` — crear sala (usuario autenticado queda como HOST)
- `GET /api/v1/sessions` — listar salas (filtro opcional `?status=PLAYING`)
- `GET /api/v1/sessions/{session_id}` — detalle de la sala + participantes
- `DELETE /api/v1/sessions/{session_id}` — terminar sala (solo HOST)
- `PATCH /api/v1/sessions/{session_id}/playback` — actualizar play/pause/posición (solo HOST)

### Miembros

- `POST /api/v1/sessions/{session_id}/members` — unirse a la sala
- `GET /api/v1/sessions/{session_id}/members` — listar participantes
- `DELETE /api/v1/sessions/{session_id}/members/me` — salir de la sala (HOST no puede salir)

### Tiempo real

- `WS /api/v1/sessions/{session_id}/ws?token=<JWT>` — canal de sincronización y chat

## Reglas de negocio

- Solo el `HOST` (creador de la sala) puede iniciar/pausar/mover la reproducción o terminar la sesión.
- El `HOST` no puede "salir" de la sala; debe terminarla explícitamente.
- Un usuario no puede unirse dos veces a la misma sala, ni unirse si ya está llena o si ya terminó.
- Al terminar una sesión se notifica a todos los participantes conectados por WebSocket y luego se libera de memoria.

## Tests

Instala dependencias de desarrollo:

```bash
pip install -r requirements-dev.txt
```

Ejecuta:

```bash
pytest -q
```

Los tests generan sus propios JWT localmente con el mismo `JWT_SECRET_KEY`
de `Settings`, así que no dependen de que Community Service esté corriendo.

## Notas / próximos pasos posibles

- Actualmente el estado vive en un solo proceso; si se necesitara escalar
  horizontalmente, habría que mover el estado compartido a Redis (pub/sub
  para el broadcast entre instancias).
- No se valida que `movie_id` exista en Catalog Service (se podría agregar
  una llamada HTTP a ese microservicio si el profesor lo pide).
- No se persiste historial de sesiones — si se requiere, ese dato debería
  vivir en Analytics Service.
