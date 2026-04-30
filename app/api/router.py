from fastapi import APIRouter
from .routers import organization, user, subtype, capability, feature

# Single router to group all api routers
master_router = APIRouter()

master_router.include_router(organization.router)
master_router.include_router(user.router)
master_router.include_router(subtype.router)
master_router.include_router(capability.router)
master_router.include_router(feature.router)
