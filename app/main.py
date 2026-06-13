import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from fastapi import FastAPI, Request
from scalar_fastapi import get_scalar_api_reference

from app.database.session import create_db_tables

from app.api.router import master_router
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    await create_db_tables()
    # Overlay DB-stored integration credentials onto the in-memory settings so
    # the Credentials page takes precedence over the .env file.
    try:
        from app.database.session import get_session
        from app.credentials_store import hydrate_settings
        agen = get_session()
        session = await agen.__anext__()
        try:
            applied = await hydrate_settings(session)
            logging.getLogger(__name__).info("Hydrated %d integration credential(s) from DB", applied)
        finally:
            await agen.aclose()
    except Exception as e:
        logging.getLogger(__name__).warning("Credential hydration skipped: %s", e)
    yield

app = FastAPI(lifespan=lifespan_handler)


# ===================== CORS Middleware =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(master_router)


templates = Jinja2Templates(directory="./app/templates")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def organization_view(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request, "current_page": "organizations"}
    )


@app.get("/users-page", response_class=HTMLResponse, include_in_schema=False)
async def users_view(request: Request):
    return templates.TemplateResponse(
        request=request, name="user.html", context={"request": request, "current_page": "users"}
    )


@app.get("/subtypes-page", response_class=HTMLResponse, include_in_schema=False)
async def subtype_view(request: Request):
    return templates.TemplateResponse(
        request=request, name="subtype.html", context={"request": request, "current_page": "subtypes"}
    )


@app.get("/capabilities-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_capabilities_page(request: Request):
    return templates.TemplateResponse(request=request,name="capability.html", context={"request": request, "current_page": "capabilities"})



@app.get("/features-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_features_page(request: Request):
    return templates.TemplateResponse(request=request,name="feature.html", context={"request": request, "current_page": "features"})



@app.get("/usecases-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_usecases_page(request: Request):
    return templates.TemplateResponse(request=request,name="usecase.html", context={"request": request, "current_page": "usecases"})


# Serve HTML Routes
@app.get("/languages-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_languages_page(request: Request):
    return templates.TemplateResponse(request=request,name="language.html",context= {"request": request, "current_page": "languages"})

@app.get("/skills-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_skills_page(request: Request):
    return templates.TemplateResponse(request=request,name="skill.html",context= {"request": request, "current_page": "skills"})


@app.get("/document-templates-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_document_templates_page(request: Request):
    return templates.TemplateResponse(request=request,name="document_template.html", context={"request": request, "current_page": "document_templates"})

@app.get("/projects-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_projects_page(request: Request):
    return templates.TemplateResponse(request=request,name="project.html", context={"request": request, "current_page": "projects"})


@app.get("/integrations-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_integrations_page(request: Request):
    return templates.TemplateResponse(request=request,name="integrations.html", context={"request": request, "current_page": "integrations"})

@app.get("/documentation-links-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_documentation_links_page(request: Request):
    return templates.TemplateResponse(request=request,name="documentation_link.html", context={"request": request, "current_page": "documentation_links"})

@app.get("/countries-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_countries_page(request: Request):
    return templates.TemplateResponse(request=request,name="country.html", context={"request": request, "current_page": "countries"})

@app.get("/master-objectives-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_master_objectives_page(request: Request):
    return templates.TemplateResponse(request=request,name="master_objective.html", context={"request": request, "current_page": "master_objectives"})

@app.get("/master-success-criteria-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_master_success_criteria_page(request: Request):
    return templates.TemplateResponse(request=request,name="master_success_criterion.html", context={"request": request, "current_page": "master_success_criteria"})

@app.get("/master-project-risks-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_master_project_risks_page(request: Request):
    return templates.TemplateResponse(request=request,name="master_project_risk.html", context={"request": request, "current_page": "master_project_risks"})

@app.get("/master-erp-systems-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_master_erp_systems_page(request: Request):
    return templates.TemplateResponse(request=request,name="master_erp_system.html", context={"request": request, "current_page": "master_erp_systems"})

@app.get("/custom-project-fields-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_custom_project_fields_page(request: Request):
    return templates.TemplateResponse(request=request,name="custom_project_fields.html", context={"request": request, "current_page": "custom_project_fields"})

@app.get("/csm-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_csm_page(request: Request):
    return templates.TemplateResponse(request=request,name="csm_list.html", context={"request": request, "current_page": "csm"})

@app.get("/csm-account-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_csm_account_page(request: Request):
    return templates.TemplateResponse(request=request,name="csm_account.html", context={"request": request, "current_page": "csm"})


@app.get("/credentials-page",response_class=HTMLResponse,include_in_schema=False)
async def serve_credentials_page(request: Request):
    return templates.TemplateResponse(request=request,name="credentials.html", context={"request": request, "current_page": "credentials"})


@app.get("/scalar",include_in_schema=False)
async def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API"
    )