from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import Numeric
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


class ProjectType(str, Enum):
    pilot = "pilot"
    poc = "poc"
    custom_demo = "custom_demo"
    rollout = "rollout"


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


class FeatureUsecase(SQLModel, table=True):
    __tablename__ = "feature_usecase"

    feature_id: UUID = Field(foreign_key="feature.id", primary_key=True)
    usecase_id: UUID = Field(foreign_key="usecase.id", primary_key=True)


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
    type: OrganizationType
    email: EmailStr
    industry: str
    country: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    users: list["User"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    projects: list["Project"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    teams_groups: list["OrganizationTeamsGroup"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    slack_channels: list["OrganizationSlackChannel"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    metabase_groups: list["OrganizationMetabaseGroup"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    hystudio_companies: list["OrganizationHyStudioCompany"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    erp_systems: list["ERPSystem"] = Relationship(
        back_populates="organization",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Subtype(SQLModel, table=True):
    __tablename__ = "subtype"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    name: SubtypeName
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
    deal_winner_id: UUID = Field(foreign_key="user.id")
    default_duration_weeks: int
    requires_integration: bool
    integration_type: IntegrationType
    partner_budget_hours: Decimal = Field(sa_column=Column(Numeric))
    internal_budget_hours: Decimal = Field(sa_column=Column(Numeric))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    customer: Organization = Relationship(
        back_populates="projects",
        sa_relationship_kwargs={"lazy": "selectin"},
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
    requirement_description: str
    solution_description: str
    deliverables: str
    scope_type: ScopeType
    owner_id: UUID = Field(foreign_key="user.id")
    scoping_questionnaire: bool
    reference_documentation: Optional[str] = Field(default=None)
    included_in_ootb: bool
    default_enabled: bool
    active: bool
    multiple_value: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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


class DocumentTemplate(SQLModel, table=True):
    __tablename__ = "document_template"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    name: str
    type: DocumentTemplateType
    markdown_content: str
    variables: list = Field(sa_column=Column(postgresql.JSONB))
    version: int
    is_active: bool
    created_by_id: UUID = Field(foreign_key="user.id")
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
    __tablename__ = "generated_document"

    id: UUID = Field(
        sa_column=Column(postgresql.UUID, default=uuid4, primary_key=True)
    )
    project_id: UUID = Field(foreign_key="project.id")
    template_id: UUID = Field(foreign_key="document_template.id")
    document_type: str
    markdown_generated: str
    docx_file_url: str
    pdf_file_url: str
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
    external_id: str
    channel_name: str
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