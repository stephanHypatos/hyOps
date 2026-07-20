from app.database.models import ProjectType, IntegrationType, ProjectStatus
from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import Optional
from datetime import datetime, date


# ===================== Nested JSONB Schemas =====================

class DocumentTypeItem(BaseModel):
    """Structure for document_types JSONB array items"""
    document_name: str
    accuracy_target: int = 95


# ===================== Project Schemas =====================

class ProjectBase(BaseModel):
    # Core Info
    name: str
    type: ProjectType
    start_date: date
    customer_id: UUID
    partner_id: Optional[UUID] = None
    deal_winner_id: UUID
    default_duration_weeks: int
    requires_integration: bool
    integration_type: IntegrationType
    partner_budget_hours: int = 0
    internal_budget_hours: int = 0
    
    # Core Status
    status: ProjectStatus = ProjectStatus.draft
    primary_usecase_id: Optional[UUID] = None

    # Project Details & Objectives
    go_live_date: Optional[date] = None
    go_live_regions: list[str] = []
    rollout_regions: list[str] = []
    project_background: Optional[str] = None
    main_objectives: list[str] = []
    top_three_pain_points: Optional[str] = None
    language_constraints: Optional[str] = None
    project_risks: list[str] = []
    overall_accuracy_target: Optional[int] = None

    # Success Criteria & Document Types
    success_criteria: list[str] = []
    success_criteria_custom: Optional[str] = None
    document_types: list[DocumentTypeItem] = []

    # Volume & Performance Metrics
    annual_doc_volume_per_usecase: Optional[int] = None
    e2e_cost_per_doc: Optional[float] = None
    e2e_processing_time_mins: Optional[int] = None
    automation_improvement_percentage: Optional[int] = None
    approx_supplier_customer_count: Optional[int] = None

    # Technical Integration
    target_erp: list[str] = []
    sap_addon_concerns: Optional[str] = None
    current_workflow: Optional[str] = None
    existing_services: Optional[str] = None
    document_receipt_channels: list[str] = []
    data_points_current: Optional[str] = None

    # Document Processing Discovery
    users_work_in_studio: Optional[str] = None
    supplier_guidelines: Optional[str] = None
    other_processing_guidelines: Optional[str] = None
    multi_invoice_documents: Optional[str] = None
    multi_invoice_share: Optional[int] = None
    file_formats_received: list[str] = []
    poor_quality_scans: Optional[str] = None
    document_submission_channels: list[str] = []
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
    po_types_common: list[str] = []
    po_vs_invoice_values: Optional[str] = None
    po_deviation_handling: Optional[str] = None
    missing_po_number: Optional[str] = None
    non_matched_po_processing: Optional[str] = None

    # Accounting Coding & GL
    custom_gl_logic: Optional[str] = None
    mandatory_posting_attributes: list[str] = []
    accounting_templates_usage: Optional[str] = None
    gl_costcenter_assignment: Optional[str] = None
    reviewer_approver_derivation: Optional[str] = None

    # KPIs & Success Measurement
    current_kpis: Optional[str] = None
    verification_team_kpis: Optional[str] = None
    special_document_handling: Optional[str] = None
    custom_answers: dict = {}

    # Document Paths
    sow_markdown_path: Optional[str] = None
    sow_docx_path: Optional[str] = None
    success_contract_path: Optional[str] = None
    solution_design_path: Optional[str] = None

    # 🆕 Validators: Convert ISO date strings to Python date objects
    @field_validator('start_date', 'go_live_date', mode='before')
    @classmethod
    def parse_date_strings(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError(f'Invalid date format: {v}. Expected YYYY-MM-DD')
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    """Make every single field Optional for PATCH updates"""
    name: Optional[str] = None
    type: Optional[ProjectType] = None
    start_date: Optional[date] = None
    customer_id: Optional[UUID] = None
    partner_id: Optional[UUID] = None
    deal_winner_id: Optional[UUID] = None
    default_duration_weeks: Optional[int] = None
    requires_integration: Optional[bool] = None
    integration_type: Optional[IntegrationType] = None
    partner_budget_hours: Optional[int] = None
    internal_budget_hours: Optional[int] = None
    
    status: Optional[ProjectStatus] = None
    primary_usecase_id: Optional[UUID] = None

    # Project Details & Objectives
    go_live_date: Optional[date] = None
    go_live_regions: Optional[list[str]] = None
    rollout_regions: Optional[list[str]] = None
    project_background: Optional[str] = None
    main_objectives: Optional[list[str]] = None
    top_three_pain_points: Optional[str] = None
    language_constraints: Optional[str] = None
    project_risks: Optional[list[str]] = None
    overall_accuracy_target: Optional[int] = None

    # Success Criteria & Document Types
    success_criteria: Optional[list[str]] = None
    success_criteria_custom: Optional[str] = None
    document_types: Optional[list[DocumentTypeItem]] = None

    # Volume & Performance Metrics
    annual_doc_volume_per_usecase: Optional[int] = None
    e2e_cost_per_doc: Optional[float] = None
    e2e_processing_time_mins: Optional[int] = None
    automation_improvement_percentage: Optional[int] = None
    approx_supplier_customer_count: Optional[int] = None

    # Technical Integration
    target_erp: Optional[list[str]] = None
    sap_addon_concerns: Optional[str] = None
    current_workflow: Optional[str] = None
    existing_services: Optional[str] = None
    document_receipt_channels: Optional[list[str]] = None
    data_points_current: Optional[str] = None

    # Document Processing Discovery
    users_work_in_studio: Optional[str] = None
    supplier_guidelines: Optional[str] = None
    other_processing_guidelines: Optional[str] = None
    multi_invoice_documents: Optional[str] = None
    multi_invoice_share: Optional[int] = None
    file_formats_received: Optional[list[str]] = None
    poor_quality_scans: Optional[str] = None
    document_submission_channels: Optional[list[str]] = None
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
    po_types_common: Optional[list[str]] = None
    po_vs_invoice_values: Optional[str] = None
    po_deviation_handling: Optional[str] = None
    missing_po_number: Optional[str] = None
    non_matched_po_processing: Optional[str] = None

    # Accounting Coding & GL
    custom_gl_logic: Optional[str] = None
    mandatory_posting_attributes: Optional[list[str]] = None
    accounting_templates_usage: Optional[str] = None
    gl_costcenter_assignment: Optional[str] = None
    reviewer_approver_derivation: Optional[str] = None

    # KPIs & Success Measurement
    current_kpis: Optional[str] = None
    verification_team_kpis: Optional[str] = None
    special_document_handling: Optional[str] = None
    custom_answers: Optional[dict] = None

    # Document Paths
    sow_markdown_path: Optional[str] = None
    sow_docx_path: Optional[str] = None
    success_contract_path: Optional[str] = None
    solution_design_path: Optional[str] = None

    # 🆕 Validators: Convert ISO date strings to Python date objects
    @field_validator('start_date', 'go_live_date', mode='before')
    @classmethod
    def parse_date_strings(cls, v):
        if v is None or v == '':
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                return date.fromisoformat(v)
            except ValueError:
                raise ValueError(f'Invalid date format: {v}. Expected YYYY-MM-DD')
        return v


class ProjectRead(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


# ===================== Stakeholder M2M Schemas =====================

class StakeholderAssign(BaseModel):
    user_id: UUID
    role: str

class StakeholderRead(BaseModel):
    project_id: UUID
    user_id: UUID
    role: Optional[str] = None

class StakeholderReadEnriched(BaseModel):
    project_id: UUID
    user_id: UUID
    role: Optional[str] = None
    first_name: str
    last_name: str
    email: str


# ===================== Usecase M2M Schemas =====================

class UsecaseAssign(BaseModel):
    usecase_id: UUID

class UsecaseRead(BaseModel):
    project_id: UUID
    usecase_id: UUID


# ===================== Custom Feature M2M Schemas =====================

class ProjectFeatureAssign(BaseModel):
    feature_id: UUID


class ExcludedFeaturesSet(BaseModel):
    """Full replacement set of use-case features this project opts out of."""
    feature_ids: list[UUID] = []



# ===================== Template-Based Generation Schemas =====================

class GenerateFromTemplatesRequest(BaseModel):
    template_ids: list[UUID]