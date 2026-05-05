from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, select
from app.database.models import DocumentTemplate, DocumentTemplateType
from app.database.session import SessionDep
from app.api.schemas.document_template import DocumentTemplateCreate,DocumentTemplateRead,DocumentTemplateUpdate

router = APIRouter(prefix="/document-template", tags=["Document Template"])



# ===================== Endpoints =====================
@router.get("/document-templates", response_model=list[DocumentTemplateRead])
async def get_all_document_templates(session: SessionDep):
    result = await session.execute(select(DocumentTemplate))
    return result.scalars().all()

@router.get("/", response_model=DocumentTemplateRead)
async def get_document_template(id: UUID, session: SessionDep):
    template = await session.get(DocumentTemplate, id)
    if not template: 
        raise HTTPException(status_code=404, detail="Document Template not found")
    return template

@router.post("/", response_model=None)
async def create_document_template(data: DocumentTemplateCreate, session: SessionDep) -> dict[str, UUID]:
    # Pydantic will automatically ensure 'variables' is a list of strings here
    new_template = DocumentTemplate(**data.model_dump())
    session.add(new_template)
    await session.commit()
    await session.refresh(new_template)
    return {"id": new_template.id}

@router.patch("/", response_model=DocumentTemplateRead)
async def update_document_template(id: UUID, data: DocumentTemplateUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data: 
        raise HTTPException(status_code=400, detail="No data to update")
    
    template = await session.get(DocumentTemplate, id)
    if not template: 
        raise HTTPException(status_code=404, detail="Document Template not found")
    
    # Manually update timestamp
    update_data["updated_at"] = datetime.now()
    
    template.sqlmodel_update(update_data)
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template

@router.delete("/")
async def delete_document_template(id: UUID, session: SessionDep):
    template = await session.get(DocumentTemplate, id)
    if not template: 
        raise HTTPException(status_code=404, detail="Document Template not found")
    await session.delete(template)
    await session.commit()
    return {"detail": "Deleted"}