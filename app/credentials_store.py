"""
Metadata + helpers for the admin Credentials page.

The Credentials page lets admins enter integration secrets in the UI instead of
the .env file. Values are persisted in the `integration_credential` table and
overlaid onto the in-memory `integration_settings` object at startup (and live
on every save), so adapters keep reading `integration_settings.X` unchanged
while the DB takes precedence over .env.
"""

from dataclasses import dataclass, field
from typing import Optional

from app.config import integration_settings


@dataclass
class CredField:
    key: str                    # matches the .env / integration_settings attribute name
    label: str
    secret: bool = False        # masked on read; blank-on-save means "keep existing"
    placeholder: str = ""
    help: str = ""


@dataclass
class CredGroup:
    id: str
    name: str
    icon: str
    fields: list[CredField] = field(default_factory=list)


# NOTE: SMTP is intentionally NOT here — it is managed via the existing
# /smtp-config/ endpoints and surfaced on the Credentials page through them,
# so there is a single source of truth for email settings.
CREDENTIAL_GROUPS: list[CredGroup] = [
    CredGroup("metabase", "Metabase", "📊", [
        CredField("METABASE_URL", "Base URL", placeholder="https://insights.hypatos.ai/"),
        CredField("METABASE_API_KEY", "API Key", secret=True),
    ]),
    CredGroup("azure", "Microsoft Azure (Teams / SharePoint)", "🔷", [
        CredField("AZURE_TENANT_ID", "Tenant ID"),
        CredField("AZURE_CLIENT_ID", "Client ID"),
        CredField("AZURE_CLIENT_SECRET", "Client Secret", secret=True),
        CredField("TEAMS_ADMIN_USER_ID", "Teams Admin User ID",
                  help="Object ID of the admin user used to provision Teams."),
    ]),
    CredGroup("slack", "Slack", "💬", [
        CredField("SLACK_BOT_TOKEN", "Bot Token", secret=True, placeholder="xoxb-…",
                  help="OAuth bot token with groups:* and users:read scopes."),
    ]),
    CredGroup("jira", "Jira / Confluence (Atlassian)", "🧩", [
        CredField("JIRA_BASE_URL", "Base URL", placeholder="https://hypatos.atlassian.net"),
        CredField("JIRA_EMAIL", "Account Email"),
        CredField("JIRA_API_TOKEN", "API Token", secret=True),
    ]),
    CredGroup("salesforce", "Salesforce", "☁️", [
        CredField("SALESFORCE_INSTANCE_URL", "Instance / Login URL",
                  placeholder="https://login.salesforce.com",
                  help="Login host for OAuth (https://login.salesforce.com) or your My Domain URL."),
        CredField("SALESFORCE_CLIENT_ID", "Consumer Key (Client ID)", secret=True),
        CredField("SALESFORCE_CLIENT_SECRET", "Consumer Secret (Client Secret)", secret=True),
        CredField("SALESFORCE_USERNAME", "Username",
                  help="Only for the username-password OAuth flow. Leave blank for client-credentials."),
        CredField("SALESFORCE_PASSWORD", "Password", secret=True,
                  help="Only for the username-password OAuth flow."),
        CredField("SALESFORCE_SECURITY_TOKEN", "Security Token", secret=True,
                  help="Appended to the password for the username-password OAuth flow."),
    ]),
    # NOTE: Hypatos Studio is NOT a flat group — it supports multiple clusters,
    # managed via the `studio_cluster` table and the /studio-clusters/ endpoints,
    # surfaced as a dedicated section on the Credentials page.
]

# Flat lookup: key -> CredField
ALL_FIELDS: dict[str, CredField] = {f.key: f for g in CREDENTIAL_GROUPS for f in g.fields}


def apply_to_settings(key: str, value: Optional[str]) -> None:
    """Overlay a single credential onto the live in-memory settings object."""
    if key in ALL_FIELDS and hasattr(integration_settings, key):
        setattr(integration_settings, key, value if value not in (None, "") else None)


async def hydrate_settings(session) -> int:
    """Load all stored credentials from the DB and overlay them onto
    `integration_settings`. Returns the number of values applied. Called once at
    startup so DB-stored credentials take precedence over the .env file."""
    from sqlmodel import select
    from app.database.models import IntegrationCredential

    rows = (await session.execute(select(IntegrationCredential))).scalars().all()
    applied = 0
    for row in rows:
        if row.value not in (None, ""):
            apply_to_settings(row.key, row.value)
            applied += 1
    return applied
