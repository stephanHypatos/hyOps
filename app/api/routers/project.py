from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import Optional
from datetime import datetime
from sqlmodel import select

from app.database.models import (
    Project, ProjectStakeholder, ProjectUsecase, 
    User, Usecase
)
from app.database.session import SessionDep
from app.api.schemas.project import (
    ProjectCreate, ProjectRead, ProjectUpdate,
    StakeholderRead, StakeholderReadEnriched, StakeholderAssign,
    UsecaseAssign, UsecaseRead
)
from pathlib import Path
from datetime import datetime
from app.adapters.project_adapter import project_to_form_data, FeatureDBAdapter
from app.modules.document_generator import DocumentGenerator
import os
from fastapi.responses import FileResponse

router = APIRouter(prefix="/project", tags=["Project"])


# ===================== Project CRUD Endpoints =====================

@router.get("/projects", response_model=list[ProjectRead])
async def get_all_projects(session: SessionDep):
    result = await session.execute(select(Project))
    return result.scalars().all()


@router.get("/", response_model=ProjectRead)
async def get_project(id: UUID, session: SessionDep):
    project = await session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=dict)
async def create_project(data: ProjectCreate, session: SessionDep):
    new_project = Project(**data.model_dump())
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return {"id": new_project.id}


@router.patch("/", response_model=ProjectRead)
async def update_project(id: UUID, data: ProjectUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    project = await session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data["updated_at"] = datetime.now()
    project.sqlmodel_update(update_data)
    
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@router.delete("/")
async def delete_project(id: UUID, session: SessionDep):
    project = await session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"detail": "Deleted"}


# ===================== Stakeholder M2M Endpoints =====================

@router.get("/{project_id}/stakeholders", response_model=list[StakeholderReadEnriched])
async def get_project_stakeholders(project_id: UUID, session: SessionDep):
    """
    Get stakeholders with enriched user details (name, email).
    Single query JOIN eliminates N+1 lookups on the frontend.
    """
    result = await session.execute(
        select(ProjectStakeholder, User)
        .join(User, ProjectStakeholder.user_id == User.id)
        .where(ProjectStakeholder.project_id == project_id)
    )
    rows = result.all()
    
    return [
        StakeholderReadEnriched(
            project_id=ps.project_id,
            user_id=ps.user_id,
            role=ps.role,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email
        )
        for ps, user in rows
    ]


@router.post("/{project_id}/stakeholder", response_model=StakeholderRead)
async def assign_stakeholder(project_id: UUID, data: StakeholderAssign, session: SessionDep):
    # Validate user exists
    user = await session.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate project exists
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check for duplicate
    existing = await session.get(ProjectStakeholder, (project_id, data.user_id))
    if existing:
        raise HTTPException(status_code=400, detail="User is already a stakeholder in this project")
    
    link = ProjectStakeholder(project_id=project_id, **data.model_dump())
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@router.delete("/{project_id}/stakeholder/{user_id}")
async def remove_stakeholder(project_id: UUID, user_id: UUID, session: SessionDep):
    link = await session.get(ProjectStakeholder, (project_id, user_id))
    if not link:
        raise HTTPException(status_code=404, detail="Stakeholder not found in this project")
    await session.delete(link)
    await session.commit()
    return {"detail": "Stakeholder removed"}


# ===================== Usecase M2M Endpoints =====================

@router.get("/{project_id}/usecases", response_model=list[UsecaseRead])
async def get_project_usecases(project_id: UUID, session: SessionDep):
    result = await session.execute(
        select(ProjectUsecase).where(ProjectUsecase.project_id == project_id)
    )
    return result.scalars().all()


@router.post("/{project_id}/usecase")
async def assign_usecase(project_id: UUID, data: UsecaseAssign, session: SessionDep):
    # Validate usecase exists
    usecase = await session.get(Usecase, data.usecase_id)
    if not usecase:
        raise HTTPException(status_code=404, detail="Usecase not found")
    
    # Check for duplicate
    existing = await session.get(ProjectUsecase, (project_id, data.usecase_id))
    if existing:
        raise HTTPException(status_code=400, detail="Usecase is already in this project")
    
    link = ProjectUsecase(project_id=project_id, **data.model_dump())
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@router.delete("/{project_id}/usecase/{usecase_id}")
async def remove_usecase(project_id: UUID, usecase_id: UUID, session: SessionDep):
    link = await session.get(ProjectUsecase, (project_id, usecase_id))
    if not link:
        raise HTTPException(status_code=404, detail="Usecase not found in this project")
    await session.delete(link)
    await session.commit()
    return {"detail": "Usecase removed from project"}





# ===================== Document Generation Endpoint =====================

@router.post("/{project_id}/generate-documents")
async def generate_project_documents(project_id: UUID, session: SessionDep):
    """
    Generates SOW, Success Contract, and Solution Design documents for a project.
    Uses the DB models -> form_data adapter -> existing DocumentGenerator.
    """
    # 1. Fetch project (selectin relationships in the model auto-load stakeholders, usecases, etc.)
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # 2. Convert DB models to the dict format DocumentGenerator expects
        form_data = project_to_form_data(project)
        
        # 3. Build the feature requirements adapter
        all_features = []
        for uc in project.linked_usecases:
            all_features.extend(uc.features)
        fake_db_manager = FeatureDBAdapter(all_features)
        import os
        from app.config import basedir
        # 4. Generate documents
        output_dir = os.path.join(basedir,'generated_documents',str(project.id))
        print(output_dir)
        # output_dir = Path("generated_documents") / str(project.id)
        doc_gen = DocumentGenerator(output_dir, db_manager=fake_db_manager)
        
        documents = doc_gen.generate_all_documents(form_data, submission_id=0)
        
        # 5. Save generated document paths back to the project record
        update_data = {
            "sow_markdown_path": documents.get('sow'),
            "sow_docx_path": documents.get('sow_docx'),
            "success_contract_path": documents.get('success_contract'),
            "solution_design_path": documents.get('solution_design'),
            # "status": "completed", # Update status to completed
            "updated_at": datetime.now()
        }
        project.sqlmodel_update(update_data)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        
        return {
            "detail": "Documents generated successfully",
            "paths": {
                "sow": documents.get('sow'),
                "sow_docx": documents.get('sow_docx'),
                "success_contract": documents.get('success_contract'),
                "solution_design": documents.get('solution_design')
            }
        }
    except Exception as e:
        print("===============================================")
        print('Error',e)
        print("===============================================")
        raise HTTPException(status_code=500, detail=f"Error generating documents: {str(e)}")
    





@router.get("/{project_id}/download/{document_type}")
async def download_generated_document(
    project_id: UUID, 
    document_type: str, 
    session: SessionDep
):
    """
    Downloads a generated document for a project.
    document_type: 'sow' | 'sow_docx' | 'success_contract' | 'solution_design'
    """
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Map document type to the stored path field
    path_map = {
        "sow": project.sow_markdown_path,
        "sow_docx": project.sow_docx_path,
        "success_contract": project.success_contract_path,
        "solution_design": project.solution_design_path,
    }
    
    file_path = path_map.get(document_type)
    if not file_path:
        raise HTTPException(
            status_code=404, 
            detail=f"Document '{document_type}' not found or not generated yet"
        )
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, 
            detail="File not found on disk. It may have been moved or deleted."
        )
    
    # Determine filename and media type based on extension
    filename = os.path.basename(file_path)
    if file_path.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_path.endswith(".md"):
        media_type = "text/markdown"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=file_path, 
        media_type=media_type, 
        filename=filename
    )