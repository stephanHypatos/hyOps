"""
Adapters for Document Generation
Converts SQLModel DB objects to the form_data dict format expected by DocumentGenerator.
"""

from typing import Dict, Any, List
from datetime import datetime


def project_to_form_data(project) -> Dict[str, Any]:
    """
    Convert a Project (with eagerly loaded relationships) to the form_data dict
    that DocumentGenerator.generate_all_documents() expects.
    """
    customer = project.customer

    # ──────────────────────────────────────────────
    # 1. STAKEHOLDERS
    # ──────────────────────────────────────────────
    def _get_stakeholder(subtype_name: str) -> Dict[str, str]:
        """Find a stakeholder by their subtype role"""
        for user in project.stakeholders:
            if user.subtype.name == subtype_name:
                return {
                    'name': f"{user.first_name} {user.last_name}".strip(),
                    'email': user.email
                }
        return {'name': '', 'email': ''}
    
    # Customer stakeholders
    project_sponsor = _get_stakeholder('project_sponsor')
    project_lead = _get_stakeholder('project_lead')
    business_lead = _get_stakeholder('business_lead')
    technical_lead = _get_stakeholder('technical_lead')
    ap_lead = _get_stakeholder('accounts_payable_lead')
    
    # Hypatos stakeholders
    ae = _get_stakeholder('account_executive')
    sa = _get_stakeholder('solution_architect')
    pm = _get_stakeholder('project_manager')
    csm = _get_stakeholder('customer_success_manager')
    
    # ──────────────────────────────────────────────
    # 2. FEATURES (grouped by Capability.contract)
    # ──────────────────────────────────────────────
    def _build_feature_list(features: list) -> List[Dict[str, Any]]:
        """Convert Feature objects to the list format DocumentGenerator expects"""
        return [
            {
                'feature_name': f.name,
                'feature_code': str(f.id),
            }
            for f in features
        ]
    
    # Group features by capability contract
    features_by_category: Dict[str, list] = {
        'professional_services': [],
        'hypatos_studio': [],
        'hypatos_insights': [],
        'document_processing': [],
        'translation_ai': [],
        'data_enrichment': [],
        'integration': [],
        'archiving': [],
    }
    
    for usecase in project.linked_usecases:
        for feature in usecase.features:
            category = feature.capability.contract if feature.capability else None
            if category in features_by_category:
                features_by_category[category].append(feature)
    
    # ──────────────────────────────────────────────
    # 3. USE CASES
    # ──────────────────────────────────────────────
    primary_usecase_name = project.primary_usecase.name if project.primary_usecase else ''
    
    # ──────────────────────────────────────────────
    # 4. BUILD THE DICT
    # ──────────────────────────────────────────────
    form_data = {
        # === Top-level fields ===
        
        # Basic info
        'customer_name': customer.name,
        'project_name': project.name,
        'project_type': project.type.value if project.type else '',
        'industry': customer.industry or 'N/A',
        'company_overview': customer.company_overview or '',
        
        # Objectives & pain points
        'main_objectives': project.main_objectives or [],
        'top_three_pain_points': project.top_three_pain_points or '',
        'use_cases': primary_usecase_name,
        
        # Volume metrics
        'annual_document_volume': project.annual_doc_volume_per_usecase or 'N/A',
        'cost_per_document': float(project.e2e_cost_per_doc) if project.e2e_cost_per_doc else 'N/A',
        'processing_time_minutes': project.e2e_processing_time_mins or 'N/A',
        'current_automation_percentage': project.automation_improvement_percentage or 0,
        'overall_accuracy_target': project.overall_accuracy_target or 95,
        
        # Timeline
        'project_start_date': str(project.start_date) if project.start_date else 'TBD',
        'go_live_date': str(project.go_live_date) if project.go_live_date else 'TBD',
        'go_live_regions': project.go_live_regions or '',
        'rollout_regions': project.rollout_regions or '',
        
        # Background & risks
        'project_background': project.project_background or '',
        'project_risks': project.project_risks or '',
        'language_constraints': project.language_constraints or 'No language constraints - English is fine',
        
        # Success criteria
        'success_criteria': project.success_criteria or [],
        'success_criteria_custom': project.success_criteria_custom or '',
        
        # Technical
        'primary_erp_system': project.target_erp or '',
        'users_work_in_studio': project.users_work_in_studio or False,
        
        # Document types
        'document_types': project.document_types or [],
        
        # Stakeholders - Hypatos (top level)
        'ae_name': ae['name'], 'ae_email': ae['email'],
        'sa_name': sa['name'], 'sa_email': sa['email'],
        'pm_name': pm['name'], 'pm_email': pm['email'],
        'csm_name': csm['name'], 'csm_email': csm['email'],
        
        # Feature category lists (top level)
        'professional_services': _build_feature_list(features_by_category['professional_services']),
        'hypatos_studio': _build_feature_list(features_by_category['hypatos_studio']),
        'hypatos_insights': _build_feature_list(features_by_category['hypatos_insights']),
        'document_processing': _build_feature_list(features_by_category['document_processing']),
        'translation_ai': _build_feature_list(features_by_category['translation_ai']),
        'data_enrichment': _build_feature_list(features_by_category['data_enrichment']),
        'integration': _build_feature_list(features_by_category['integration']),
        'archiving': _build_feature_list(features_by_category['archiving']),
        
        # === Extended data (nested) ===
        'extended_data': {
            # Success criteria
            'success_criteria': project.success_criteria or [],
            'success_criteria_custom': project.success_criteria_custom or '',
            
            # Use cases & objectives (duplicated for compat)
            'use_cases': primary_usecase_name,
            'main_objectives': project.main_objectives or [],
            'top_three_pain_points': project.top_three_pain_points or '',
            
            # Customer stakeholders
            'project_sponsor_name': project_sponsor['name'],
            'project_sponsor_email': project_sponsor['email'],
            'project_lead_name': project_lead['name'],
            'project_lead_email': project_lead['email'],
            'business_lead_name': business_lead['name'],
            'business_lead_email': business_lead['email'],
            'technical_lead_name': technical_lead['name'],
            'technical_lead_email': technical_lead['email'],
            'ap_accountants_lead_name': ap_lead['name'],
            'ap_accountants_lead_email': ap_lead['email'],
            
            # Technical
            'target_erp': project.target_erp or 'N/A',
            'current_workflow': project.current_workflow or '',
            'existing_services': project.existing_services or '',
            'sap_addon_concerns': project.sap_addon_concerns or '',
            'document_receipt_channels': project.document_receipt_channels or [],
            'data_points_current': project.data_points_current or '',
            'number_erp_systems': project.number_erp_systems,
        },
    }
    
    return form_data


class FeatureDBAdapter:
    """
    Mimics the old db_manager interface so DocumentGenerator works without code changes.
    It uses the in-memory features loaded from the DB relationships.
    """
    def __init__(self, features_list: list):
        # Index features by their string ID for fast lookup
        self.features = {str(f.id): f for f in features_list}

    def get_requirements_by_feature(self, feature_code: str) -> list:
        feature = self.features.get(feature_code)
        if not feature:
            return []
        
        # Use the structured JSONB requirements if available
        if feature.requirements:
            return feature.requirements
        
        # Fallback to flat text fields if JSONB is empty
        if feature.requirement_description:
            return [{
                'requirement': feature.requirement_description,
                'description': feature.service_description or '',
                'solution': feature.solution_description or ''
            }]
        
        return []