from fastapi import APIRouter
from .routers import organization, user, subtype, capability, feature, skill, language, document_template, project, usecase
from .routers import metabase, teams, slack, jira
from .routers import documentation_link, smtp_config

# Single router to group all api routers
master_router = APIRouter()

# Core domain routers
master_router.include_router(organization.router)
master_router.include_router(user.router)
master_router.include_router(subtype.router)
master_router.include_router(capability.router)
master_router.include_router(feature.router)
master_router.include_router(skill.router)
master_router.include_router(language.router)
master_router.include_router(document_template.router)
master_router.include_router(project.router)
master_router.include_router(usecase.router)

master_router.include_router(documentation_link.router)
master_router.include_router(smtp_config.router)

# Integration routers
master_router.include_router(metabase.router)
master_router.include_router(teams.router)
master_router.include_router(slack.router)
master_router.include_router(jira.router)
