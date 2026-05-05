from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from datetime import datetime
from sqlmodel import select
from app.database.models import Project, ProjectType, IntegrationType,ProjectStakeholder
from app.database.session import SessionDep
from app.api.schemas.project import ProjectRead,ProjectCreate, ProjectUpdate, StakeholderAssign,StakeholderRead,UsecaseAssign


router = APIRouter(prefix="/project", tags=["Project"])


# ===================== Endpoints =====================
@router.get("/projects", response_model=list[ProjectRead])
async def get_all_projects(session: SessionDep):
    result = await session.execute(select(Project))
    return result.scalars().all()

@router.get("/", response_model=ProjectRead)
async def get_project(id: UUID, session: SessionDep):
    project = await session.get(Project, id)
    if not project: raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/", response_model=None)
async def create_project(data: ProjectCreate, session: SessionDep) -> dict[str, UUID]:
    new_project = Project(**data.model_dump())
    if "start_date" in new_project:
        new_project["start_date"] = datetime.strptime(
            new_project["start_date"], "%Y-%m-%d"
        ).date()
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return {"id": new_project.id}

@router.patch("/", response_model=ProjectRead)
async def update_project(id: UUID, data: ProjectUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data: raise HTTPException(status_code=400, detail="No data to update")
    
    project = await session.get(Project, id)
    if not project: raise HTTPException(status_code=404, detail="Project not found")
    
    from datetime import datetime

    if "start_date" in update_data:
        update_data["start_date"] = datetime.strptime(
            update_data["start_date"], "%Y-%m-%d"
        ).date()
    update_data["updated_at"] = datetime.now()
    project.sqlmodel_update(update_data)
    
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project

@router.delete("/")
async def delete_project(id: UUID, session: SessionDep):
    project = await session.get(Project, id)
    if not project: raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"detail": "Deleted"}


# ===================== Stakeholder Endpoints =====================

# GET all stakeholders for a specific project
@router.get("/{project_id}/stakeholders", response_model=list[StakeholderRead])
async def get_project_stakeholders(project_id: UUID, session: SessionDep):
    result = await session.execute(
        select(ProjectStakeholder).where(ProjectStakeholder.project_id == project_id)
    )
    return result.scalars().all()

# POST (Assign) a stakeholder to a project
@router.post("/{project_id}/stakeholder", response_model=StakeholderRead)
async def assign_stakeholder(project_id: UUID, data: StakeholderAssign, session: SessionDep):
    # Check if already assigned
    existing = await session.get(ProjectStakeholder, (project_id, data.user_id))
    if existing:
        raise HTTPException(status_code=400, detail="User is already a stakeholder in this project")
    
    link = ProjectStakeholder(project_id=project_id, **data.model_dump())
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link

# DELETE (Remove) a stakeholder from a project
@router.delete("/{project_id}/stakeholder/{user_id}")
async def remove_stakeholder(project_id: UUID, user_id: UUID, session: SessionDep):
    link = await session.get(ProjectStakeholder, (project_id, user_id))
    if not link:
        raise HTTPException(status_code=404, detail="Stakeholder not found in this project")
    
    await session.delete(link)
    await session.commit()
    return {"detail": "Stakeholder removed"}




# ===================== Usecase M2M Endpoints =====================

# GET all usecases for a specific project
# @router.get("/{project_id}/usecases")
# async def get_project_usecases(project_id: UUID, session: SessionDep):
#     result = await session.execute(
#         select(ProjectUsecase).where(ProjectUsecase.project_id == project_id)
#     )
#     return result.scalars().all()

# # POST (Assign) a usecase to a project
# @router.post("/{project_id}/usecase")
# async def assign_usecase(project_id: UUID, data: UsecaseAssign, session: SessionDep):
#     existing = await session.get(ProjectUsecase, (project_id, data.usecase_id))
#     if existing:
#         raise HTTPException(status_code=400, detail="Usecase is already in this project")
    
#     link = ProjectUsecase(project_id=project_id, **data.model_dump())
#     session.add(link)
#     await session.commit()
#     await session.refresh(link)
#     return link

# # DELETE (Remove) a usecase from a project
# @router.delete("/{project_id}/usecase/{usecase_id}")
# async def remove_usecase(project_id: UUID, usecase_id: UUID, session: SessionDep):
#     link = await session.get(ProjectUsecase, (project_id, usecase_id))
#     if not link:
#         raise HTTPException(status_code=404, detail="Usecase not found in this project")
    
#     await session.delete(link)
#     await session.commit()
#     return {"detail": "Usecase removed from project"}