from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Microservicio Cinema Session Service: salas virtuales de cine en "
        "grupo, sincronización de reproducción y chat en tiempo real. "
        "No tiene base de datos propia; las sesiones viven en memoria."
    ),
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
