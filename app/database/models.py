from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Numeric, String
from sqlalchemy.dialects import postgresql
from enum import Enum
from datetime import datetime, date
from decimal import Decimal
from pydantic import EmailStr
from uuid import uuid4, UUID
from typing import Optional


# ===================== Enums =====================


class OrganizationType(str, Enum):
    customer = "customer"
    partner = "partner"
    internal = "internal"


class UserType(str, Enum):
    partner = "partner"
    customer = "customer"
    internal = "internal"


class UserRole(str, Enum):
    admin = "admin"
    enduser = "enduser"


class SubtypeName(str, Enum):
    project_manager = "project_manager"
    business_analyst = "business_analyst"
    accountant = "accountant"
    integration_expert = "integration_expert"
    accounts_payable_lead = "accounts_payable_lead"
    business_lead = "business_lead"
    project_lead = "project_lead"
    clerk = "clerk"
    coe = "coe"
    solution_architect = "solution_architect"
    project_sponsor = "project_sponsor"
    project_champion = "project_champion"
    sap_basis = "sap_basis"
    technical_lead = "technical_lead"
    customer_success_manager = "customer_success_manager"
    head_of_professional_service = "head_of_professional_service"
    account_executive = "account_executive"  # 🆕 Required for AE stakeholder



    

class ProjectType(str, Enum):
    pilot = "pilot"
    poc = "poc"
    custom_demo = "custom_demo"
    rollout = "rollout"


class ProjectStatus(str, Enum): # NEW ENUM
    draft = "draft"
    completed = "completed"
    archived = "archived"


class IntegrationType(str, Enum):
    none = "none"
    sap_addon = "sap_addon"
    sap_cloud_connector = "sap_cloud_connector"
    coupa_connector = "coupa_connector"
    boomi = "boomi"
    custom_middleware = "custom_middleware"


class ScopeType(str, Enum):
    standard = "standard"
    non_standard = "non_standard"


class TeamType(str, Enum):
    service_team = "service_team"
    enablement_team = "enablement_team"
    customer = "customer"


class DocumentTemplateType(str, Enum):
    sow = "sow"
    success_contract = "success_contract"
    solution_design = "solution_design"
    email = "email"
    other = "other"


class DocumentStatus(str, Enum):
    draft = "draft"
    final = "final"
    archived = "archived"


class ERPType(str, Enum):
    sap = "sap"
    coupa = "coupa"
    oracle = "oracle"
    other = "other"


class CredentialType(str, Enum):
    keycloak = "keycloak"
    other = "other"


# ===================== Link Models (Many-to-Many) =====================


class UserLanguage(SQLModel, table=True):
    __tablename__ = "user_language"

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    language_id: UUID = Field(foreign_key="language.id", primary_key=True)


class UserSkill(SQLModel, table=True):
    __tablename__ = "user_skill"

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    skill_id: UUID = Field(foreign_key="skill.id", primary_key=True)


