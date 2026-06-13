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
    TEAMS_TEAM_ID: Optional[str] = None  # legacy — per-org teams now stored in DB
    TEAMS_ADMIN_USER_ID: str = "02f15082-7848-48ac-830f-3af9db319dee"  # Stephan power-admin

    # Slack
    SLACK_BOT_TOKEN: Optional[str] = None  # xoxb-... from OAuth & Permissions

    # Jira / Confluence (Atlassian)
    JIRA_BASE_URL:  Optional[str] = None   # https://hypatos.atlassian.net
    JIRA_EMAIL:     Optional[str] = None   # admin email for Basic auth
    JIRA_API_TOKEN: Optional[str] = None   # Atlassian API token

    # Email (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    # Salesforce (Connected App — supports client-credentials and username-password OAuth flows)
    SALESFORCE_INSTANCE_URL: Optional[str] = None   # e.g. https://login.salesforce.com or https://<org>.my.salesforce.com
    SALESFORCE_CLIENT_ID: Optional[str] = None       # Connected App consumer key
    SALESFORCE_CLIENT_SECRET: Optional[str] = None   # Connected App consumer secret
    SALESFORCE_USERNAME: Optional[str] = None         # only for username-password flow
    SALESFORCE_PASSWORD: Optional[str] = None         # only for username-password flow
    SALESFORCE_SECURITY_TOKEN: Optional[str] = None   # appended to password for username-password flow

    # Hypatos Studio credentials are NOT here — Studio supports multiple clusters,
    # each stored as a row in the `studio_cluster` table (managed on the
    # Credentials page) rather than as single env values.

    model_config = _env_config


settings = DatabaseSettings()
integration_settings = IntegrationSettings()