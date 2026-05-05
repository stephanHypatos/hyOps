from fastapi import APIRouter
from .routers import organization, user, subtype, capability, feature,skill,language, document_template, project, usecase

# Single router to group all api routers
master_router = APIRouter()

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