class ProjectStakeholder(SQLModel, table=True):
    __tablename__ = "project_stakeholder"

    project_id: UUID = Field(foreign_key="project.id", primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    role: Optional[str] = Field(default=None)


class ProjectUsecase(SQLModel, table=True): # NEW LINK MODEL
    __tablename__ = "project_usecase"

    project_id: UUID = Field(foreign_key="project.id", primary_key=True)
    usecase_id: UUID = Field(foreign_key="usecase.id", primary_key=True)


class FeatureUsecase(SQLModel, table=True):
    __tablename__ = "feature_usecase"

    feature_id: UUID = Field(foreign_key="feature.id", primary_key=True)
    usecase_id: UUID = Field(foreign_key="usecase.id", primary_key=True)


class ProjectFeature(SQLModel, table=True):
    """Custom features attached directly to a single project, independent of
    use cases. Lets a customer-specific feature be scoped to one project
    without auto-applying to every project that selects the same use case."""
    __tablename__ = "project_feature"

    project_id: UUID = Field(foreign_key="project.id", primary_key=True)
    feature_id: UUID = Field(foreign_key="feature.id", primary_key=True)


class UserTeamsGroup(SQLModel, table=True):
    __tablename__ = "user_teams_group"

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    teams_group_id: UUID = Field(
        foreign_key="organization_teams_group.id", primary_key=True
    )


class UserSlackChannel(SQLModel, table=True):
    __tablename__ = "user_slack_channel"

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    slack_channel_id: UUID = Field(
        foreign_key="organization_slack_channel.id", primary_key=True
    )


class UserMetabaseGroup(SQLModel, table=True):
    __tablename__ = "user_metabase_group"

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    metabase_group_id: UUID = Field(
        foreign_key="organization_metabase_group.id", primary_key=True
    )


class UserHyStudioCompany(SQLModel, table=True):
    __tablename__ = "user_hystudio_company"

    user_id: UUID = Field(foreign_key="user.id", primary_key=True)
    hystudio_company_id: UUID = Field(
        foreign_key="organization_hystudio_company.id", primary_key=True
    )


class HyStudioCompanyProject(SQLModel, table=True):
    __tablename__ = "hystudio_company_project"

    hystudio_company_id: UUID = Field(
        foreign_key="organization_hystudio_company.id", primary_key=True
    )
    project_id: UUID = Field(foreign_key="project.id", primary_key=True)


# ===================== Main Models =====================




class Organization(SQLModel, table=True):
    __tablename__ = "organization"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    name: str
    key: Optional[str] = Field(
        default=None,
        sa_column=Column(String(7), nullable=True, unique=True, index=True),
    )
    type: OrganizationType
    email: EmailStr
    industry: str
    country: str
    regions_operation: Optional[str] = Field(default=None)
    number_subsidiaries: Optional[str] = Field(default=None)
    company_overview: Optional[str] = Field(default=None)
    languages: Optional[str] = Field(default=None)  # comma-separated

    # CSM & Account
    csm_id: Optional[UUID] = Field(sa_column=Column(postgresql.UUID, nullable=True, default=None))
    account_executive_id: Optional[UUID] = Field(sa_column=Column(postgresql.UUID, nullable=True, default=None))
    sales_representative_id: Optional[UUID] = Field(sa_column=Column(postgresql.UUID, nullable=True, default=None))
    account_status: Optional[str] = Field(default=None)  # onboarding / live
    health_score_question_id: Optional[str] = Field(default=None)  # future Metabase hook

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    users: list["User"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    projects: list["Project"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan", "foreign_keys": "[Project.customer_id]"},
    )
    teams_groups: list["OrganizationTeamsGroup"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    slack_channels: list["OrganizationSlackChannel"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    jira_projects: list["OrganizationJiraProject"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    metabase_groups: list["OrganizationMetabaseGroup"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    hystudio_companies: list["OrganizationHyStudioCompany"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    erp_systems: list["ERPSystem"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )



class Subtype(SQLModel, table=True):
    __tablename__ = "subtype"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    name: str
    description: Optional[str] = Field(default=None)

    users: list["User"] = Relationship(
        back_populates="subtype",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Language(SQLModel, table=True):
    __tablename__ = "language"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    code: str
    name: str

    users: list["User"] = Relationship(
        back_populates="languages",
        link_model=UserLanguage,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Skill(SQLModel, table=True):
    __tablename__ = "skill"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    name: str
    category: Optional[str] = Field(default=None)

    users: list["User"] = Relationship(
        back_populates="skills",
        link_model=UserSkill,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    organization_id: UUID = Field(foreign_key="organization.id")
    type: UserType
    subtype_id: UUID = Field(foreign_key="subtype.id")
    role: UserRole
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    metabase_user_id: Optional[int] = Field(default=None)   # cached Metabase internal user ID
    teams_user_id: Optional[str] = Field(default=None)      # Azure AD object ID (cached after first provisioning)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    subtype: Subtype = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    languages: list[Language] = Relationship(
        back_populates="users",
        link_model=UserLanguage,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    skills: list[Skill] = Relationship(
        back_populates="users",
        link_model=UserSkill,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    won_projects: list["Project"] = Relationship(
        back_populates="deal_winner",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    owned_features: list["Feature"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    created_templates: list["DocumentTemplate"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    projects: list["Project"] = Relationship(
        back_populates="stakeholders",
        link_model=ProjectStakeholder,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    teams_groups: list["OrganizationTeamsGroup"] = Relationship(
        back_populates="users",
        link_model=UserTeamsGroup,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    slack_channels: list["OrganizationSlackChannel"] = Relationship(
        back_populates="users",
        link_model=UserSlackChannel,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    metabase_groups: list["OrganizationMetabaseGroup"] = Relationship(
        back_populates="users",
        link_model=UserMetabaseGroup,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    hystudio_companies: list["OrganizationHyStudioCompany"] = Relationship(
        back_populates="users",
        link_model=UserHyStudioCompany,
        sa_relationship_kwargs={"lazy": "selectin"},
    )




class Project(SQLModel, table=True):
    __tablename__ = "project"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    name: str
    type: ProjectType
    start_date: date
    customer_id: UUID = Field(foreign_key="organization.id")
    partner_id: Optional[UUID] = Field(default=None, foreign_key="organization.id")
    deal_winner_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    default_duration_weeks: int
    requires_integration: bool
    integration_type: IntegrationType
    partner_budget_hours: int = Field(default=0)
    internal_budget_hours: int = Field(default=0)
    
    # --- NEW FIELDS ---
    status: ProjectStatus = ProjectStatus.draft
    primary_usecase_id: Optional[UUID] = Field(default=None, foreign_key="usecase.id")

    # Technical Integration
    target_erp: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    sap_addon_concerns: Optional[str] = None
    current_workflow: Optional[str] = None
    existing_services: Optional[str] = None
    document_receipt_channels: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    data_points_current: Optional[str] = None

    # Document Processing Discovery
    users_work_in_studio: Optional[str] = None
    supplier_guidelines: Optional[str] = None
    other_processing_guidelines: Optional[str] = None
    multi_invoice_documents: Optional[str] = None
    multi_invoice_share: Optional[int] = None
    file_formats_received: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    poor_quality_scans: Optional[str] = None
    document_submission_channels: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    expected_doc_types_in_channels: Optional[str] = None
    out_of_scope_handling: Optional[str] = None

    # Email Processing
    email_content_downstream: Optional[str] = None
    eml_archiving: Optional[str] = None
    inbound_email_rules: Optional[str] = None
    email_routing: Optional[str] = None

    # Classification & Matching
    document_classification_method: Optional[str] = None
    statements_classification: Optional[str] = None
    statements_downstream: Optional[str] = None
    leases_recurring_handling: Optional[str] = None
    po_nonpo_identification: Optional[str] = None
    po_nonpo_distribution: Optional[str] = None
    rejection_classification: Optional[str] = None
    rejection_timing: Optional[str] = None
    rejection_communication: Optional[str] = None
    standardized_rejection_messages: Optional[str] = None
    bounced_rejections_handling: Optional[str] = None

    # Master Data & Verification
    verification_team_structure: Optional[str] = None
    routing_criteria: Optional[str] = None
    master_data_assignment: Optional[str] = None
    missing_master_data_handling: Optional[str] = None
    duplicate_master_data: Optional[str] = None

    # PO Matching & Processing
    delivery_note_extraction: Optional[str] = None
    po_types_common: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    po_vs_invoice_values: Optional[str] = None
    po_deviation_handling: Optional[str] = None
    missing_po_number: Optional[str] = None
    non_matched_po_processing: Optional[str] = None

    # Accounting Coding & GL
    custom_gl_logic: Optional[str] = None
    mandatory_posting_attributes: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    accounting_templates_usage: Optional[str] = None
    gl_costcenter_assignment: Optional[str] = None
    reviewer_approver_derivation: Optional[str] = None
    
    # 📊 Volume & Performance Metrics
    annual_doc_volume_per_usecase: Optional[int] = Field(default=0)
    e2e_cost_per_doc: Optional[Decimal] = Field(default=0, sa_column=Column(Numeric))
    e2e_processing_time_mins: Optional[int] = Field(default=0)
    automation_improvement_percentage: Optional[int] = Field(default=0)
    approx_supplier_customer_count: Optional[int] = Field(default=0)

    # KPIs & Success Measurement
    current_kpis: Optional[str] = None
    verification_team_kpis: Optional[str] = None
    special_document_handling: Optional[str] = None
    custom_answers: dict = Field(sa_column=Column(postgresql.JSONB), default_factory=dict)

    # --- Generated Document Paths ---
    # sow_markdown_path: Optional[str] = None
    # sow_docx_path: Optional[str] = None
    # success_contract_path: Optional[str] = None
    # solution_design_path: Optional[str] = None
    
    # 🆕 REQUIRED FOR DOCUMENT GENERATION:
    go_live_date: Optional[date] = None
    go_live_regions: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    rollout_regions: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    project_background: Optional[str] = None
    main_objectives: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    top_three_pain_points: Optional[str] = None
    language_constraints: Optional[str] = None
    project_risks: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    overall_accuracy_target: Optional[int] = None
    success_criteria: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    success_criteria_custom: Optional[str] = None
    document_types: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: Organization = Relationship(
        back_populates="projects",
        sa_relationship_kwargs={"lazy": "selectin", "foreign_keys": "[Project.customer_id]"},
    )
    partner: Optional[Organization] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin", "foreign_keys": "[Project.partner_id]"},
    )
    deal_winner: User = Relationship(
        back_populates="won_projects",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    stakeholders: list[User] = Relationship(
        back_populates="projects",
        link_model=ProjectStakeholder,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    linked_usecases: list["Usecase"] = Relationship(
        back_populates="projects",
        link_model=ProjectUsecase,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    custom_features: list["Feature"] = Relationship(
        link_model=ProjectFeature,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    primary_usecase: Optional["Usecase"] = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    generated_documents: list["GeneratedDocument"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    erp_connectors: list["ERPConnector"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    hystudio_companies: list["OrganizationHyStudioCompany"] = Relationship(
        back_populates="projects",
        link_model=HyStudioCompanyProject,
        sa_relationship_kwargs={"lazy": "selectin"},
    )




class Capability(SQLModel, table=True):
    __tablename__ = "capability"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    contract: str
    name: str
    description: Optional[str] = Field(default=None)

    features: list["Feature"] = Relationship(
        back_populates="capability",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Feature(SQLModel, table=True):
    __tablename__ = "feature"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    capability_id: UUID = Field(foreign_key="capability.id")
    name: str
    service_description: str
    deliverables: str
    scope_type: ScopeType
    owner_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    scoping_questionnaire: bool
    reference_documentation: Optional[str] = Field(default=None)
    included_in_ootb: bool
    default_enabled: bool
    active: bool
    multiple_value: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    
    # 🆕 Required for Solution Design Document tables
    requirements: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    # Structure: [{"requirement": "...", "description": "...", "solution": "..."}]

    capability: Capability = Relationship(
        back_populates="features",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    owner: User = Relationship(
        back_populates="owned_features",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    scope_specifications: list["ScopeSpecification"] = Relationship(
        back_populates="feature",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    cost_drivers: list["CostDriver"] = Relationship(
        back_populates="feature",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    feature_efforts: list["FeatureEffort"] = Relationship(
        back_populates="feature",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    usecases: list["Usecase"] = Relationship(
        back_populates="features",
        link_model=FeatureUsecase,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class ScopeSpecification(SQLModel, table=True):
    __tablename__ = "scope_specification"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    feature_id: UUID = Field(foreign_key="feature.id")
    name: str
    order: Optional[int] = Field(default=None)

    feature: Feature = Relationship(
        back_populates="scope_specifications",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class CostDriver(SQLModel, table=True):
    __tablename__ = "cost_driver"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    feature_id: UUID = Field(foreign_key="feature.id")
    driver_name: str
    description: Optional[str] = Field(default=None)
    unit: str

    feature: Feature = Relationship(
        back_populates="cost_drivers",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class FeatureEffort(SQLModel, table=True):
    __tablename__ = "feature_effort"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    feature_id: UUID = Field(foreign_key="feature.id")
    team_type: TeamType
    unit_effort_pd: Decimal = Field(sa_column=Column(Numeric))
    total_effort_pd: Decimal = Field(sa_column=Column(Numeric))
    in_scope: bool
    comments: Optional[str] = Field(default=None)

    feature: Feature = Relationship(
        back_populates="feature_efforts",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Usecase(SQLModel, table=True):
    __tablename__ = "usecase"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    name: str
    description: Optional[str] = Field(default=None)

    features: list[Feature] = Relationship(
        back_populates="usecases",
        link_model=FeatureUsecase,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    # NEW RELATIONSHIP
    projects: list["Project"] = Relationship(
        back_populates="linked_usecases",
        link_model=ProjectUsecase,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class DocumentTemplate(SQLModel, table=True):
    __tablename__ = "document_template"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    name: str
    type: DocumentTemplateType
    markdown_content: str
    variables: list = Field(sa_column=Column(postgresql.JSONB))
    version: float = 1.0
    is_active: bool


    # 🆕 File Format and Path
    file_format: str = "md"  # "md" or "docx"
    # file_path: Optional[str] = None

    created_by_id: Optional[UUID] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    created_by: User = Relationship(
        back_populates="created_templates",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    generated_documents: list["GeneratedDocument"] = Relationship(
        back_populates="template",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class GeneratedDocument(SQLModel, table=True):
    """One row per generation — the version ledger for generated documents.

    Generating a document never overwrites history: each run appends a new row
    with the next version_no for that (project, template) pair. The rendered
    markdown is stored alongside the on-disk file path so a version can be
    inspected without reading from disk."""
    __tablename__ = "generated_document"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    project_id: UUID = Field(foreign_key="project.id")
    template_id: UUID = Field(foreign_key="document_template.id")
    version_no: int = Field(default=1, index=True)   # 1-based, per project+template
    document_type: str
    markdown_generated: str
    file_path: str                                   # absolute path on disk
    file_format: str = Field(default="md")           # "md" or "docx"
    template_version: Optional[float] = Field(default=None)  # template version at generation time
    status: DocumentStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    project: Project = Relationship(
        back_populates="generated_documents",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    template: DocumentTemplate = Relationship(
        back_populates="generated_documents",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class OrganizationTeamsGroup(SQLModel, table=True):
    __tablename__ = "organization_teams_group"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    organization_id: UUID = Field(foreign_key="organization.id")
    external_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sharepoint_copied_at: Optional[datetime] = Field(default=None)  # set when template folder is copied

    organization: Organization = Relationship(
        back_populates="teams_groups",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    users: list[User] = Relationship(
        back_populates="teams_groups",
        link_model=UserTeamsGroup,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class OrganizationSlackChannel(SQLModel, table=True):
    __tablename__ = "organization_slack_channel"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    organization_id: UUID = Field(foreign_key="organization.id")
    external_id: str        # Slack channel ID (C01234ABCDE)
    channel_name: str       # human-readable Slack channel name
    channel_type: str = Field(default="client")  # "client" or "ext_partner"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization = Relationship(
        back_populates="slack_channels",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    users: list[User] = Relationship(
        back_populates="slack_channels",
        link_model=UserSlackChannel,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class OrganizationJiraProject(SQLModel, table=True):
    __tablename__ = "organization_jira_project"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    organization_id: UUID = Field(foreign_key="organization.id")
    project_key:  str              # e.g. "FNK"  (Jira project key)
    project_id:   str              # Jira internal numeric ID
    project_name: str              # display name
    board_url:    str              # https://…/jira/core/projects/{KEY}/board
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization = Relationship(
        back_populates="jira_projects",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class JiraLeadUser(SQLModel, table=True):
    """Global list of Jira users eligible to be project leads.
    Managed via the admin panel in the integrations page."""
    __tablename__ = "jira_lead_user"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    username: str = Field(unique=True, index=True)   # human-readable key, e.g. "stephan.kuche"
    jira_account_id: str                              # Atlassian account ID
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationMetabaseGroup(SQLModel, table=True):
    __tablename__ = "organization_metabase_group"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    organization_id: UUID = Field(foreign_key="organization.id")
    external_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization = Relationship(
        back_populates="metabase_groups",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    users: list[User] = Relationship(
        back_populates="metabase_groups",
        link_model=UserMetabaseGroup,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class OrganizationHyStudioCompany(SQLModel, table=True):
    __tablename__ = "organization_hystudio_company"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    organization_id: UUID = Field(foreign_key="organization.id")
    external_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization = Relationship(
        back_populates="hystudio_companies",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    users: list[User] = Relationship(
        back_populates="hystudio_companies",
        link_model=UserHyStudioCompany,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    projects: list[Project] = Relationship(
        back_populates="hystudio_companies",
        link_model=HyStudioCompanyProject,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    api_credentials: list["APICredential"] = Relationship(
        back_populates="hystudio_company",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class ERPSystem(SQLModel, table=True):
    __tablename__ = "erp_system"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    organization_id: UUID = Field(foreign_key="organization.id")
    type: ERPType
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    organization: Organization = Relationship(
        back_populates="erp_systems",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    erp_connectors: list["ERPConnector"] = Relationship(
        back_populates="erp_system",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class ERPConnector(SQLModel, table=True):
    __tablename__ = "erp_connector"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    project_id: UUID = Field(foreign_key="project.id")
    erp_system_id: UUID = Field(foreign_key="erp_system.id")
    connector_version: str
    contact_first_name: str
    contact_last_name: str
    contact_email: EmailStr
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    project: Project = Relationship(
        back_populates="erp_connectors",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    erp_system: ERPSystem = Relationship(
        back_populates="erp_connectors",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class APICredential(SQLModel, table=True):
    __tablename__ = "api_credential"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    hystudio_company_id: UUID = Field(
        foreign_key="organization_hystudio_company.id"
    )
    credential_type: CredentialType
    secret_reference: str
    scopes: list = Field(sa_column=Column(postgresql.JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    hystudio_company: OrganizationHyStudioCompany = Relationship(
        back_populates="api_credentials",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class DocumentationLink(SQLModel, table=True):
    __tablename__ = "documentation_link"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    title: str
    url: str
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Project Master Data ───────────────────────────────────────────────────────

class Country(SQLModel, table=True):
    __tablename__ = "country"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    name: str = Field(index=True)
    alpha2_code: str = Field(max_length=2, sa_column=Column(String(2), unique=True, index=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MasterObjective(SQLModel, table=True):
    __tablename__ = "master_objective"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MasterSuccessCriterion(SQLModel, table=True):
    __tablename__ = "master_success_criterion"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MasterProjectRisk(SQLModel, table=True):
    __tablename__ = "master_project_risk"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MasterERPSystem(SQLModel, table=True):
    __tablename__ = "master_erp_system"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CustomSection(SQLModel, table=True):
    __tablename__ = "custom_section"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    name: str
    order: int = Field(default=0)
    use_case_id: Optional[UUID] = Field(sa_column=Column(postgresql.UUID, nullable=True, default=None))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CustomQuestion(SQLModel, table=True):
    __tablename__ = "custom_question"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    section_id: UUID = Field(sa_column=Column(postgresql.UUID, nullable=False))
    label: str
    type: str = Field(default="text")  # text | textarea | number | select
    options: list = Field(sa_column=Column(postgresql.JSONB), default_factory=list)
    required: bool = Field(default=False)
    order: int = Field(default=0)
    help_text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AccountHealth(SQLModel, table=True):
    __tablename__ = "account_health"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    org_id: UUID = Field(sa_column=Column(postgresql.UUID, nullable=False))
    status: str  # green / yellow / red / churned
    comment: Optional[str] = None
    created_by_id: Optional[UUID] = Field(sa_column=Column(postgresql.UUID, nullable=True, default=None))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Contract(SQLModel, table=True):
    __tablename__ = "contract"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    org_id: UUID = Field(sa_column=Column(postgresql.UUID, nullable=False))
    project_id: Optional[UUID] = Field(sa_column=Column(postgresql.UUID, nullable=True, default=None))
    name: str
    type: str = Field(default="MSA")       # MSA / SOW / Amendment / Renewal / NDA / Other
    status: str = Field(default="active")  # active / expired / pending / cancelled
    url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    paid: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SmtpConfig(SQLModel, table=True):
    """Singleton table — always exactly one row (id=1)."""
    __tablename__ = "smtp_config"

    id: int = Field(default=1, primary_key=True)
    host: Optional[str] = Field(default=None)
    port: int = Field(default=587)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    from_name: Optional[str] = Field(default="hyOps")
    from_email: Optional[str] = Field(default=None)
    use_tls: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IntegrationCredential(SQLModel, table=True):
    """Key/value store for integration credentials, managed from the admin
    Credentials page. The key matches the corresponding .env variable name
    (e.g. SLACK_BOT_TOKEN). Values stored here overlay `integration_settings`
    at startup, so the DB takes precedence over the .env file."""
    __tablename__ = "integration_credential"

    key: str = Field(primary_key=True)
    value: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StudioCluster(SQLModel, table=True):
    """A Hypatos Studio cluster's OAuth credentials. Studio runs on multiple
    clusters (e.g. EU / US), so credentials are stored as a list rather than as
    single env values. Adapters resolve a cluster by name (or the default)."""
    __tablename__ = "studio_cluster"

    id: UUID = Field(sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True))
    name: str = Field(index=True)                 # human label, e.g. "EU", "US"
    base_url: str
    client_id: str
    client_secret: str
    is_default: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
