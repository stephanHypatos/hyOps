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
- **Projects** — full lifecycle (pilot, PoC, custom demo, rollout) with rich discovery fields; partner org linkage; partner + Hypatos budget fields (integer hours)
- **Capabilities & Features** — scope specs, cost drivers, effort estimation by team
- **Use Cases** — linked to features and projects
- **Document Templates & Generation** — Markdown/DOCX templates (SOW, Success Contract, Solution Design) with variable substitution
- **ERP Systems & Connectors** — SAP, Coupa, Oracle, and others per project
- **Documentation Links** — global list of links shared with every new user added to the system
- **Custom Project Fields** — admin-defined sections and questions attached to projects; sections can be global or scoped to a specific use case, which auto-loads them when that use case is selected on a project

### CSM
- **Account overview** — contracts (MSA, SOW, NDA), account health scores, and project status tracking per organisation
- **CSM List** — dashboard view across all accounts with health, contract, and integration status

### Integrations (managed per organisation on the Integrations page)

| Integration | What it does |
|---|---|
| **Microsoft Teams** | Creates a private Teams group for the org; manages member provisioning |
| **SharePoint** | Copies the standard "Project" folder template from CSTemplates to the org's Teams SharePoint |
| **Slack** | Creates two private channels: `client-{org}` (internal users) and `ext-partner-{org}` (internal + partner users); manages members |
| **Jira** | Creates a company-managed Jira Core board (`{org} x Hypatos`); assigns standard Hypatos workflow/permission schemes; OR links an existing project by key |
| **Metabase** | Creates or links a Metabase group for the org |
| **Email (SMTP)** | Configures the outbound SMTP server used for automated onboarding emails |
| **Salesforce** | Reads account data from a connected Salesforce instance (OAuth username-password or client-credentials flow) |
| **Hypatos Studio** | Multi-cluster credential management (EU, US, etc.) — each cluster stored independently; selected at use-time by name or as the default |

### Admin Credentials Page (`/credentials-page`)
Centralised admin UI for all integration credentials. Secrets are stored in the database (encrypted at the application layer) and overlay `.env` values at startup — adapters require no code changes. Blank secret field on save keeps the existing value.

---

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1 — Clone and configure

```bash
git clone https://github.com/stephanHypatos/hyOps.git
cd hyOps
```

Create a `.env` file (only `POSTGRESQL_URL` is strictly required — all other credentials can be set via the Credentials page at runtime):

```env
POSTGRESQL_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>
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

Create a `.env` file at the project root (never commit it — it is in `.gitignore`).

Only `POSTGRESQL_URL` is required. Everything else can be configured via the **Credentials page** (`/credentials-page`) at runtime:

```env
# Required — must be in .env (app needs it to reach the DB before the UI is available)
POSTGRESQL_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>

# Optional — can be set here or via the Credentials page (DB wins over .env)

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

# Salesforce (username-password flow; omit USERNAME/PASSWORD for client-credentials)
SALESFORCE_INSTANCE_URL=https://<instance>.salesforce.com
SALESFORCE_CLIENT_ID=…
SALESFORCE_CLIENT_SECRET=…
SALESFORCE_USERNAME=…          # optional
SALESFORCE_PASSWORD=…          # optional
SALESFORCE_SECURITY_TOKEN=…    # optional

