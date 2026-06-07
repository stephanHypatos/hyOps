# hyOps

Internal ops tool for the Hypatos CS team — manages the full lifecycle of customer implementations, from organisations and users to scoping, document generation, and third-party integrations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) (async) |
| ORM | [SQLModel](https://sqlmodel.tiangolo.com/) + SQLAlchemy async |
| Database | PostgreSQL (asyncpg driver) |
| Containerization | Docker + Docker Compose |
| Frontend | Jinja2 + Alpine.js + Bootstrap 5 |
| API Docs | Scalar / Swagger UI |
| Settings | Pydantic Settings + `.env` |

---

## Features

### Core
- **Organisations** — manage customers, partners, and internal entities; unique auto-generated org key (2–7 alpha); industry dropdown (25 categories + Other); country dropdown (ISO Alpha-2)
- **Users** — stakeholders by role (`admin`/`enduser`), type (`customer`/`partner`/`internal`), skills, and languages
- **Projects** — full lifecycle (pilot, PoC, custom demo, rollout) with rich discovery fields
- **Capabilities & Features** — scope specs, cost drivers, effort estimation by team
- **Use Cases** — linked to features and projects
- **Document Templates & Generation** — Markdown/DOCX templates (SOW, Success Contract, Solution Design) with variable substitution
- **ERP Systems & Connectors** — SAP, Coupa, Oracle, and others per project

### Integrations (managed per organisation on the Integrations page)

| Integration | What it does |
|---|---|
| **Microsoft Teams** | Creates a private Teams group for the org; manages member provisioning |
| **SharePoint** | Copies the standard "Project" folder template from CSTemplates to the org's Teams SharePoint |
| **Slack** | Creates two private channels: `client-{org}` (internal users) and `ext-partner-{org}` (internal + partner users); manages members |
| **Jira** | Creates a company-managed Jira Core board (`{org} x Hypatos`); assigns standard Hypatos workflow/permission schemes; OR links an existing project by key |
| **Metabase** | Creates or links a Metabase group for the org |

---

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1 — Clone and configure

```bash
git clone https://github.com/stephanHypatos/hyOps.git
cd hyOps
cp .env.sample .env   # then fill in your values
```

### 2 — Start

```bash
docker compose up --build
```

The app is available at **http://localhost:8000**. Tables are created automatically on first start.

### Remote database (Supabase / RDS)

Set only `POSTGRESQL_URL` in `.env` and start only the API container:

```bash
docker compose up --build api
```

---

## Environment Variables

Create a `.env` file at the project root (never commit it — it is in `.gitignore`):

```env
# Database
POSTGRESQL_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>

# Microsoft Azure (Teams + SharePoint)
AZURE_TENANT_ID=<directory-tenant-id>
AZURE_CLIENT_ID=<app-registration-client-id>
AZURE_CLIENT_SECRET=<client-secret-value>

# Slack
SLACK_BOT_TOKEN=xoxb-…

# Jira / Atlassian
JIRA_BASE_URL=https://hypatos.atlassian.net
JIRA_EMAIL=<service-account-email>
JIRA_API_TOKEN=<atlassian-api-token>

# Metabase
METABASE_URL=https://insights.hypatos.ai/
METABASE_API_KEY=mb_…
```

---

## API Documentation

| Interface | URL |
|---|---|
| Scalar (recommended) | http://localhost:8000/scalar |
| Swagger UI | http://localhost:8000/docs |

---

## Project Structure

```
hyOps/
├── app/
│   ├── main.py                   # App entry point, HTML routes
│   ├── config.py                 # Settings (reads .env)
│   ├── api/
│   │   ├── router.py             # Master router
│   │   ├── routers/              # Endpoint handlers per domain
│   │   └── schemas/              # Pydantic request/response schemas
│   ├── database/
│   │   ├── models.py             # All SQLModel table definitions
│   │   └── session.py            # Async engine + SessionDep
│   ├── adapters/                 # External service integrations
│   │   ├── jira.py               # Atlassian Jira
│   │   ├── slack.py              # Slack Web API
│   │   ├── sharepoint.py         # Microsoft Graph / SharePoint
│   │   ├── teams.py              # Microsoft Graph / Teams
│   │   └── metabase.py           # Metabase
│   ├── templates/                # Jinja2 HTML templates
│   └── modules/                  # Business logic (doc generation, etc.)
├── docs/
│   └── admin-guide.md            # Admin user guide
├── migrate_*.py                  # One-shot DB migration scripts
├── CLAUDE.md                     # AI assistant context file
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Data Model

```
Organization  (key, industry, country)
  ├── Users               (role, type, skills, languages)
  ├── Projects            (lifecycle, discovery fields, ERP, docs)
  ├── OrganizationTeamsGroup      → Teams group + SharePoint copy status
  ├── OrganizationSlackChannel    → client + ext-partner channels
  ├── OrganizationJiraProject     → Jira board link
  └── OrganizationMetabaseGroup   → Metabase group link

JiraLeadUser              (global list of eligible Jira project leads)
Capabilities → Features → ScopeSpec / CostDriver / FeatureEffort / UseCases
DocumentTemplates → GeneratedDocuments
```

---

## Migrations

Schema changes are managed with plain SQL scripts. Run them inside the container:

```bash
docker exec hyops_api python migrate_add_org_key.py
docker exec hyops_api python migrate_add_jira_lead_user.py
```

---

## Docker Reference

| Action | Command |
|---|---|
| Start (build) | `docker compose up --build` |
| Start (detached) | `docker compose up --build -d` |
| Stop | `docker compose down` |
| Stop + wipe DB | `docker compose down -v` |
| View logs | `docker compose logs api -f` |
| Run migration | `docker exec hyops_api python migrate_<name>.py` |
| Open shell | `docker exec -it hyops_api sh` |
