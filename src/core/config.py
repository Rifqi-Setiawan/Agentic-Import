
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_PORT: int = 8120
    APP_HOST: str = "127.0.0.1"

    DATABASE_URL: str = "postgresql://imporjaga_user:imporjaga@127.0.0.1:5432/imporjaga"
    TEST_DATABASE_URL: str = "postgresql://imporjaga_user:imporjaga@127.0.0.1:5432/imporjaga_test"

    JWT_SECRET: str = "default_secret_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    STORAGE_VAULT_PATH: str = "/srv/hermes-control/services/agentic-import/data/vault"
    MAX_UPLOAD_SIZE_MB: int = 10

    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3060",
        "http://127.0.0.1:3060",
        "https://imporjaga.rifqisetiawan.my.id",
        "https://artha.rifqisetiawan.my.id",
    ]

    LLM_DATA_POLICY: str = "redacted_dev_router"
    LLM_GATEWAY_URL: str = "http://127.0.0.1:20128/v1"
    LLM_GATEWAY_KEY: str = ""
    LLM_MODEL: str = "ag/gemini-3.8-flash-high"
    LLM_TEMPERATURE: float = 0.0

    SMTP_HOST: str = "127.0.0.1"
    SMTP_PORT: int = 1025
    AGENT_EMAIL_ALLOWED_RECIPIENTS: list[str] = [
        "tim-impor@mitrakemas.co.id",
        "rifqi@rifqisetiawan.my.id",
    ]
    FOLLOWUP_DELAY_MINUTES: int = 3

    model_config = SettingsConfigDict(
        env_file="/srv/hermes-control/services/agentic-import/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
