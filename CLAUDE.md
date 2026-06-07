# CLAUDE.md — Codebase context for AI assistants

This file gives an AI assistant everything it needs to work effectively in the hyOps codebase without re-deriving context from scratch.

---

## What this project is

**hyOps** is an internal ops tool for the Hypatos CS (Customer Success) team. It manages the full lifecycle of customer implementations: organisations, users, projects, scoping, document generation, and a growing set of third-party integrations (Teams, Slack, SharePoint, Jira, Metabase).

---

## Tech stack

| Layer | Choice |
|---|---|
| Framework | FastAPI (async) |
| ORM | SQLModel + SQLAlchemy async |
| DB driver | asyncpg → PostgreSQL |
| Container | Docker + Docker Compose |
| Frontend | Jinja2 templates + Alpine.js + Bootstrap 5 |
| Settings | Pydantic Settings + `.env` |
| HTTP client | httpx (sync, run in `asyncio.to_thread`) |

---

## Repository layout

```
app/
  main.py                  # FastAPI app, mounts HTML routes + API router
  config.py                # IntegrationSettings (reads .env)
  api/
    router.py              # Master router — includes all sub-routers
    routers/               # One file per domain (organization, user, jira, slack, …)
    schemas/               # Pydantic request/response models
  database/
    models.py              # ALL SQLModel table definitions
    session.py             # Async engine + SessionDep
  adapters/                # Thin wrappers for external APIs
    jira.py                # Atlassian Jira REST API v3 (+ v2 for project creation)
    slack.py               # Slack Web API (groups:* scopes for private channels)
    sharepoint.py          # Microsoft Graph API (SharePoint copy)
    teams.py               # Microsoft Graph API (Teams provisioning)
    metabase.py            # Metabase API
    email.py               # SMTP email helper
  templates/               # Jinja2 HTML pages
    index.html             # Organizations CRUD
    integrations.html      # All integration management (Teams, Slack, Jira, Metabase)
    user.html              # User management
    project.html           # Project management
    …
migrations/                # One-shot migration scripts (run inside the container)
docs/
  admin-guide.md           # Human-readable guide for admins
```

---

## Key patterns

### Adapters
All external API calls live in `app/adapters/`. They are **synchronous** functions that are called via `asyncio.to_thread(...)` from async router code. This avoids blocking the event loop while keeping the adapter code simple (no `aiohttp`/`httpx` async).

```python
# adapter pattern
def _do_thing_sync(arg: str) -> dict:
    resp = httpx.get(url, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()

async def do_thing(arg: str) -> dict:
    return await asyncio.to_thread(_do_thing_sync, arg)
```

### Routers
- Use `SessionDep` for DB access (`from app.database.session import SessionDep`)
- Return raw dicts or Pydantic models
- Raise `HTTPException` for all errors

### Models
All SQLModel table classes are in `app/database/models.py`. Add new tables there, then write a `migrate_*.py` script. **Do not use Alembic** — migrations are plain SQL via `sqlalchemy.text`.

### Migrations
Create a script in the `migrations/` folder:
```python
# migrations/my_change.py
async def run():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE …"))
```
Run inside the container: `docker exec hyops_api python migrations/my_change.py`

---

## Integration details

### Slack (`app/adapters/slack.py`)
- **Auth**: Bot token from `SLACK_BOT_TOKEN` env var
- **Required scopes**: `groups:write`, `groups:read`, `users:read`, `users:read.email`
- **Channel naming**: `client-{org-slug}` (internal users only) and `ext-partner-{org-slug}` (internal + partner users)
- **DB model**: `OrganizationSlackChannel` — one row per channel per org
- Key functions: `get_or_create_channel()`, `provision_users_to_channel()`, `remove_from_channel()`

### SharePoint / Teams (`app/adapters/sharepoint.py`, `app/adapters/teams.py`)
- **Auth**: Azure AD OAuth2 client credentials (`AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`)
- **SharePoint copy**: Uses MS Graph async copy endpoint (`POST /drives/{id}/items/{id}/copy` → 202 + Location poll). Copies the specific folder ID `01BFQU2H26EYJ5I3JKERDYUEZFZJITPFIR` ("Project") from `https://hypatos.sharepoint.com/sites/CSTemplates` to the org's Teams SharePoint.
- Completion is stamped as `sharepoint_copied_at` on `OrganizationTeamsGroup`
- **DB model**: `OrganizationTeamsGroup`

