"""
Demo data seeder — POST /demo/seed to populate, DELETE /demo/seed to clear.
All records use fixed UUIDs so they can be identified and removed cleanly.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete as sql_delete
from sqlmodel import select

from app.database.models import (
    Capability,
    Country,
    Feature,
    FeatureUsecase,
    MasterERPSystem,
    MasterSuccessCriterion,
    Organization,
    OrganizationType,
    Project,
    ProjectStakeholder,
    ProjectStatus,
    ProjectType,
    ProjectUsecase,
    IntegrationType,
    ScopeType,
    Subtype,
    Usecase,
    User,
    UserRole,
    UserType,
)
from app.database.session import SessionDep

router = APIRouter(prefix="/demo", tags=["Demo"])

# ── Fixed UUIDs ────────────────────────────────────────────────────────────────
# Organizations
ORG_HYPATOS  = UUID("00000000-0000-0000-0000-000000000001")
ORG_ACME     = UUID("00000000-0000-0000-0000-000000000002")
ORG_EY       = UUID("00000000-0000-0000-0000-000000000003")

# Subtypes / roles
SUB_CSM      = UUID("00000000-0000-0000-0000-000000000010")
SUB_SA       = UUID("00000000-0000-0000-0000-000000000011")
SUB_PM       = UUID("00000000-0000-0000-0000-000000000012")
SUB_COE      = UUID("00000000-0000-0000-0000-000000000013")
SUB_SPONSOR  = UUID("00000000-0000-0000-0000-000000000014")

# Users — Hypatos (internal)
USR_CSM      = UUID("00000000-0000-0000-0000-000000000020")
USR_SA_INT   = UUID("00000000-0000-0000-0000-000000000021")
USR_PM_INT   = UUID("00000000-0000-0000-0000-000000000022")
# Users — Acme (customer)
USR_PM_CUST  = UUID("00000000-0000-0000-0000-000000000023")
USR_SPONSOR  = UUID("00000000-0000-0000-0000-000000000024")
# Users — EY Germany (partner)
USR_COE      = UUID("00000000-0000-0000-0000-000000000025")
USR_SA_EY    = UUID("00000000-0000-0000-0000-000000000026")
USR_PM_EY    = UUID("00000000-0000-0000-0000-000000000027")

# Usecases
UC_INVOICE   = UUID("00000000-0000-0000-0000-000000000030")
UC_PO_CONF   = UUID("00000000-0000-0000-0000-000000000031")
UC_ORDER_MGT = UUID("00000000-0000-0000-0000-000000000032")

# Capability + Features
CAP_CORE     = UUID("00000000-0000-0000-0000-000000000040")
FEAT_DOC_EXT = UUID("00000000-0000-0000-0000-000000000041")
FEAT_DUP_CHK = UUID("00000000-0000-0000-0000-000000000042")
FEAT_EINV    = UUID("00000000-0000-0000-0000-000000000043")
FEAT_MDE     = UUID("00000000-0000-0000-0000-000000000044")

# Countries
CTR_DE       = UUID("00000000-0000-0000-0000-000000000050")
CTR_FR       = UUID("00000000-0000-0000-0000-000000000051")
CTR_AT       = UUID("00000000-0000-0000-0000-000000000052")

# Master success criteria
MSC_1        = UUID("00000000-0000-0000-0000-000000000060")
MSC_2        = UUID("00000000-0000-0000-0000-000000000061")
MSC_3        = UUID("00000000-0000-0000-0000-000000000062")

# Master ERP systems
MERP_SAP_ECC = UUID("00000000-0000-0000-0000-000000000070")
MERP_SAP_S4  = UUID("00000000-0000-0000-0000-000000000071")
MERP_COUPA   = UUID("00000000-0000-0000-0000-000000000072")

# Project
PROJ_DEMO    = UUID("00000000-0000-0000-0000-000000000080")

_ALL_USER_IDS    = [USR_CSM, USR_SA_INT, USR_PM_INT, USR_PM_CUST, USR_SPONSOR, USR_COE, USR_SA_EY, USR_PM_EY]
_ALL_FEAT_IDS    = [FEAT_DOC_EXT, FEAT_DUP_CHK, FEAT_EINV, FEAT_MDE]
_ALL_UC_IDS      = [UC_INVOICE, UC_PO_CONF, UC_ORDER_MGT]
_ALL_ORG_IDS     = [ORG_ACME, ORG_EY, ORG_HYPATOS]
_ALL_SUB_IDS     = [SUB_CSM, SUB_SA, SUB_PM, SUB_COE, SUB_SPONSOR]
_ALL_CTR_IDS     = [CTR_DE, CTR_FR, CTR_AT]
_ALL_MSC_IDS     = [MSC_1, MSC_2, MSC_3]
_ALL_MERP_IDS    = [MERP_SAP_ECC, MERP_SAP_S4, MERP_COUPA]


# ── Status ─────────────────────────────────────────────────────────────────────

@router.get("/seed")
async def demo_status(session: SessionDep):
    existing = await session.get(Organization, ORG_HYPATOS)
    return {"seeded": existing is not None}


# ── Seed ───────────────────────────────────────────────────────────────────────

@router.post("/seed")
async def seed_demo(session: SessionDep):
    if await session.get(Organization, ORG_HYPATOS):
        raise HTTPException(status_code=409, detail="Demo data already exists — clear it first.")

    # 1. Subtypes (roles)
    for obj in [
        Subtype(id=SUB_CSM,     name="Customer Success Manager", description="Internal CSM responsible for customer success"),
        Subtype(id=SUB_SA,      name="Solution Architect",       description="Technical solution design and architecture"),
        Subtype(id=SUB_PM,      name="Project Manager",          description="Project planning and delivery"),
        Subtype(id=SUB_COE,     name="COE",                      description="Center of Excellence"),
        Subtype(id=SUB_SPONSOR, name="Project Sponsor",          description="Executive project sponsor"),
    ]:
        session.add(obj)

    # 2. Organizations
    for obj in [
        Organization(id=ORG_HYPATOS, name="Hypatos GmbH",    key="HYP", type=OrganizationType.internal,
                     email="info@hypatos.ai",    industry="Software",    country="Germany"),
        Organization(id=ORG_ACME,    name="Acme Industries", key="ACM", type=OrganizationType.customer,
                     email="contact@acme.com",   industry="Manufacturing", country="Germany"),
        Organization(id=ORG_EY,      name="EY Germany",      key="EYG", type=OrganizationType.partner,
                     email="contact@ey.com",     industry="Consulting",  country="Germany"),
    ]:
        session.add(obj)

    await session.commit()

    # 3. Users
    for obj in [
        # Hypatos — internal
        User(id=USR_CSM,     organization_id=ORG_HYPATOS, type=UserType.internal, subtype_id=SUB_CSM,
             role=UserRole.admin,   first_name="Max",     last_name="Müller",
             email="max.mueller@hypatos.ai",    phone="+49 30 1234 5670"),
        User(id=USR_SA_INT,  organization_id=ORG_HYPATOS, type=UserType.internal, subtype_id=SUB_SA,
             role=UserRole.enduser, first_name="Anna",    last_name="Schmidt",
             email="anna.schmidt@hypatos.ai",   phone="+49 30 1234 5671"),
        User(id=USR_PM_INT,  organization_id=ORG_HYPATOS, type=UserType.internal, subtype_id=SUB_PM,
             role=UserRole.enduser, first_name="Thomas",  last_name="Wagner",
             email="thomas.wagner@hypatos.ai",  phone="+49 30 1234 5672"),
        # Acme — customer
        User(id=USR_PM_CUST, organization_id=ORG_ACME, type=UserType.customer, subtype_id=SUB_PM,
             role=UserRole.enduser, first_name="Maria",  last_name="Bauer",
             email="maria.bauer@acme.com",      phone="+49 89 9876 5430"),
        User(id=USR_SPONSOR, organization_id=ORG_ACME, type=UserType.customer, subtype_id=SUB_SPONSOR,
             role=UserRole.admin,   first_name="Klaus",  last_name="Fischer",
             email="klaus.fischer@acme.com",    phone="+49 89 9876 5431"),
        # EY Germany — partner
        User(id=USR_COE,    organization_id=ORG_EY, type=UserType.partner, subtype_id=SUB_COE,
             role=UserRole.enduser, first_name="Sarah",   last_name="Schneider",
             email="sarah.schneider@ey.com",    phone="+49 69 7564 0001"),
        User(id=USR_SA_EY,  organization_id=ORG_EY, type=UserType.partner, subtype_id=SUB_SA,
             role=UserRole.enduser, first_name="Michael", last_name="Braun",
             email="michael.braun@ey.com",      phone="+49 69 7564 0002"),
        User(id=USR_PM_EY,  organization_id=ORG_EY, type=UserType.partner, subtype_id=SUB_PM,
             role=UserRole.enduser, first_name="Lisa",    last_name="Hofmann",
             email="lisa.hofmann@ey.com",       phone="+49 69 7564 0003"),
    ]:
        session.add(obj)

    # 4. Usecases
    for obj in [
        Usecase(id=UC_INVOICE,   name="Invoice Processing",           description="End-to-end automated processing of supplier invoices"),
        Usecase(id=UC_PO_CONF,   name="Purchase Order Confirmation",  description="Automated processing and matching of PO confirmations"),
        Usecase(id=UC_ORDER_MGT, name="Order Management",             description="Streamlined order creation and tracking"),
    ]:
        session.add(obj)

    # 5. Capability + Features
    session.add(Capability(id=CAP_CORE, contract="Core", name="Core Processing",
                           description="Core document processing capabilities"))
    for obj in [
        Feature(id=FEAT_DOC_EXT, capability_id=CAP_CORE, name="Document Extraction",
                service_description="AI-powered extraction of key data points from documents",
                deliverables="Extracted data in structured format (JSON/XML)",
                scope_type=ScopeType.standard, scoping_questionnaire=True,
                included_in_ootb=True, default_enabled=True, active=True, multiple_value=1),
        Feature(id=FEAT_DUP_CHK, capability_id=CAP_CORE, name="Duplicate Check",
                service_description="Detection of duplicate documents before processing",
                deliverables="Duplicate flagging and rejection workflow",
                scope_type=ScopeType.standard, scoping_questionnaire=False,
                included_in_ootb=True, default_enabled=True, active=True, multiple_value=1),
        Feature(id=FEAT_EINV, capability_id=CAP_CORE, name="E-Invoice Processing",
                service_description="Processing of electronic invoices in ZUGFeRD, XRechnung, and EDI formats",
                deliverables="Parsed e-invoice data integrated into the processing workflow",
                scope_type=ScopeType.standard, scoping_questionnaire=True,
                included_in_ootb=True, default_enabled=False, active=True, multiple_value=1),
        Feature(id=FEAT_MDE, capability_id=CAP_CORE, name="Master Data Enrichment",
                service_description="Automatic enrichment of extracted data with master data from ERP",
                deliverables="Enriched extraction output with resolved master data references",
                scope_type=ScopeType.non_standard, scoping_questionnaire=True,
                included_in_ootb=False, default_enabled=False, active=True, multiple_value=1),
    ]:
        session.add(obj)

    # 6. Countries (skip if alpha2_code already exists)
    for ctr_id, name, code in [(CTR_DE, "Germany", "DE"), (CTR_FR, "France", "FR"), (CTR_AT, "Austria", "AT")]:
        exists = (await session.execute(select(Country).where(Country.alpha2_code == code))).scalars().first()
        if not exists:
            session.add(Country(id=ctr_id, name=name, alpha2_code=code))

    # 7. Master success criteria
    for obj in [
        MasterSuccessCriterion(id=MSC_1, text="Achieve ≥ 90% straight-through processing rate for invoices"),
        MasterSuccessCriterion(id=MSC_2, text="Reduce average invoice processing time by at least 50%"),
        MasterSuccessCriterion(id=MSC_3, text="Eliminate 100% of duplicate invoice payments"),
    ]:
        session.add(obj)

    # 8. Master ERP systems
    for obj in [
        MasterERPSystem(id=MERP_SAP_ECC, name="SAP ECC"),
        MasterERPSystem(id=MERP_SAP_S4,  name="SAP S/4"),
        MasterERPSystem(id=MERP_COUPA,   name="Coupa"),
    ]:
        session.add(obj)

    await session.commit()

    # 9. Feature → Usecase links
    # All 4 features apply to Invoice Processing
    for feat_id in _ALL_FEAT_IDS:
        session.add(FeatureUsecase(feature_id=feat_id, usecase_id=UC_INVOICE))
    # Doc Extraction + Duplicate Check also apply to PO Confirmation
    for feat_id in [FEAT_DOC_EXT, FEAT_DUP_CHK]:
        session.add(FeatureUsecase(feature_id=feat_id, usecase_id=UC_PO_CONF))

    # 10. Demo project
    session.add(Project(
        id=PROJ_DEMO,
        name="Acme Industries x Hypatos",
        type=ProjectType.pilot,
        start_date=date(2025, 3, 1),
        customer_id=ORG_ACME,
        partner_id=ORG_EY,
        deal_winner_id=USR_PM_INT,
        default_duration_weeks=12,
        requires_integration=True,
        integration_type=IntegrationType.sap_addon,
        partner_budget_hours=200,
        internal_budget_hours=300,
        status=ProjectStatus.draft,
        primary_usecase_id=UC_INVOICE,
    ))

    await session.commit()

    # 11. Project stakeholders
    for user_id, role_label in [
        (USR_PM_INT,  "Project Manager (Hypatos)"),
        (USR_SA_INT,  "Solution Architect (Hypatos)"),
        (USR_CSM,     "Customer Success Manager"),
        (USR_PM_CUST, "Project Manager (Customer)"),
        (USR_SPONSOR, "Project Sponsor"),
        (USR_COE,     "COE (EY)"),
        (USR_SA_EY,   "Solution Architect (EY)"),
        (USR_PM_EY,   "Project Manager (EY)"),
    ]:
        session.add(ProjectStakeholder(project_id=PROJ_DEMO, user_id=user_id, role=role_label))

    # 12. Project → Usecase links
    for uc_id in _ALL_UC_IDS:
        session.add(ProjectUsecase(project_id=PROJ_DEMO, usecase_id=uc_id))

    await session.commit()

    return {
        "detail": (
            "Demo data seeded: 3 organisations · 8 users · 1 capability · 4 features · "
            "3 use cases · 3 countries · 3 success criteria · 3 ERP systems · 1 project"
        )
    }


# ── Clear ──────────────────────────────────────────────────────────────────────

@router.delete("/seed")
async def clear_demo(session: SessionDep):
    # 1. ProjectStakeholder links
    for user_id in _ALL_USER_IDS:
        link = await session.get(ProjectStakeholder, (PROJ_DEMO, user_id))
        if link:
            await session.delete(link)
    await session.commit()

    # 2. ProjectUsecase links
    for uc_id in _ALL_UC_IDS:
        link = await session.get(ProjectUsecase, (PROJ_DEMO, uc_id))
        if link:
            await session.delete(link)
    await session.commit()

    # 3. FeatureUsecase links (bulk delete)
    await session.execute(
        sql_delete(FeatureUsecase).where(FeatureUsecase.feature_id.in_(_ALL_FEAT_IDS))
    )
    await session.commit()

    # 4. Project
    proj = await session.get(Project, PROJ_DEMO)
    if proj:
        await session.delete(proj)
    await session.commit()

    # 5. Usecases
    for uc_id in _ALL_UC_IDS:
        obj = await session.get(Usecase, uc_id)
        if obj:
            await session.delete(obj)
    await session.commit()

    # 6. Features
    for feat_id in _ALL_FEAT_IDS:
        obj = await session.get(Feature, feat_id)
        if obj:
            await session.delete(obj)
    await session.commit()

    # 7. Capability
    obj = await session.get(Capability, CAP_CORE)
    if obj:
        await session.delete(obj)
    await session.commit()

    # 8. Users (before orgs)
    for user_id in _ALL_USER_IDS:
        obj = await session.get(User, user_id)
        if obj:
            await session.delete(obj)
    await session.commit()

    # 9. Organizations (cascade handles remaining erp_systems etc.)
    for org_id in _ALL_ORG_IDS:
        obj = await session.get(Organization, org_id)
        if obj:
            await session.delete(obj)
    await session.commit()

    # 10. Subtypes
    for sub_id in _ALL_SUB_IDS:
        obj = await session.get(Subtype, sub_id)
        if obj:
            await session.delete(obj)
    await session.commit()

    # 11. Countries (only those created by demo seed)
    for ctr_id in _ALL_CTR_IDS:
        obj = await session.get(Country, ctr_id)
        if obj:
            await session.delete(obj)
    await session.commit()

    # 12. Master data
    for msc_id in _ALL_MSC_IDS:
        obj = await session.get(MasterSuccessCriterion, msc_id)
        if obj:
            await session.delete(obj)
    for merp_id in _ALL_MERP_IDS:
        obj = await session.get(MasterERPSystem, merp_id)
        if obj:
            await session.delete(obj)
    await session.commit()

    return {"detail": "Demo data cleared successfully."}
