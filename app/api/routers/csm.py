from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime

from app.database.session import SessionDep
from app.database.models import (
    Organization, User, Project, Contract, AccountHealth,
    OrganizationTeamsGroup, OrganizationSlackChannel, OrganizationJiraProject,
    ProjectStatus,
)

router = APIRouter(tags=["csm"])


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class ContractCreate(BaseModel):
    org_id: UUID
    project_id: Optional[UUID] = None
    name: str
    type: str = "MSA"
    status: str = "active"
    url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    paid: bool = False

class ContractUpdate(BaseModel):
    project_id: Optional[UUID] = None
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    paid: Optional[bool] = None

class ContractRead(BaseModel):
    id: UUID
    org_id: UUID
    project_id: Optional[UUID]
    name: str
    type: str
    status: str
    url: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    renewal_date: Optional[date]
    paid: bool
    created_at: datetime

class HealthCreate(BaseModel):
    org_id: UUID
    status: str  # green / yellow / red / churned
    comment: Optional[str] = None
    created_by_id: Optional[UUID] = None

class HealthRead(BaseModel):
    id: UUID
    org_id: UUID
    status: str
    comment: Optional[str]
    created_by_id: Optional[UUID]
    created_at: datetime

class UserSummary(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str

class CsmAccountListItem(BaseModel):
    id: UUID
    name: str
    type: str
    account_status: Optional[str]
    health_status: Optional[str]
    health_comment: Optional[str]
    csm: Optional[UserSummary]
    active_project_count: int
    has_unpaid_contracts: bool

class ProjectSummary(BaseModel):
    id: UUID
    name: str
    type: str
    status: str
    start_date: Optional[date]
    go_live_date: Optional[date]
    target_erp: list
    integration_type: Optional[str]

class IntegrationStatus(BaseModel):
    teams: bool
    jira: bool
    slack: bool

class AccountOverview(BaseModel):
    org: dict
    csm: Optional[UserSummary]
    account_executive: Optional[UserSummary]
    sales_representative: Optional[UserSummary]
    current_health: Optional[HealthRead]
    health_history: list[HealthRead]
    contracts: list[ContractRead]
    projects: list[ProjectSummary]
    integrations: IntegrationStatus


# ── Helpers ──────────────────────────────────────────────────────────────────

def _user_summary(u: User) -> UserSummary:
    return UserSummary(id=u.id, first_name=u.first_name, last_name=u.last_name, email=u.email)

def _contract_read(c: Contract) -> ContractRead:
    return ContractRead(
        id=c.id, org_id=c.org_id, project_id=c.project_id, name=c.name,
        type=c.type, status=c.status, url=c.url,
        start_date=c.start_date, end_date=c.end_date, renewal_date=c.renewal_date,
        paid=c.paid, created_at=c.created_at,
    )

def _health_read(h: AccountHealth) -> HealthRead:
    return HealthRead(
        id=h.id, org_id=h.org_id, status=h.status, comment=h.comment,
        created_by_id=h.created_by_id, created_at=h.created_at,
    )


# ── CSM account list ─────────────────────────────────────────────────────────

@router.get("/csm-accounts/", response_model=list[CsmAccountListItem])
async def list_csm_accounts(session: SessionDep):
    orgs = (await session.execute(select(Organization).order_by(Organization.name))).scalars().all()

    # Latest health per org
    subq = (
        select(AccountHealth.org_id, func.max(AccountHealth.created_at).label("max_ts"))
        .group_by(AccountHealth.org_id)
        .subquery()
    )
    latest_health_rows = (
        await session.execute(
            select(AccountHealth).join(
                subq,
                (AccountHealth.org_id == subq.c.org_id) & (AccountHealth.created_at == subq.c.max_ts)
            )
        )
    ).scalars().all()
    latest_health = {str(h.org_id): h for h in latest_health_rows}

    # Active project count per org (status != 'completed' / 'cancelled')
    proj_counts = (
        await session.execute(
            select(Project.customer_id, func.count(Project.id).label("cnt"))
            .where(Project.status == ProjectStatus.draft)
            .group_by(Project.customer_id)
        )
    ).all()
    active_counts = {str(r.customer_id): r.cnt for r in proj_counts}

    # Unpaid contracts per org
    unpaid_orgs = set(
        str(r[0]) for r in (
            await session.execute(
                select(Contract.org_id).where(Contract.paid == False).distinct()
            )
        ).all()
    )

    # CSM user lookup
    csm_ids = {o.csm_id for o in orgs if o.csm_id}
    csm_users = {}
    if csm_ids:
        rows = (await session.execute(select(User).where(User.id.in_(csm_ids)))).scalars().all()
        csm_users = {str(u.id): u for u in rows}

    result = []
    for org in orgs:
        h = latest_health.get(str(org.id))
        csm_user = csm_users.get(str(org.csm_id)) if org.csm_id else None
        result.append(CsmAccountListItem(
            id=org.id, name=org.name, type=org.type.value,
            account_status=org.account_status,
            health_status=h.status if h else None,
            health_comment=h.comment if h else None,
            csm=_user_summary(csm_user) if csm_user else None,
            active_project_count=active_counts.get(str(org.id), 0),
            has_unpaid_contracts=str(org.id) in unpaid_orgs,
        ))
    return result


# ── Account overview (360°) ───────────────────────────────────────────────────

@router.get("/csm-accounts/{org_id}/overview", response_model=AccountOverview)
async def get_account_overview(org_id: UUID, session: SessionDep):
    org = await session.get(Organization, org_id)
    if not org:
        raise HTTPException(404)

    # Resolve named users (CSM / AE / SalesRep)
    named_ids = {uid for uid in [org.csm_id, org.account_executive_id, org.sales_representative_id] if uid}
    named_users = {}
    if named_ids:
        rows = (await session.execute(select(User).where(User.id.in_(named_ids)))).scalars().all()
        named_users = {str(u.id): u for u in rows}

    # Health history
    health_rows = (
        await session.execute(
            select(AccountHealth).where(AccountHealth.org_id == org_id)
            .order_by(AccountHealth.created_at.desc())
        )
    ).scalars().all()

    # Contracts
    contract_rows = (
        await session.execute(select(Contract).where(Contract.org_id == org_id).order_by(Contract.created_at.desc()))
    ).scalars().all()

    # Projects
    project_rows = (
        await session.execute(select(Project).where(Project.customer_id == org_id).order_by(Project.start_date.desc()))
    ).scalars().all()

    # Integrations
    has_teams = bool((await session.execute(select(OrganizationTeamsGroup).where(OrganizationTeamsGroup.organization_id == org_id))).first())
    has_jira = bool((await session.execute(select(OrganizationJiraProject).where(OrganizationJiraProject.organization_id == org_id))).first())
    has_slack = bool((await session.execute(select(OrganizationSlackChannel).where(OrganizationSlackChannel.organization_id == org_id))).first())

    def _u(uid): return _user_summary(named_users[str(uid)]) if uid and str(uid) in named_users else None

    org_dict = {
        "id": str(org.id), "name": org.name, "type": org.type.value,
        "email": org.email, "industry": org.industry, "country": org.country,
        "account_status": org.account_status,
        "health_score_question_id": org.health_score_question_id,
        "key": org.key,
    }

    return AccountOverview(
        org=org_dict,
        csm=_u(org.csm_id),
        account_executive=_u(org.account_executive_id),
        sales_representative=_u(org.sales_representative_id),
        current_health=_health_read(health_rows[0]) if health_rows else None,
        health_history=[_health_read(h) for h in health_rows],
        contracts=[_contract_read(c) for c in contract_rows],
        projects=[
            ProjectSummary(
                id=p.id, name=p.name, type=p.type.value, status=p.status.value,
                start_date=p.start_date, go_live_date=p.go_live_date,
                target_erp=p.target_erp or [], integration_type=p.integration_type,
            )
            for p in project_rows
        ],
        integrations=IntegrationStatus(teams=has_teams, jira=has_jira, slack=has_slack),
    )


# ── Contracts CRUD ───────────────────────────────────────────────────────────

@router.get("/contracts/", response_model=list[ContractRead])
async def list_contracts(session: SessionDep, org_id: Optional[UUID] = None, project_id: Optional[UUID] = None):
    q = select(Contract).order_by(Contract.created_at.desc())
    if org_id:
        q = q.where(Contract.org_id == org_id)
    if project_id:
        q = q.where(Contract.project_id == project_id)
    rows = (await session.execute(q)).scalars().all()
    return [_contract_read(c) for c in rows]

@router.post("/contracts/", response_model=ContractRead)
async def create_contract(body: ContractCreate, session: SessionDep):
    c = Contract(**body.model_dump())
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return _contract_read(c)

@router.patch("/contracts/{cid}", response_model=ContractRead)
async def update_contract(cid: UUID, body: ContractUpdate, session: SessionDep):
    c = await session.get(Contract, cid)
    if not c:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(c, k, v)
    await session.commit()
    await session.refresh(c)
    return _contract_read(c)

@router.delete("/contracts/{cid}")
async def delete_contract(cid: UUID, session: SessionDep):
    c = await session.get(Contract, cid)
    if not c:
        raise HTTPException(404)
    await session.delete(c)
    await session.commit()
    return {"ok": True}


# ── Account Health CRUD ───────────────────────────────────────────────────────

@router.get("/account-health/{org_id}", response_model=list[HealthRead])
async def get_health_history(org_id: UUID, session: SessionDep):
    rows = (
        await session.execute(
            select(AccountHealth).where(AccountHealth.org_id == org_id)
            .order_by(AccountHealth.created_at.desc())
        )
    ).scalars().all()
    return [_health_read(h) for h in rows]

@router.post("/account-health/", response_model=HealthRead)
async def add_health_entry(body: HealthCreate, session: SessionDep):
    h = AccountHealth(**body.model_dump())
    session.add(h)
    await session.commit()
    await session.refresh(h)
    return _health_read(h)

@router.delete("/account-health/entry/{hid}")
async def delete_health_entry(hid: UUID, session: SessionDep):
    h = await session.get(AccountHealth, hid)
    if not h:
        raise HTTPException(404)
    await session.delete(h)
    await session.commit()
    return {"ok": True}