### Jira (`app/adapters/jira.py`)
- **Auth**: HTTP Basic `base64(email:api_token)` — credentials from `JIRA_EMAIL`, `JIRA_API_TOKEN`
- **API version**: v3 for everything except project creation (v2 used there because v3 silently ignores the `key` field)
- **Project naming convention**: `"{client_name} x Hypatos"`
- **Key rules**: 2–7 uppercase letters, not in `EXCLUDED_KEYS`, unique in workspace
- **After creation**, assigns 4 schemes automatically:
  - Workflow scheme: `10145`
  - Issue type screen scheme: `10137`
  - Issue type scheme: `10466`
  - Permission scheme: `10087`
- Then assigns groups `COE` + `administrators` to Admin role `10002`
- **Lead users**: stored in `jira_lead_user` DB table; managed via the Jira Settings admin panel
- **DB model**: `OrganizationJiraProject`, `JiraLeadUser`

### Metabase (`app/adapters/metabase.py`)
- **Auth**: API key from `METABASE_API_KEY`
- **DB model**: `OrganizationMetabaseGroup`

---

## Database models (key ones)

| Model | Table | Notes |
|---|---|---|
| `Organization` | `organization` | Has `key` (2–7 alpha, unique), `industry`, `country` |
| `User` | `user` | `type`: customer/partner/internal; `role`: admin/enduser |
| `Project` | `project` | Rich discovery fields |
| `OrganizationTeamsGroup` | `organization_teams_group` | Has `sharepoint_copied_at` |
| `OrganizationSlackChannel` | `organization_slack_channel` | `channel_type`: client/ext_partner |
| `OrganizationJiraProject` | `organization_jira_project` | Jira project key + board URL |
| `JiraLeadUser` | `jira_lead_user` | Global list of eligible Jira project leads |

---

## Organization `key` field

- 2–7 uppercase letters A–Z only
- Unique across all organisations (DB unique constraint)
- Auto-generated on creation (prefers 3-char initials; extends to 4–7 if taken)
- Editable manually via inline edit in the table or the edit form
- **Future use**: will become the Jira project key when creating boards for that org

---

## Security rules — NEVER violate these

1. **`.env` must never be committed or pushed.** It is in `.gitignore`. All credentials live only in `.env`.
2. All secrets are read via `app/config.py` → `IntegrationSettings` → `pydantic_settings.BaseSettings`.
3. Jira API token, Slack bot token, Azure secrets, Metabase API key — all in `.env` only.

---

## Environment variables

```env
POSTGRESQL_URL=postgresql+asyncpg://…

# Microsoft Azure / Teams / SharePoint
AZURE_TENANT_ID=…
AZURE_CLIENT_ID=…
AZURE_CLIENT_SECRET=…

# Slack
SLACK_BOT_TOKEN=xoxb-…

# Jira / Atlassian
JIRA_BASE_URL=https://hypatos.atlassian.net
JIRA_EMAIL=…
JIRA_API_TOKEN=…

# Metabase
METABASE_URL=https://insights.hypatos.ai/
METABASE_API_KEY=…
```

---

## Docker

```bash
docker compose up --build          # start everything
docker compose up --build -d       # detached
docker compose logs api -f         # tail logs
docker exec hyops_api python …     # run a script inside the container
```

The API container is named `hyops_api`, DB is `hyops_db`.

---

## Conventions

- New router → add to `app/api/router.py` `include_router(...)`
- New integration adapter → `app/adapters/<name>.py`, settings in `app/config.py`
- New DB model → `app/database/models.py`, migration script in `migrations/`
- Slugs: `org.name.lower().replace(" ", "-")` via `slugify()` in Slack adapter
- Error handling: `ValueError` = validation error (422), `RuntimeError` = upstream API error (502)
- All timestamps use `datetime.utcnow()` as default
