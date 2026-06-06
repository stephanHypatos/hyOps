# hyOps

A FastAPI backend for managing the full lifecycle of customer implementation projects — from organizations and users to scoping, document generation, and ERP integrations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLModel](https://sqlmodel.tiangolo.com/) + SQLAlchemy (async) |
| Database | PostgreSQL (asyncpg driver) |
| Containerization | Docker + Docker Compose |
| API Docs | Scalar / Swagger UI |
| Settings | Pydantic Settings + `.env` |

---

## Features

- **Organizations** — manage customers, partners, and internal entities with regional and industry metadata
- **Users** — track stakeholders by role, subtype, skills, and languages across organizations
- **Projects** — full project lifecycle (pilot, PoC, custom demo, rollout) with rich discovery fields covering document processing, ERP integration, classification, PO matching, and KPIs
- **Capabilities & Features** — define platform capabilities, scope specifications, cost drivers, and effort estimations by team
- **Use Cases** — link use cases to features and projects
- **Document Templates** — create Markdown or DOCX templates (SOW, Success Contract, Solution Design) with variable substitution
- **Document Generation** — generate project-specific documents from templates
- **ERP Systems & Connectors** — track SAP, Coupa, Oracle, and other ERP integrations per project
- **Integrations** — Teams groups, Slack channels, Metabase groups, HyStudio companies, and API credentials per organization

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Run with local PostgreSQL (recommended for development)

```bash
git clone https://github.com/stephanHypatos/hyOps.git
cd hyOps
docker compose up --build
```

The app will be available at **http://localhost:8000**

> The database tables are created automatically on first startup.

### Run with a remote database (e.g. Supabase)

Create a `.env` file in the project root:

```env
POSTGRESQL_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>
```

Then start only the API container:

```bash
docker compose up --build api
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `POSTGRESQL_URL` | Full async PostgreSQL connection string |

Copy `.env.sample` to `.env` and fill in your values.

---

## API Documentation

Once running, the interactive API docs are available at:

| Interface | URL |
|---|---|
| Scalar (recommended) | http://localhost:8000/scalar |
| Swagger UI | http://localhost:8000/docs |

---

## Project Structure

```
hyOps/
├── app/
│   ├── main.py               # FastAPI app entry point & HTML routes
│   ├── config.py             # Settings (reads from .env)
│   ├── api/
│   │   ├── router.py         # Master router
│   │   ├── routers/          # Endpoint handlers per module
│   │   └── schemas/          # Pydantic request/response schemas
│   ├── database/
│   │   ├── models.py         # SQLModel table definitions
│   │   └── session.py        # Async engine & session management
│   ├── modules/              # Business logic (document generation, etc.)
│   ├── adapters/             # External service adapters
│   ├── templates/            # Jinja2 HTML templates
│   ├── doc_templates/        # Document template files
│   └── consts/               # Constants and form questions
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.sample
```

---

## Data Model Overview

```
Organization
  └── Users (roles: admin, enduser | types: customer, partner, internal)
  └── Projects
        └── Stakeholders (Users)
        └── Use Cases
        └── Generated Documents
        └── ERP Connectors
  └── ERP Systems
  └── Teams Groups / Slack Channels / Metabase Groups / HyStudio Companies

Capabilities
  └── Features
        └── Scope Specifications
        └── Cost Drivers
        └── Feature Efforts (by team type)
        └── Use Cases

Document Templates → Generated Documents
```

---

## Docker Commands

| Action | Command |
|---|---|
| Start (build) | `docker compose up --build` |
| Start (detached) | `docker compose up --build -d` |
| Stop | `docker compose down` |
| Stop + wipe DB | `docker compose down -v` |
| View logs | `docker compose logs api -f` |
