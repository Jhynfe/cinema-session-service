from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cinema Session Service"
    API_V1_PREFIX: str = "/api/v1"

    # Este servicio no tiene base de datos propia: las sesiones grupales
    # viven en memoria mientras el proceso está activo.
    MAX_PARTICIPANTS_PER_SESSION: int = 20

    # El JWT lo emite Community Service (Auth). Aquí solo lo validamos,
    # por eso el secreto y el algoritmo deben coincidir con los de ese servicio.
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
