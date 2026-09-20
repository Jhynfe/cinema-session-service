from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
def health_check():
    return {"status": "ok"}
