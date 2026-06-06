from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

basedir = os.path.abspath(os.path.dirname(__file__))

_env_config = SettingsConfigDict(
    env_file="./.env",
    env_ignore_empty=True,
    extra="ignore",
)


class DatabaseSettings(BaseSettings):
    POSTGRESQL_URL: str
    model_config = _env_config


class IntegrationSettings(BaseSettings):
    # Metabase
    METABASE_URL: Optional[str] = None
    METABASE_API_KEY: Optional[str] = None

    # Microsoft Teams (Azure AD)
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    TEAMS_TEAM_ID: Optional[str] = None

    # Email (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    model_config = _env_config


settings = DatabaseSettings()
integration_settings = IntegrationSettings()