# Hypatos Studio — NOT in .env; managed via the Studio Clusters UI on the Credentials page
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
│   ├── main.py                    # App entry point, HTML routes, startup hydration
│   ├── config.py                  # IntegrationSettings (reads .env)
│   ├── credentials_store.py       # Credential group definitions + live overlay logic
│   ├── api/
│   │   ├── router.py              # Master router
│   │   ├── routers/               # Endpoint handlers per domain
│   │   │   ├── credentials.py     # Admin Credentials page endpoints
│   │   │   ├── studio_clusters.py # Hypatos Studio multi-cluster CRUD
│   │   │   ├── custom_questions.py# Admin custom sections/questions
│   │   │   ├── csm.py             # CSM account / contract / health endpoints
│   │   │   ├── smtp_config.py     # GET/PUT /smtp-config/ + test
│   │   │   └── …                  # Other domain routers
│   │   └── schemas/               # Pydantic request/response schemas
│   ├── database/
│   │   ├── models.py              # All SQLModel table definitions
│   │   └── session.py             # Async engine + SessionDep
│   ├── adapters/                  # External service integrations
│   │   ├── jira.py                # Atlassian Jira
│   │   ├── slack.py               # Slack Web API
│   │   ├── sharepoint.py          # Microsoft Graph / SharePoint
│   │   ├── teams.py               # Microsoft Graph / Teams
│   │   ├── metabase.py            # Metabase
│   │   ├── salesforce.py          # Salesforce REST API (OAuth)
│   │   ├── studio.py              # Hypatos Studio API (multi-cluster)
│   │   └── email.py               # SMTP email helper (DB config → .env fallback)
│   ├── templates/                 # Jinja2 HTML templates
│   │   ├── credentials.html       # Admin Credentials page
│   │   ├── custom_project_fields.html  # Custom sections/questions admin
│   │   ├── csm_account.html       # CSM account detail view
│   │   ├── csm_list.html          # CSM dashboard
│   │   └── …
│   └── modules/                   # Business logic (doc generation, etc.)
├── docs/
│   └── admin-guide.md             # Admin user guide
├── migrations/                    # One-shot DB migration scripts
├── CLAUDE.md                      # AI assistant context file
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Data Model

```
Organization  (key, industry, country)
  ├── Users               (role, type, skills, languages)
  ├── Projects            (lifecycle, partner_id, partner_budget_hours, internal_budget_hours, ERP, docs)
  ├── Contracts           (MSA/SOW/NDA, start/end/renewal dates, payment status)
  ├── AccountHealth       (health score, notes, recorded_at)
  ├── OrganizationTeamsGroup      → Teams group + SharePoint copy status
  ├── OrganizationSlackChannel    → client + ext-partner channels
  ├── OrganizationJiraProject     → Jira board link
  └── OrganizationMetabaseGroup   → Metabase group link

JiraLeadUser              (global list of eligible Jira project leads)
DocumentationLink         (global list of links sent to every new user)
SmtpConfig                (singleton — outbound SMTP server settings)
IntegrationCredential     (key/value store for integration credentials; overlays .env at startup)
StudioCluster             (one row per Hypatos Studio cluster — name, base_url, client_id, client_secret, is_default)
CustomSection             (admin-defined project form sections; use_case_id=NULL means global)
CustomQuestion            (questions within a section)
CustomAnswer              (project answers to custom questions)
Capabilities → Features → ScopeSpec / CostDriver / FeatureEffort / UseCases
DocumentTemplates → GeneratedDocuments
```

> **Cascade deletes:** deleting an Organisation automatically removes all its linked records (users, projects, contracts, integration links, ERP systems). Deleting a User removes all their link-table entries; references in documents, features, and projects are set to NULL.

---

## Migrations

Schema changes are managed with plain SQL scripts stored in `migrations/`. Run them inside the container:

```bash
docker exec hyops_api python migrations/add_org_key.py
docker exec hyops_api python migrations/add_jira_lead_user.py
docker exec hyops_api python migrations/add_cascade_deletes.py
docker exec hyops_api python migrations/add_project_partner.py
docker exec hyops_api python migrations/add_csm_fields.py
docker exec hyops_api python migrations/add_custom_answers.py
docker exec hyops_api python migrations/add_custom_section_usecase.py
```

New models added via `SQLModel.metadata.create_all` on startup (no migration script needed for brand-new tables).

---

## Docker Reference

| Action | Command |
|---|---|
| Start (build) | `docker compose up --build` |
| Start (detached) | `docker compose up --build -d` |
| Stop | `docker compose down` |
| Stop + wipe DB | `docker compose down -v` |
| View logs | `docker compose logs api -f` |
| Run migration | `docker exec hyops_api python migrations/<name>.py` |
| Open shell | `docker exec -it hyops_api sh` |

> **Development note:** The app runs with `fastapi dev` (auto-reload on file change). Changes to Python files are picked up automatically; no container restart needed.
