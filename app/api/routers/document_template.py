# from fastapi import APIRouter, HTTPException, status
# from uuid import UUID
# from typing import Optional
# from datetime import datetime
# from sqlmodel import SQLModel, select
# from app.database.models import DocumentTemplate, DocumentTemplateType
# from app.database.session import SessionDep
# from app.api.schemas.document_template import DocumentTemplateCreate,DocumentTemplateRead,DocumentTemplateUpdate

# router = APIRouter(prefix="/document-template", tags=["Document Template"])



# # ===================== Endpoints =====================
# @router.get("/document-templates", response_model=list[DocumentTemplateRead])
# async def get_all_document_templates(session: SessionDep):
#     result = await session.execute(select(DocumentTemplate))
#     return result.scalars().all()

# @router.get("/", response_model=DocumentTemplateRead)
# async def get_document_template(id: UUID, session: SessionDep):
#     template = await session.get(DocumentTemplate, id)
#     if not template: 
#         raise HTTPException(status_code=404, detail="Document Template not found")
#     return template

# @router.post("/", response_model=None)
# async def create_document_template(data: DocumentTemplateCreate, session: SessionDep) -> dict[str, UUID]:
#     # Pydantic will automatically ensure 'variables' is a list of strings here
#     new_template = DocumentTemplate(**data.model_dump())
#     session.add(new_template)
#     await session.commit()
#     await session.refresh(new_template)
#     return {"id": new_template.id}

# @router.patch("/", response_model=DocumentTemplateRead)
# async def update_document_template(id: UUID, data: DocumentTemplateUpdate, session: SessionDep):
#     update_data = data.model_dump(exclude_none=True)
#     if not update_data: 
#         raise HTTPException(status_code=400, detail="No data to update")
    
#     template = await session.get(DocumentTemplate, id)
#     if not template: 
#         raise HTTPException(status_code=404, detail="Document Template not found")
    
#     # Manually update timestamp
#     update_data["updated_at"] = datetime.now()
    
#     template.sqlmodel_update(update_data)
#     session.add(template)
#     await session.commit()
#     await session.refresh(template)
#     return template

# @router.delete("/")
# async def delete_document_template(id: UUID, session: SessionDep):
#     template = await session.get(DocumentTemplate, id)
#     if not template: 
#         raise HTTPException(status_code=404, detail="Document Template not found")
#     await session.delete(template)
#     await session.commit()
#     return {"detail": "Deleted"}




## app/api/endpoints/document_template.py

from fastapi import APIRouter, HTTPException
from uuid import UUID
from datetime import datetime
from sqlmodel import select
import os

from app.database.models import DocumentTemplate
from app.database.session import SessionDep
from app.api.schemas.document_template import DocumentTemplateCreate, DocumentTemplateRead, DocumentTemplateUpdate

router = APIRouter(prefix="/document-template", tags=["Document Template"])


# 🆕 Helper function to generate and save the file
def generate_template_file(template_id: UUID, markdown_content: str, file_format: str) -> str:
    from app.config import basedir
    
    # Ensure the output directory exists
    output_dir = os.path.join(basedir, 'generated_templates')
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{template_id}.{file_format}"
    file_path = os.path.join(output_dir, filename)
    
    if file_format == "md":
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
    elif file_format == "docx":
        # Requires python-docx: pip install python-docx
        from docx import Document
        
        doc = Document()
        # Add markdown content as paragraphs (splits by newline)
        for line in markdown_content.split('\n'):
            doc.add_paragraph(line)
        doc.save(file_path)
        
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
        
    return file_path


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


@router.post("/", response_model=DocumentTemplateRead)
async def create_document_template(data: DocumentTemplateCreate, session: SessionDep):
    # 1. Create DB record first to get the ID
    new_template = DocumentTemplate(**data.model_dump())
    session.add(new_template)
    await session.commit()
    await session.refresh(new_template)
    
    # 2. Generate the file using the new ID
    try:
        file_path = generate_template_file(
            template_id=new_template.id,
            markdown_content=new_template.markdown_content,
            file_format=new_template.file_format
        )
        # 3. Update record with the saved file path
        new_template.file_path = file_path
        session.add(new_template)
        await session.commit()
        await session.refresh(new_template)
    except Exception as e:
        # If file generation fails, delete the DB record to avoid orphans
        await session.delete(new_template)
        await session.commit()
        raise HTTPException(status_code=500, detail=f"Error generating file: {str(e)}")
        
    return new_template


@router.patch("/", response_model=DocumentTemplateRead)
async def update_document_template(id: UUID, data: DocumentTemplateUpdate, session: SessionDep):
    update_data = data.model_dump(exclude_none=True)
    if not update_data: 
        raise HTTPException(status_code=400, detail="No data to update")
    
    template = await session.get(DocumentTemplate, id)
    if not template: 
        raise HTTPException(status_code=404, detail="Document Template not found")
    
    # Update timestamp
    update_data["updated_at"] = datetime.now()
    template.sqlmodel_update(update_data)
    session.add(template)
    await session.commit()
    await session.refresh(template)
    
    # 🆕 Regenerate file if content or format changed
    content_changed = "markdown_content" in update_data
    format_changed = "file_format" in update_data
    
    if content_changed or format_changed:
        try:
            # Delete old file if format changed (so we don't leave .md when switching to .docx)
            if format_changed and template.file_path and os.path.exists(template.file_path):
                os.remove(template.file_path)
                
            file_path = generate_template_file(
                template_id=template.id,
                markdown_content=template.markdown_content,
                file_format=template.file_format
            )
            template.file_path = file_path
            session.add(template)
            await session.commit()
            await session.refresh(template)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error regenerating file: {str(e)}")
    
    return template


@router.delete("/")
async def delete_document_template(id: UUID, session: SessionDep):
    template = await session.get(DocumentTemplate, id)
    if not template: 
        raise HTTPException(status_code=404, detail="Document Template not found")
    
    # 🆕 Delete the file from disk
    if template.file_path and os.path.exists(template.file_path):
        os.remove(template.file_path)
        
    await session.delete(template)
    await session.commit()
    return {"detail": "Deleted"}