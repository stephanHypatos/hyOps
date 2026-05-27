"""
Document Generator
Generates onboarding documents from submission data
"""

import os
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from app.consts.form_questions import SUCCESS_CRITERIA_DEFINITIONS, PROJECT_TYPE_DELIVERABLES
from app.utils.logger import logger
from app.config import basedir

class DocumentGenerator:
    """Generates onboarding documents"""

    def __init__(self, output_dir: Path, template_dir: Path = None, db_manager=None):
        """
        Initialize document generator

        Args:
            output_dir: Directory to save generated documents
            template_dir: Directory containing template files
            db_manager: Optional DatabaseManager for fetching feature requirements
        """
        # self.output_dir = output_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.template_dir = Path(os.path.join(basedir,"doc_templates"))
        # self.template_dir = template_dir or Path(__file__).parent.parent / "templates"
        self.db_manager = db_manager

    def _load_template(self, template_name: str) -> str:
        """Load a template file"""
        template_path = self.template_dir / template_name
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with mustache-like syntax.

        Supports:
        - {{variable}} - simple variable substitution
        - {{#section}}...{{/section}} - conditional sections (shown if truthy)
        - {{^section}}...{{/section}} - inverted sections (shown if falsy)
        - {{#list}}...{{/list}} - list iteration
        """
        if not template:
            return ""

        result = template

        # Handle list iterations first (e.g., {{#document_types_list}}...{{/document_types_list}})
        list_pattern = r'\{\{#(\w+_list)\}\}(.*?)\{\{/\1\}\}'
        for match in re.finditer(list_pattern, result, re.DOTALL):
            list_name = match.group(1)
            list_template = match.group(2)
            list_data = context.get(list_name, [])

            if list_data:
                rendered_items = []
                for i, item in enumerate(list_data):
                    item_context = {**item, 'index': i + 1}
                    item_rendered = list_template
                    for key, value in item_context.items():
                        item_rendered = item_rendered.replace(f'{{{{{key}}}}}', str(value) if value else '')
                    rendered_items.append(item_rendered.strip())
                result = result.replace(match.group(0), '\n'.join(rendered_items))
            else:
                result = result.replace(match.group(0), '')

        # Handle conditional sections (e.g., {{#section}}...{{/section}})
        section_pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'
        for match in re.finditer(section_pattern, result, re.DOTALL):
            section_name = match.group(1)
            section_content = match.group(2)
            section_value = context.get(section_name)

            if section_value:
                # Replace section with content, also substitute any nested variables
                rendered = section_content
                for key, value in context.items():
                    if not isinstance(value, (list, dict)):
                        rendered = rendered.replace(f'{{{{{key}}}}}', str(value) if value else '')
                result = result.replace(match.group(0), rendered)
            else:
                result = result.replace(match.group(0), '')

        # Handle inverted sections (e.g., {{^section}}...{{/section}})
        inverted_pattern = r'\{\{\^(\w+)\}\}(.*?)\{\{/\1\}\}'
        for match in re.finditer(inverted_pattern, result, re.DOTALL):
            section_name = match.group(1)
            section_content = match.group(2)
            section_value = context.get(section_name)

            if not section_value:
                result = result.replace(match.group(0), section_content)
            else:
                result = result.replace(match.group(0), '')

        # Handle simple variable substitution
        for key, value in context.items():
            if not isinstance(value, (list, dict)):
                result = result.replace(f'{{{{{key}}}}}', str(value) if value else 'N/A')

        # Clean up any remaining unsubstituted variables
        result = re.sub(r'\{\{[^}]+\}\}', '', result)

        # Clean up excessive blank lines
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result

    def _build_template_context(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the context dictionary for template rendering"""
        extended_data = form_data.get('extended_data', {})
        customer_name = form_data.get('customer_name', 'Customer')

        # Build feature lists for all 7 new categories
        def _build_feature_list(items, name_keys=('feature_name', 'feature_code')):
            result = []
            for item in items:
                name = None
                for key in name_keys:
                    if item.get(key):
                        name = item[key]
                        break
                result.append({'feature_name': name or 'Unknown'})
            return result

        professional_services_list = _build_feature_list(form_data.get('professional_services', []))
        hypatos_studio_list = _build_feature_list(form_data.get('hypatos_studio', []))
        hypatos_insights_list = _build_feature_list(form_data.get('hypatos_insights', []))
        document_processing_list = _build_feature_list(form_data.get('document_processing', []))
        translation_ai_list = _build_feature_list(form_data.get('translation_ai', []))
        data_enrichment_list = _build_feature_list(form_data.get('data_enrichment', []))
        integration_list = _build_feature_list(form_data.get('integration', []), name_keys=('feature_name', 'integration_name', 'feature_code', 'integration_type'))
        archiving_list = _build_feature_list(form_data.get('archiving', []))

        # Backward compat lists (for old template sections)
        core_features_list = _build_feature_list(form_data.get('core_features', []))
        validation_features_list = _build_feature_list(form_data.get('validation_features', []))
        governance_features_list = _build_feature_list(form_data.get('governance_features', []))
        integrations_list = _build_feature_list(
            form_data.get('integrations', []) or form_data.get('integration', []),
            name_keys=('feature_name', 'integration_name', 'feature_code', 'integration_type')
        )
        doc_types = form_data.get('document_types', [])
        document_types_list = [{'document_name': dt.get('document_name', dt.get('document_type', 'Unknown')), 'accuracy_target': dt.get('accuracy_target', 95)} for dt in doc_types]

        # Build success criteria list
        success_criteria = extended_data.get('success_criteria', [])
        success_criteria_list = []
        for i, criterion in enumerate(success_criteria, 1):
            success_criteria_list.append({
                'index': i,
                'criterion_name': criterion,
                'criterion_definition': SUCCESS_CRITERIA_DEFINITIONS.get(criterion, ''),
                'measurement_method': 'Automated system metrics',
                'target_value': 'As defined above'
            })

        # Build deliverables list based on project type
        project_type = form_data.get('project_type', '')
        deliverables = PROJECT_TYPE_DELIVERABLES.get(project_type, [])
        deliverables_list = []
        for d in deliverables:
            owner = d['owner']
            # Replace 'customer' with actual customer name
            if owner == 'customer':
                owner = customer_name
            deliverables_list.append({
                'deliverable_name': d['deliverable'],
                'deliverable_description': d['description'],
                'deliverable_owner': owner
            })

        # Determine user interface
        users_in_studio = form_data.get('users_work_in_studio', False)
        if isinstance(users_in_studio, str):
            users_in_studio = 'studio' in users_in_studio.lower()

        # Language check
        language_constraints = form_data.get('language_constraints', 'No language constraints - English is fine')
        is_german = 'German' in str(language_constraints)

        # Project type check (for conditional sections)
        project_type = form_data.get('project_type', '')
        is_pilot = project_type == 'Pilot'

        context = {
            # Basic info
            'customer_name': customer_name,
            'customer_acronym': self.generate_customer_acronym(customer_name),
            'project_name': form_data.get('project_name', 'Automation Project'),
            'project_type': form_data.get('project_type', 'N/A'),
            'industry': form_data.get('industry', 'N/A'),
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'generated_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),

            # Company info
            'company_overview': form_data.get('company_overview', ''),
            'project_background': form_data.get('project_background', ''),

            # Objectives (convert list to formatted text for templates)
            'main_objectives': '\n'.join(f'- {obj}' for obj in form_data.get('main_objectives', [])) if isinstance(form_data.get('main_objectives'), list) else form_data.get('main_objectives', ''),
            'top_three_pain_points': form_data.get('top_three_pain_points', ''),
            'use_cases': form_data.get('use_cases', ''),

            # Volume metrics
            'annual_document_volume': form_data.get('annual_document_volume', 'N/A'),
            'processing_time_minutes': form_data.get('processing_time_minutes', 'N/A'),
            'current_automation_percentage': form_data.get('current_automation_percentage', 0),
            'target_automation_percentage': 80,
            'cost_per_document': form_data.get('cost_per_document', 'N/A'),
            'touchless_target': 80,

            # Timeline
            'project_start_date': form_data.get('project_start_date', 'TBD'),
            'go_live_date': form_data.get('go_live_date', 'TBD'),
            'go_live_regions': form_data.get('go_live_regions', ''),
            'rollout_regions': form_data.get('rollout_regions', ''),

            # Technical
            'target_erp': form_data.get('primary_erp_system') or extended_data.get('target_erp', 'N/A'),
            'current_workflow': extended_data.get('current_workflow', ''),
            'user_interface': 'Hypatos Studio' if users_in_studio else 'ERP System',

            # Language
            'language_constraints': language_constraints,
            'is_german': is_german,

            # Project type flags
            'is_pilot': is_pilot,

            # Risks
            'project_risks': form_data.get('project_risks', ''),

            # Success criteria
            'success_criteria_custom': extended_data.get('success_criteria_custom', ''),
            'overall_accuracy_target': form_data.get('overall_accuracy_target', 95),

            # Stakeholders - Customer
            'project_sponsor_name': extended_data.get('project_sponsor_name', ''),
            'project_sponsor_email': extended_data.get('project_sponsor_email', ''),
            'project_lead_name': extended_data.get('project_lead_name', ''),
            'project_lead_email': extended_data.get('project_lead_email', ''),
            'business_lead_name': extended_data.get('business_lead_name', ''),
            'business_lead_email': extended_data.get('business_lead_email', ''),
            'technical_lead_name': extended_data.get('technical_lead_name', ''),
            'technical_lead_email': extended_data.get('technical_lead_email', ''),
            'ap_accountants_lead_name': extended_data.get('ap_accountants_lead_name', ''),
            'ap_accountants_lead_email': extended_data.get('ap_accountants_lead_email', ''),

            # Stakeholders - Hypatos
            'ae_name': form_data.get('ae_name', ''),
            'ae_email': form_data.get('ae_email', ''),
            'sa_name': form_data.get('sa_name', ''),
            'sa_email': form_data.get('sa_email', ''),
            'pm_name': form_data.get('pm_name', ''),
            'pm_email': form_data.get('pm_email', ''),
            'csm_name': form_data.get('csm_name', ''),
            'csm_email': form_data.get('csm_email', ''),

            # New category flags (bool for template conditionals)
            'professional_services': bool(professional_services_list),
            'hypatos_studio': bool(hypatos_studio_list),
            'hypatos_insights': bool(hypatos_insights_list),
            'document_processing': bool(document_processing_list),
            'translation_ai': bool(translation_ai_list),
            'data_enrichment': bool(data_enrichment_list),
            'integration': bool(integration_list),
            'archiving': bool(archiving_list),

            # New category lists
            'professional_services_list': professional_services_list,
            'hypatos_studio_list': hypatos_studio_list,
            'hypatos_insights_list': hypatos_insights_list,
            'document_processing_list': document_processing_list,
            'translation_ai_list': translation_ai_list,
            'data_enrichment_list': data_enrichment_list,
            'integration_list': integration_list,
            'archiving_list': archiving_list,

            # Backward compat lists (for conditionals)
            'document_types': bool(document_types_list),
            'core_features': bool(core_features_list),
            'validation_features': bool(validation_features_list),
            'integrations': bool(integrations_list),
            'governance_features': bool(governance_features_list),
            'deliverables': bool(deliverables_list),

            # Backward compat lists (for iteration)
            'document_types_list': document_types_list,
            'core_features_list': core_features_list,
            'validation_features_list': validation_features_list,
            'integrations_list': integrations_list,
            'governance_features_list': governance_features_list,
            'success_criteria_list': success_criteria_list,
            'deliverables_list': deliverables_list,
        }

        # Build dynamic SDD sections from feature requirements
        if self.db_manager:
            context['application_components_sections'] = self._build_application_components_sections(form_data)
            context['system_integration_sections'] = self._build_system_integration_sections(form_data)
        else:
            context['application_components_sections'] = '_No feature requirements configured. Add requirements via Feature Management._'
            context['system_integration_sections'] = '_No integration requirements configured. Add requirements via Feature Management._'

        return context

    def _build_feature_section_md(self, feature_name: str, requirements: list) -> str:
        """Build a markdown section for a single feature with its requirements/solutions."""
        lines = [f'### {feature_name}', '']

        if not requirements:
            lines.append('_No requirements defined for this feature._')
            lines.append('')
            return '\n'.join(lines)

        # Requirements table
        lines.append('#### Requirements')
        lines.append('')
        lines.append('| Requirement | Description |')
        lines.append('|-------------|-------------|')
        for req in requirements:
            requirement = (req.get('requirement') or '').replace('|', '\\|')
            description = (req.get('description') or '').replace('|', '\\|')
            lines.append(f'| {requirement} | {description} |')
        lines.append('')

        # Solution table (only if any solution text exists)
        if any(req.get('solution') for req in requirements):
            lines.append('#### Solution')
            lines.append('')
            lines.append('| Requirement | Solution |')
            lines.append('|-------------|----------|')
            for req in requirements:
                requirement = (req.get('requirement') or '').replace('|', '\\|')
                solution = (req.get('solution') or '').replace('|', '\\|')
                lines.append(f'| {requirement} | {solution} |')
            lines.append('')

        lines.append('---')
        lines.append('')
        return '\n'.join(lines)

    def _build_application_components_sections(self, form_data: Dict[str, Any]) -> str:
        """Build dynamic Application Components content from selected non-integration features."""
        sections = []

        # All non-integration feature categories
        feature_groups = [
            form_data.get('professional_services', []),
            form_data.get('hypatos_studio', []),
            form_data.get('hypatos_insights', []),
            form_data.get('document_processing', []),
            form_data.get('translation_ai', []),
            form_data.get('data_enrichment', []),
            form_data.get('archiving', []),
        ]

        for group in feature_groups:
            for feature in group:
                feature_code = feature.get('feature_code') or feature.get('document_type', '')
                feature_name = feature.get('feature_name') or feature.get('document_name', feature_code)
                requirements = self.db_manager.get_requirements_by_feature(feature_code)
                sections.append(self._build_feature_section_md(feature_name, requirements))

        if not sections:
            return '_No features selected._'

        return '\n'.join(sections)

    def _build_system_integration_sections(self, form_data: Dict[str, Any]) -> str:
        """Build dynamic System Integration content from selected integration features."""
        sections = []

        for integration in form_data.get('integration', []) or form_data.get('integrations', []):
            feature_code = integration.get('feature_code') or integration.get('integration_type', '')
            feature_name = integration.get('feature_name') or integration.get('integration_name', feature_code)
            requirements = self.db_manager.get_requirements_by_feature(feature_code)
            sections.append(self._build_feature_section_md(feature_name, requirements))

        if not sections:
            return '_No integrations selected._'

        return '\n'.join(sections)

    def generate_customer_acronym(self, customer_name: str) -> str:
        """
        Generate a 3-letter acronym from customer name

        Args:
            customer_name: Customer company name

        Returns:
            3-letter acronym in uppercase
        """
        if not customer_name:
            return "CUS"

        # Remove common company suffixes
        name = re.sub(r'\b(Inc|LLC|Ltd|GmbH|AG|Corp|Corporation|Company|Co)\b\.?', '', customer_name, flags=re.IGNORECASE)

        # Split into words and filter out short words
        words = [w.strip() for w in name.split() if len(w.strip()) > 0]

        if len(words) == 0:
            # Fallback to first 3 letters of customer name
            return customer_name[:3].upper()

        elif len(words) == 1:
            # Single word: take first 3 letters
            return words[0][:3].upper()

        elif len(words) == 2:
            # Two words: first 2 letters of first word + first letter of second
            return (words[0][:2] + words[1][:1]).upper()

        else:
            # Three or more words: first letter of each of first 3 words
            return (words[0][:1] + words[1][:1] + words[2][:1]).upper()

    def generate_sow(self, form_data: Dict[str, Any], submission_id: int) -> str:
        """
        Generate Statement of Work markdown document

        Args:
            form_data: Form submission data
            submission_id: Submission ID

        Returns:
            Path to generated document
        """
        customer_name = form_data.get('customer_name', 'Customer')
        customer_acronym = self.generate_customer_acronym(customer_name)
        extended_data = form_data.get('extended_data', {})

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{timestamp}_{customer_acronym}_Statement_of_Work.md"
        filepath = self.output_dir / filename

        # Try to use template file first
        template = self._load_template('sow_template.md')
        if template:
            context = self._build_template_context(form_data)
            content = self._render_template(template, context)
            logger.info("Using template file for SOW generation")
        else:
            # Fallback to programmatic generation
            content = self._build_sow_content(form_data, customer_name, customer_acronym, extended_data)
            logger.info("Using programmatic SOW generation (template not found)")

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated SOW: {filepath}")
        return str(filepath)

    def _build_sow_content(self, form_data: Dict[str, Any], customer_name: str, customer_acronym: str, extended_data: Dict[str, Any]) -> str:
        """Build the Statement of Work content"""
        # [Unchanged programmatic SOW builder method from original file]
        # I am truncating this for brevity, but you should paste your full _build_sow_content method here.
        # It works perfectly as-is.
        return "# Statement of Work\n\n_Generated programmatically (Template missing)_"

    def generate_sow_docx(self, form_data: Dict[str, Any], submission_id: int) -> Tuple[str, bytes]:
        """
        Generate Statement of Work as a Word document (.docx)

        Args:
            form_data: Form submission data
            submission_id: Submission ID

        Returns:
            Tuple of (filepath, document_bytes) for download
        """
        customer_name = form_data.get('customer_name', 'Customer')
        customer_acronym = self.generate_customer_acronym(customer_name)
        extended_data = form_data.get('extended_data', {})

        # Create document
        doc = Document()
        # [Unchanged DOCX builder logic from original file]
        # I am truncating this for brevity, but you should paste your full DOCX builder logic here.

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{timestamp}_{customer_acronym}_Statement_of_Work.docx"
        filepath = self.output_dir / filename

        # Save to file
        doc.save(filepath)

        # Also return bytes for download
        doc_bytes = io.BytesIO()
        doc.save(doc_bytes)
        doc_bytes.seek(0)

        logger.info(f"Generated SOW (Word): {filepath}")
        return str(filepath), doc_bytes.getvalue()

    def generate_success_contract(self, form_data: Dict[str, Any], submission_id: int) -> str:
        """
        Generate Success Contract markdown document from template

        Args:
            form_data: Form submission data
            submission_id: Submission ID

        Returns:
            Path to generated document
        """
        customer_name = form_data.get('customer_name', 'Customer')
        customer_acronym = self.generate_customer_acronym(customer_name)

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{timestamp}_{customer_acronym}_Success_Contract.md"
        filepath = self.output_dir / filename

        # Load and render template
        template = self._load_template('success_contract_template.md')
        if template:
            context = self._build_template_context(form_data)
            content = self._render_template(template, context)
            logger.info("Using template file for Success Contract generation")
        else:
            # Fallback to basic content if template not found
            content = f"# Success Contract\n## {customer_name}\n\nTemplate not found. Please create templates/success_contract_template.md"
            logger.warning("Success Contract template not found")

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated Success Contract: {filepath}")
        return str(filepath)

    def generate_solution_design(self, form_data: Dict[str, Any], submission_id: int) -> str:
        """
        Generate Solution Design Document markdown

        Args:
            form_data: Form submission data
            submission_id: Submission ID

        Returns:
            Path to generated document
        """
        customer_name = form_data.get('customer_name', 'Customer')
        customer_acronym = self.generate_customer_acronym(customer_name)

        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"{timestamp}_{customer_acronym}_Solution_Design.md"
        filepath = self.output_dir / filename

        template = self._load_template('solution_design_invoice_processing_template.md')
        if template:
            context = self._build_template_context(form_data)
            content = self._render_template(template, context)
            logger.info("Using template file for Solution Design generation")
        else:
            content = f"# Solution Design Document\n## {customer_name}\n\nTemplate not found."
            logger.warning("Solution Design template not found")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Generated Solution Design: {filepath}")
        return str(filepath)

    def generate_all_documents(self, form_data: Dict[str, Any], submission_id: int) -> Dict[str, Any]:
        """
        Generate all documents for a submission

        Args:
            form_data: Form submission data
            submission_id: Submission ID

        Returns:
            Dictionary mapping document type to file path and bytes
        """
        documents = {}

        try:
            # Generate SOW (Markdown)
            sow_path = self.generate_sow(form_data, submission_id)
            documents['sow'] = sow_path
            logger.info(f"Generated SOW (Markdown) for submission {submission_id}")

            # Generate SOW (Word)
            sow_docx_path, sow_docx_bytes = self.generate_sow_docx(form_data, submission_id)
            documents['sow_docx'] = sow_docx_path
            documents['sow_docx_bytes'] = sow_docx_bytes
            logger.info(f"Generated SOW (Word) for submission {submission_id}")

            # Generate Success Contract (Markdown)
            success_contract_path = self.generate_success_contract(form_data, submission_id)
            documents['success_contract'] = success_contract_path
            logger.info(f"Generated Success Contract for submission {submission_id}")

            # Generate Solution Design Document (Markdown)
            solution_design_path = self.generate_solution_design(form_data, submission_id)
            documents['solution_design'] = solution_design_path
            logger.info(f"Generated Solution Design for submission {submission_id}")

        except Exception as e:
            logger.error(f"Error generating documents: {e}")
            raise

        return documents