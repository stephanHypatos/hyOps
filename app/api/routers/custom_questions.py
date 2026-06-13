from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, delete as sa_delete, or_
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.database.session import SessionDep
from app.database.models import CustomSection, CustomQuestion

router = APIRouter(tags=["custom-fields"])


class SectionCreate(BaseModel):
    name: str
    order: int = 0
    use_case_id: Optional[UUID] = None


class SectionUpdate(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None
    use_case_id: Optional[UUID] = None


class SectionRead(BaseModel):
    id: UUID
    name: str
    order: int
    use_case_id: Optional[UUID]


class QuestionCreate(BaseModel):
    section_id: UUID
    label: str
    type: str = "text"
    options: list[str] = []
    required: bool = False
    order: int = 0
    help_text: Optional[str] = None


class QuestionUpdate(BaseModel):
    label: Optional[str] = None
    type: Optional[str] = None
    options: Optional[list[str]] = None
    required: Optional[bool] = None
    order: Optional[int] = None
    help_text: Optional[str] = None


class QuestionRead(BaseModel):
    id: UUID
    section_id: UUID
    label: str
    type: str
    options: list[str]
    required: bool
    order: int
    help_text: Optional[str]


class SectionWithQuestions(BaseModel):
    id: UUID
    name: str
    order: int
    use_case_id: Optional[UUID]
    questions: list[QuestionRead]


# ── Sections ────────────────────────────────────────────────────────────────

@router.get("/custom-sections/with-questions", response_model=list[SectionWithQuestions])
async def get_sections_with_questions(
    session: SessionDep,
    use_case_id: Optional[UUID] = Query(default=None),
    include_all: bool = Query(default=False),
):
    q = select(CustomSection).order_by(CustomSection.order, CustomSection.created_at)
    if not include_all:
        if use_case_id is not None:
            # global sections + sections for this use case
            q = q.where(or_(CustomSection.use_case_id == None, CustomSection.use_case_id == use_case_id))
        else:
            # global sections only
            q = q.where(CustomSection.use_case_id == None)
    sections = (await session.execute(q)).scalars().all()
    result = []
    for s in sections:
        qs = (
            await session.execute(
                select(CustomQuestion)
                .where(CustomQuestion.section_id == s.id)
                .order_by(CustomQuestion.order, CustomQuestion.created_at)
            )
        ).scalars().all()
        result.append(SectionWithQuestions(
            id=s.id, name=s.name, order=s.order, use_case_id=s.use_case_id,
            questions=[
                QuestionRead(
                    id=q.id, section_id=q.section_id, label=q.label, type=q.type,
                    options=q.options or [], required=q.required, order=q.order,
                    help_text=q.help_text,
                )
                for q in qs
            ],
        ))
    return result


@router.get("/custom-sections/", response_model=list[SectionRead])
async def list_sections(session: SessionDep):
    rows = (await session.execute(select(CustomSection).order_by(CustomSection.order))).scalars().all()
    return rows


@router.post("/custom-sections/", response_model=SectionRead)
async def create_section(body: SectionCreate, session: SessionDep):
    s = CustomSection(**body.model_dump())
    session.add(s)
    await session.commit()
    await session.refresh(s)
    return s


@router.patch("/custom-sections/{sid}", response_model=SectionRead)
async def update_section(sid: UUID, body: SectionUpdate, session: SessionDep):
    s = await session.get(CustomSection, sid)
    if not s:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    await session.commit()
    await session.refresh(s)
    return s


@router.delete("/custom-sections/{sid}")
async def delete_section(sid: UUID, session: SessionDep):
    s = await session.get(CustomSection, sid)
    if not s:
        raise HTTPException(404)
    await session.execute(sa_delete(CustomQuestion).where(CustomQuestion.section_id == sid))
    await session.delete(s)
    await session.commit()
    return {"ok": True}


# ── Questions ────────────────────────────────────────────────────────────────

@router.get("/custom-questions/", response_model=list[QuestionRead])
async def list_questions(session: SessionDep, section_id: Optional[UUID] = None):
    q = select(CustomQuestion).order_by(CustomQuestion.order, CustomQuestion.created_at)
    if section_id:
        q = q.where(CustomQuestion.section_id == section_id)
    rows = (await session.execute(q)).scalars().all()
    return [QuestionRead(id=r.id, section_id=r.section_id, label=r.label, type=r.type,
                         options=r.options or [], required=r.required, order=r.order,
                         help_text=r.help_text) for r in rows]


@router.post("/custom-questions/", response_model=QuestionRead)
async def create_question(body: QuestionCreate, session: SessionDep):
    q = CustomQuestion(**body.model_dump())
    session.add(q)
    await session.commit()
    await session.refresh(q)
    return QuestionRead(id=q.id, section_id=q.section_id, label=q.label, type=q.type,
                        options=q.options or [], required=q.required, order=q.order,
                        help_text=q.help_text)


@router.patch("/custom-questions/{qid}", response_model=QuestionRead)
async def update_question(qid: UUID, body: QuestionUpdate, session: SessionDep):
    q = await session.get(CustomQuestion, qid)
    if not q:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(q, k, v)
    await session.commit()
    await session.refresh(q)
    return QuestionRead(id=q.id, section_id=q.section_id, label=q.label, type=q.type,
                        options=q.options or [], required=q.required, order=q.order,
                        help_text=q.help_text)


@router.delete("/custom-questions/{qid}")
async def delete_question(qid: UUID, session: SessionDep):
    q = await session.get(CustomQuestion, qid)
    if not q:
        raise HTTPException(404)
    await session.delete(q)
    await session.commit()
    return {"ok": True}
