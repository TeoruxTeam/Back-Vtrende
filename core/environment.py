import os
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from yookassa import Configuration

from core.logger import logger


class Settings(BaseSettings):
    DEBUG: bool
    POSTGRES_DB: str
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_PORT: int
    POSTGRES_HOSTNAME: str
    DATABASE_DIALECT: str

    jwt_algorithm: str

    secret_key: str
    access_token_lifetime: int
    refresh_token_lifetime: int

    media_root: str = "media"

    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_start_tls: bool
    smtp_start_ssl: bool

    redis_host: str
    redis_port: int
    redis_db: str
    redis_password: str

    allowed_origins: List[str] = Field(default=[])
    cookie_samesite: str
    domain: str

    frontend_url: str
    locales_dir: str

    firebase_credentials_path: str
    facebook_client_id: str
    facebook_secret: str

    google_client_id: str
    google_secret: str

    oauth_redirect_uri: str
    yookassa_secret_key: str
    yookassa_account_id: str

    class Config:
        env_file = os.getenv("ENV_FILE")
        env_file_encoding = "utf-8"

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


def get_settings() -> Settings:
    """Функция для получения настроек в зависимости от среды."""
    settings = Settings()
    return settings


env = get_settings()

Configuration.account_id = env.yookassa_account_id
Configuration.secret_key = env.yookassa_secret_key
