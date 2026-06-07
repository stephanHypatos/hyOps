from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.database.models import DocumentationLink
from app.database.session import SessionDep
from app.api.schemas.documentation_link import (
    DocumentationLinkCreate,
    DocumentationLinkRead,
    DocumentationLinkUpdate,
)

router = APIRouter(prefix="/documentation-links", tags=["Documentation Links"])


@router.get("/", response_model=list[DocumentationLinkRead])
async def get_all_documentation_links(session: SessionDep):
    result = await session.execute(select(DocumentationLink))
    return result.scalars().all()


@router.get("/{link_id}", response_model=DocumentationLinkRead)
async def get_documentation_link(link_id: UUID, session: SessionDep):
    link = await session.get(DocumentationLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Documentation link not found")
    return link


@router.post("/", response_model=DocumentationLinkRead)
async def create_documentation_link(data: DocumentationLinkCreate, session: SessionDep):
    link = DocumentationLink(**data.model_dump())
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@router.patch("/{link_id}", response_model=DocumentationLinkRead)
async def update_documentation_link(
    link_id: UUID, data: DocumentationLinkUpdate, session: SessionDep
):
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    link = await session.get(DocumentationLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Documentation link not found")
    update_data["updated_at"] = datetime.utcnow()
    link.sqlmodel_update(update_data)
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


@router.delete("/{link_id}")
async def delete_documentation_link(link_id: UUID, session: SessionDep):
    link = await session.get(DocumentationLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Documentation link not found")
    await session.delete(link)
    await session.commit()
    return {"detail": "Deleted"}
