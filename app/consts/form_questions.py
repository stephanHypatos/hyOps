"""
Form Questions Configuration
Organized by section with metadata for form rendering
"""

# Form structure with all questions organized by section
FORM_SECTIONS = {
    "company_profile": {
        "title": "Company Profile",
        "icon": "🏢",
        "expanded": True,
        "questions": [
            {
                "id": "customer_name",
                "label": "Company Name",
                "type": "text",
                "required": True,
                "placeholder": "e.g., Acme Corporation",
                "template_var": "{{CustomerName}}, {{CUS}}, {{CUSTOMERFULL}}"
            },
            {
                "id": "project_name",
                "label": "Project Name",
                "type": "select",
                "required": True,
                "options": ["Next Generation AI for Document Automation – Accounts Payables", "Next Generation AI for Document Automation – Order To Cash"],
                "template_var": "{{ProjectName}}"
            },
            {
                "id": "industry",
                "label": "Industry / Domain",
                "type": "select",
                "required": True,
                "options": [
                    "Healthcare / Medical",
                    "Logistics / Transportation",
                    "Media / Entertainment",
                    "Manufacturing",
                    "Financial Services",
                    "Retail / E-commerce",
                    "Technology / Software",
                    "Energy / Utilities",
                    "Professional Services",
                    "Telecommunications",
                    "Other"
                ]
            },
            {
                "id": "company_overview",
                "label": "Brief overview of company's activities",
                "type": "textarea",
                "required": False,
                "help": "Max 2-3 sentences"
            },
            {
                "id": "regions_operation",
                "label": "Regions of operation",
                "type": "multiselect",
                "required": False,
                "options": [
                    "EMEA",
                    "North America",
                    "APAC",
                    "Latin America",
                    "Middle East",
                    "Africa",
                    "Global"
                ]
            },
            {
                "id": "number_subsidiaries",
                "label": "Number of subsidiaries",
                "type": "number",
                "required": False
            },
            {
                "id": "languages",
                "label": "Languages",
                "type": "multiselect",
                "required": False,
                "options": ["English", "German", "French", "Spanish", "Italian", "Dutch", "Polish", "Other"]
            }
        ]
    },

    "business_objectives": {
        "title": "Business Objectives & Pain Points",
        "icon": "🎯",
        "expanded": True,
        "questions": [
            {
                "id": "main_objectives",
                "label": "Main objectives to be achieved with Hypatos",
                "type": "multiselect",
                "required": True,
                "help": "Auto-populated based on selected use case. You can modify if needed.",
                "options": [
                    "Increase processing efficiency and flexibility by leveraging LLM-based document understanding, enabling rapid adaptation to customer-specific requirements and invoice variations.",
                    "Achieve a high degree of touchless processing, targeting at least 80% straight-through processing for eligible invoices.",
                    "Accelerate and standardize order-to-cash document processing by automating the extraction and validation of order-related documents using LLM-based intelligence.",
                    "Reduce manual intervention in downstream processes by enabling touchless processing for the majority of standard order-to-cash transactions.",
                    "Automate the extraction and classification of travel and expense documents to improve processing speed, accuracy, and policy compliance.",
                    "Enable touchless handling of standard expense submissions, minimizing manual review effort while ensuring auditability and control.",
                    "Improve the efficiency and reliability of delivery note processing by automating document capture and data extraction using AI-based models.",
                    "Support automated matching and validation processes to reduce manual checks and increase straight-through processing rates for delivery documents.",
                    "Automate the processing of order confirmations to ensure timely, accurate capture of order data and alignment with purchase orders.",
                    "Reduce manual reconciliation effort by enabling touchless processing and early detection of deviations between orders and confirmations."
                ],
                "dynamic": True
            },
            {
                "id": "top_three_pain_points",
                "label": "Top three pain points in current document processing",
                "type": "textarea",
                "required": True,
                "help": "One per line",
                "rows": 4
            },
        ]
    },

    "volume_metrics": {
        "title": "Volume & Performance Metrics",
        "icon": "📊",
        "expanded": True,
        "questions": [
            {
                "id": "annual_document_volume",
                "label": "Annual document volume per use case",
                "type": "number",
                "required": True,
                "help": "Total documents per year"
            },
            {
                "id": "cost_per_document",
                "label": "End-to-End Cost per processed document (per use case)",
                "type": "number",
                "required": False,
                "help": "In EUR/USD"
            },
            {
                "id": "processing_time_minutes",
                "label": "End-to-End Processing Time (minutes) per use case",
                "type": "number",
                "required": False,
                "template_var": "{{CycleTime_Target}}"
            },
            {
                "id": "current_automation_percentage",
                "label": "Current percentage of automation to improve (per use case)",
                "type": "number",
                "required": False,
                "help": "0-100%",
                "template_var": "{{STP_Target}}"
            },
            {
                "id": "supplier_customer_count",
                "label": "Approximate count of Suppliers/Customers sending documents",
                "type": "number",
                "required": False
            }
        ]
    },

    "project_setup": {
        "title": "Project Setup & Scope",
        "icon": "📋",
        "expanded": True,
        "questions": [
            {
                "id": "use_cases",
                "label": "Use cases to be automated with Hypatos",
                "type": "select",
                "required": True,
                "options": [
                    "Invoice Processing Automation",
                    "Order to Cash Automation",
                    "Delivery Note Automation",
                    "Order Confirmation Automation",
                    "Travel Expense Automation"
                ],
                "template_var": "{{InScopeLong}}"
            },
            {
                "id": "project_type",
                "label": "Project Type",
                "type": "select",
                "required": True,
                "options": ["Custom Demo", "PoC", "Pilot"],
                "help": "PoC Projects have reduced scope and integration is not part of the project"
            },
            {
                "id": "project_start_date",
                "label": "Earliest possible Project start date",
                "type": "date",
                "required": True,
                "help": "Prerequisite: a team should be allocated to handle tasks"
            },
            {
                "id": "go_live_date",
                "label": "Target Go-Live Date",
                "type": "date",
                "required": True,
                "template_var": "{{GoLiveDate}}"
            },
            {
                "id": "project_background",
                "label": "Project Background and Goals",
                "type": "textarea",
                "required": True,
                "help": "Max two sentences",
                "rows": 2,
                "default": "This project validates the business benefits of Hypatos' AI-powered Document Automation solution by processing real transactions against historical and master data. The solution will reflect the customer's current and/or target processes, with IT landscape integration included for Pilot projects, enabling seamless transition to production upon successful validation."
            },
            {
                "id": "success_criteria",
                "label": "Criteria that must be achieved to close the project successfully",
                "type": "multiselect",
                "required": True,
                "options": [
                    "Standard Agentic Setup is configured",
                    "Customer Masterdata is uploaded and available",
                    "User has Access to Hypatos Studio",
                    "Manual Validation performed in Hypatos Studio (50 documents (25 FI / 25 MM))",
                    "One Special Requirement implemented (max 2h effort)",
                    "Touchless Rate: 40% of 80% of all transactions are fully touchless (one fiscal year)",
                    "100% Duplicate Detection",
                    "End-to-End Integration",
                    "Special Requirements implemented (max 10h additional effort)"
                ],
                "help": "Standard criteria are pre-selected based on project type. You can modify if needed.",
                "template_var": "{{Accuracy_Target}}, {{STP_Target}}",
                "dynamic": True
            },
            {
                "id": "success_criteria_custom",
                "label": "Additional custom success criteria (optional)",
                "type": "textarea",
                "required": False,
                "rows": 3,
                "placeholder": "Add any project-specific criteria not covered above",
                "help": "Use this field for any additional success criteria unique to this project"
            },
            {
                "id": "go_live_regions",
                "label": "Go-Live regions or company codes in scope",
                "type": "text",
                "required": False
            },
            {
                "id": "rollout_regions",
                "label": "Roll-out regions or company codes in scope",
                "type": "text",
                "required": False
            },
            {
                "id": "project_risks",
                "label": "Project risks",
                "type": "textarea",
                "required": False,
                "rows": 3
            },
            {
                "id": "language_constraints",
                "label": "Project Language & Documentation Requirements",
                "type": "select",
                "required": False,
                "options": [
                    "No language constraints - English is fine",
                    "German Project Manager required",
                    "German Project Material required",
                    "German Project Manager and Project Material required"
                ],
                "help": "Project language (documentation and project material) is English by default. If you require a German-speaking Project Manager and/or project materials in German, this will increase project costs and may delay project start."
            }
        ]
    },

    "stakeholders": {
        "title": "Stakeholders & Team",
        "icon": "👥",
        "expanded": True,
        "description": "Customer team and Hypatos/Vendor team contacts",
        "questions": [
            # Customer Team
            {"id": "project_sponsor_name", "label": "Project Sponsor - Name (Customer)", "type": "text", "required": True},
            {"id": "project_sponsor_email", "label": "Project Sponsor - Email (Customer)", "type": "email", "required": True},

            {"id": "project_lead_name", "label": "Project Lead - Name (Customer)", "type": "text", "required": True},
            {"id": "project_lead_email", "label": "Project Lead - Email (Customer)", "type": "email", "required": True},

            {"id": "business_lead_name", "label": "Business Lead - Name (Customer)", "type": "text", "required": False},
            {"id": "business_lead_email", "label": "Business Lead - Email (Customer)", "type": "email", "required": False},

            {"id": "technical_lead_name", "label": "Technical Lead - Name (Customer)", "type": "text", "required": False},
            {"id": "technical_lead_email", "label": "Technical Lead - Email (Customer)", "type": "email", "required": False},

            {"id": "ap_accountants_lead_name", "label": "AP Accountants Lead - Name (Customer)", "type": "text", "required": False},
            {"id": "ap_accountants_lead_email", "label": "AP Accountants Lead - Email (Customer)", "type": "email", "required": False},

            {"id": "integration_expert_name", "label": "Integration Expert - Name (Customer)", "type": "text", "required": False},
            {"id": "integration_expert_email", "label": "Integration Expert - Email (Customer)", "type": "email", "required": False},

            {"id": "external_consultant_name", "label": "External Consultant - Name (Customer)", "type": "text", "required": False},
            {"id": "external_consultant_email", "label": "External Consultant - Email (Customer)", "type": "email", "required": False},

            # Vendor/Hypatos Team
            {"id": "ae_name", "label": "Account Executive - Name (Hypatos)", "type": "text", "required": True},
            {"id": "ae_email", "label": "Account Executive - Email (Hypatos)", "type": "email", "required": True},

            {"id": "sa_name", "label": "Solutions Architect - Name (Hypatos)", "type": "text", "required": True},
            {"id": "sa_email", "label": "Solutions Architect - Email (Hypatos)", "type": "email", "required": True},

            {"id": "pm_name", "label": "Project Manager - Name (Hypatos)", "type": "text", "required": False},
            {"id": "pm_email", "label": "Project Manager - Email (Hypatos)", "type": "email", "required": False},

            {"id": "csm_name", "label": "Customer Success Manager - Name (Hypatos)", "type": "text", "required": False},
            {"id": "csm_email", "label": "Customer Success Manager - Email (Hypatos)", "type": "email", "required": False}
        ]
    },

    "technical_integration": {
        "title": "Technical Integration & Systems",
        "icon": "🔧",
        "expanded": False,
        "questions": [
            {
                "id": "target_erp",
                "label": "Target ERP that Hypatos should integrate with",
                "type": "multiselect",
                "required": True,
                "options": []
            },
            {
                "id": "sap_addon_concerns",
                "label": "SAP Addon Installation - Are there any concerns installing addon in PROD?",
                "type": "textarea",
                "required": False,
                "condition": "target_erp starts with 'SAP'",
                "rows": 2
            },
            {
                "id": "current_workflow",
                "label": "Current Workflow used in your SAP System",
                "type": "select",
                "required": False,
                "options": ["xsuite", "afi", "vim", "custom workflow", "no workflow"]
            },
            {
                "id": "existing_services",
                "label": "Existing services (software) involved in current document processing",
                "type": "textarea",
                "required": False,
                "help": "List all tools/services currently used",
                "rows": 3
            },
            {
                "id": "document_receipt_channels",
                "label": "Channels through which documents are received",
                "type": "multiselect",
                "required": True,
                "options": ["Email", "Portal", "EDI", "API", "Manual Upload", "Scan", "Other"]
            },
            {
                "id": "data_points_current",
                "label": "Data points in the current solution",
                "type": "textarea",
                "required": False,
                "help": "List key data points extracted currently",
                "rows": 3
            },
            {
                "id": "current_process_overview",
                "label": "Visual or written overview of current technical process per use case",
                "type": "textarea",
                "required": False,
                "rows": 4
            },
        ]
    },

    "document_processing_details": {
        "title": "Document Processing Details (Discovery)",
        "icon": "📄",
        "expanded": False,
        "description": "Detailed questions for solution configuration",
        "questions": [
            {
                "id": "users_work_in_studio",
                "label": "Will users work in the Hypatos Studio UI to validate documents?",
                "type": "select",
                "required": True,
                "options": ["Users work in Studio", "Users work in current ERP"],
                "help": "This determines the UI configuration during onboarding"
            },
            {
                "id": "supplier_guidelines",
                "label": "Do you send guidelines for document submission to suppliers?",
                "type": "textarea",
                "required": False,
                "help": "If yes, explain the guidelines",
                "rows": 3
            },
            {
                "id": "other_processing_guidelines",
                "label": "Other guidelines used during invoice processing",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "multi_invoice_documents",
                "label": "Do you receive documents with more than one invoice/credit note?",
                "type": "select",
                "required": False,
                "options": ["Yes", "No", "Sometimes"]
            },
            {
                "id": "multi_invoice_share",
                "label": "If yes, share of total volume (%)",
                "type": "number",
                "required": False,
                "condition": "multi_invoice_documents == 'Yes'"
            },
            {
                "id": "file_formats_received",
                "label": "File formats currently received",
                "type": "multiselect",
                "required": False,
                "options": ["PDF", "PDF/A", "TIFF", "JPG", "PNG", "XML", "EDI", "Other"]
            },
            {
                "id": "poor_quality_scans",
                "label": "Do you receive scanned documents with poor quality?",
                "type": "select",
                "required": False,
                "options": ["Frequently", "Sometimes", "Rarely", "Never"]
            },
            {
                "id": "document_submission_channels",
                "label": "Common document submission channels",
                "type": "multiselect",
                "required": False,
                "options": ["Email", "Portal", "EDI", "Scan", "Manual Upload", "Vendor Portal", "Other"]
            },
            {
                "id": "expected_doc_types_in_channels",
                "label": "Document types expected in channels in scope",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "out_of_scope_handling",
                "label": "What do you do with out-of-scope documents?",
                "type": "select",
                "required": False,
                "options": ["Reject", "Forward", "Manual Processing", "Other"]
            },
            {
                "id": "scanning_method",
                "label": "How do you perform scanning?",
                "type": "select",
                "required": False,
                "options": ["Batch scanning", "Individual scanning", "Mixed", "No scanning"]
            },
            {
                "id": "barcoding_separation",
                "label": "Do you use barcoding and page separation mechanisms?",
                "type": "select",
                "required": False,
                "options": ["Yes", "No", "Planning to"]
            },
            {
                "id": "classify_during_scan",
                "label": "Do you classify documents during scan process?",
                "type": "textarea",
                "required": False,
                "help": "e.g., into business units, document types, junk etc.",
                "rows": 2
            }
        ]
    },

    "email_processing": {
        "title": "Email Processing (if applicable)",
        "icon": "📧",
        "expanded": False,
        "questions": [
            {
                "id": "email_content_downstream",
                "label": "Is email content used in any downstream process?",
                "type": "select",
                "required": False,
                "options": ["Yes", "No", "Partially"]
            },
            {
                "id": "eml_archiving",
                "label": "Does the .eml file need to be archived?",
                "type": "select",
                "required": False,
                "options": ["Yes", "No"]
            },
            {
                "id": "inbound_email_rules",
                "label": "Do you apply rules on inbound emails?",
                "type": "textarea",
                "required": False,
                "help": "e.g., auto-rejection, whitelisting, blacklisting, routing",
                "rows": 3
            },
            {
                "id": "email_routing",
                "label": "Email routing strategy",
                "type": "textarea",
                "required": False,
                "help": "e.g., separate inboxes, forwarding rules",
                "rows": 2
            }
        ]
    },

    "classification_matching": {
        "title": "Classification & Matching Logic",
        "icon": "🔀",
        "expanded": False,
        "questions": [
            {
                "id": "document_classification_method",
                "label": "How do you classify different document types?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "statements_classification",
                "label": "Are Statements classified separately?",
                "type": "select",
                "required": False,
                "options": ["As Statements", "As Invoices", "As Payment Requests", "Other"]
            },
            {
                "id": "statements_downstream",
                "label": "How do you treat statements downstream?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "leases_recurring_handling",
                "label": "How do you handle Leases and recurring invoices?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "po_nonpo_identification",
                "label": "How do you identify PO / Non-PO invoices?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "po_nonpo_distribution",
                "label": "Distribution (%) of NON-PO / PO invoices",
                "type": "text",
                "required": False,
                "help": "e.g., 60% PO, 40% Non-PO"
            },
            {
                "id": "rejection_classification",
                "label": "How do you classify rejections?",
                "type": "textarea",
                "required": False,
                "help": "Forwarded to different queue/person/team?",
                "rows": 2
            },
            {
                "id": "rejection_timing",
                "label": "At what point are documents rejected or routed to specific queue?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "rejection_communication",
                "label": "How do you communicate rejection to suppliers?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "standardized_rejection_messages",
                "label": "Do you have standardized rejection messages?",
                "type": "select",
                "required": False,
                "options": ["Yes", "No", "Partially"]
            },
            {
                "id": "bounced_rejections_handling",
                "label": "How do you handle bounced rejections?",
                "type": "textarea",
                "required": False,
                "rows": 2
            }
        ]
    },

    "master_data_verification": {
        "title": "Master Data & Verification",
        "icon": "🗂️",
        "expanded": False,
        "questions": [
            {
                "id": "verification_team_structure",
                "label": "Invoice verification team structure",
                "type": "textarea",
                "required": False,
                "help": "Separate from accountants? Where located?",
                "rows": 2
            },
            {
                "id": "routing_criteria",
                "label": "Do you route invoices based on specific criteria to specific persons?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "master_data_assignment",
                "label": "How do you assign and verify Master Data (company code, vendor ID)?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "missing_master_data_handling",
                "label": "Exception handling if master data record does not exist",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "duplicate_master_data",
                "label": "Do you have many duplicate master data records?",
                "type": "select",
                "required": False,
                "options": ["Yes, many", "Some duplicates", "Few duplicates", "No duplicates"]
            }
        ]
    },

    "po_matching": {
        "title": "PO Matching & Processing",
        "icon": "📑",
        "expanded": False,
        "questions": [
            {
                "id": "delivery_note_extraction",
                "label": "Do you extract Delivery Note Numbers from invoices?",
                "type": "select",
                "required": False,
                "options": ["Yes", "No", "Sometimes"]
            },
            {
                "id": "po_types_common",
                "label": "Common types of Purchase Orders",
                "type": "multiselect",
                "required": False,
                "options": ["Standard PO", "Limit PO", "Material PO", "Service PO", "Other"]
            },
            {
                "id": "po_vs_invoice_values",
                "label": "For Price/Qty/Text/UoM, do you use values from PO or Invoice?",
                "type": "select",
                "required": False,
                "options": ["From PO", "From Invoice", "Depends on field"]
            },
            {
                "id": "po_deviation_handling",
                "label": "If price/qty/UoM deviates from PO, how do you proceed?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "missing_po_number",
                "label": "Do you receive invoices referencing PO but number not found on document?",
                "type": "select",
                "required": False,
                "options": ["Frequently", "Sometimes", "Rarely", "Never"]
            },
            {
                "id": "non_matched_po_processing",
                "label": "How do you process invoices that can't be matched against PO automatically?",
                "type": "textarea",
                "required": False,
                "rows": 2
            }
        ]
    },

    "accounting_coding": {
        "title": "Accounting Coding & GL Assignment",
        "icon": "💰",
        "expanded": False,
        "questions": [
            {
                "id": "custom_gl_logic",
                "label": "Do you have custom business logic that adds GL Accounts automatically?",
                "type": "select",
                "required": False,
                "options": ["Yes", "No", "Partially"]
            },
            {
                "id": "mandatory_posting_attributes",
                "label": "Mandatory attributes to park and post an invoice",
                "type": "multiselect",
                "required": False,
                "options": ["Tax Code", "GL Account", "Cost Center", "Internal Order", "WBS", "Profit Center", "Other"]
            },
            {
                "id": "accounting_templates_usage",
                "label": "Are accounting templates in use?",
                "type": "select",
                "required": False,
                "options": ["Yes", "No"],
                "help": "e.g., supplier XYZ always gets specific cost center or GL account"
            },
            {
                "id": "gl_costcenter_assignment",
                "label": "Who assigns GL Accounts, Cost Centers, Internal Order, WBS, Tax code?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "reviewer_approver_derivation",
                "label": "How do you derive the factual reviewer/approver of the invoice?",
                "type": "textarea",
                "required": False,
                "help": "Based on email, document, supplier, company code, cost center, etc.",
                "rows": 2
            }
        ]
    },

    "kpis_success": {
        "title": "KPIs & Success Measurement",
        "icon": "📈",
        "expanded": False,
        "questions": [
            {
                "id": "current_kpis",
                "label": "Which KPIs do you use to measure success in your I2P process?",
                "type": "textarea",
                "required": False,
                "rows": 3
            },
            {
                "id": "verification_team_kpis",
                "label": "How do you measure success of document verification teams?",
                "type": "textarea",
                "required": False,
                "rows": 2
            },
            {
                "id": "special_document_handling",
                "label": "Explain which documents need to be handled differently",
                "type": "textarea",
                "required": False,
                "rows": 2
            }
        ]
    }
}


# Success Criteria per Project Type
PROJECT_TYPE_SUCCESS_CRITERIA = {
    "Custom Demo": [
        "Standard Agentic Setup is configured",
        "Customer Masterdata is uploaded and available",
        "User has Access to Hypatos Studio"
    ],
    "PoC": [
        "Standard Agentic Setup is configured",
        "Manual Validation performed in Hypatos Studio (50 documents (25 FI / 25 MM))",
        "One Special Requirement implemented (max 2h effort)"
    ],
    "Pilot": [
        "Standard Agentic Setup is configured",
        "Touchless Rate: 40% of 80% of all transactions are fully touchless (one fiscal year)",
        "100% Duplicate Detection",
        "Manual Validation performed in Hypatos Studio (50 documents (25 FI / 25 MM))",
        "End-to-End Integration",
        "Special Requirements implemented (max 10h additional effort)"
    ]
}

# Standard Success Criteria Definitions (detailed explanations for SOW/Success Contract)
SUCCESS_CRITERIA_DEFINITIONS = {
    "Standard Agentic Setup is configured": """Hypatos will set up an out-of-the-box agentic workflow tailored to the customer's document processing requirements.""",

    "Customer Masterdata is uploaded and available": """Hypatos will upload the customer-specific masterdata (vendor/supplier data, company codes, GL accounts, cost centers, etc.) to the Hypatos environment.""",

    "User has Access to Hypatos Studio": """Hypatos will grant access to the customer's own Hypatos environment.""",

    "Manual Validation performed in Hypatos Studio (50 documents (25 FI / 25 MM))": """50 documents (25 FI / 25 MM) are manually validated by a Human-in-the-Loop within Hypatos Studio.""",

    "One Special Requirement implemented (max 2h effort)": """One custom requirement (additional to standard configuration) will be implemented, with a maximum effort of 2 hours.""",

    "Touchless Rate: 40% of 80% of all transactions are fully touchless (one fiscal year)": """**Required Data for Touchless Processing:**

**Header (mandatory fields):**
- Document number
- Document Date
- Currency
- Total gross
- Company code
- Supplier ID
- Total net
- Total tax amount
- Invoice type (invoice, credit note, etc.)
- Document type (FI, MM)

**Line-Level Data:**
- Non-PO invoices: Tax code, G/L account, Cost center
- PO invoices: PO number""",

    "100% Duplicate Detection": """100% duplicate detection - all duplicate invoices will be identified and flagged before posting.""",

    "End-to-End Integration": """Hypatos and the target ERP system are fully integrated end-to-end.""",

    "Special Requirements implemented (max 10h additional effort)": """All custom requirements (additional to standard configuration) will be implemented, with a maximum combined effort of 10 hours."""
}


# Project Deliverables per Project Type
PROJECT_TYPE_DELIVERABLES = {
    "Custom Demo": [
        {"deliverable": "Configured Workflow", "description": "End-to-end processing for in-scope documents", "owner": "Hypatos"},
        {"deliverable": "Insights Success Metrics Dashboard", "description": "STP, accuracy, cycle time, exceptions, volume; weekly reporting", "owner": "Hypatos"},
        {"deliverable": "UAT Pack", "description": "Test Playbook, entry/exit criteria, defect triage rules", "owner": "Hypatos"},
        {"deliverable": "Runbook + SOP", "description": "Operational guide, escalation path, ownership model", "owner": "Hypatos"},
        {"deliverable": "Dedicated Business and Tech Process Owner assigned", "description": "One person that combines business and tech knowledge needed for the onboarding is assigned or one person that can assign other person to perform tasks", "owner": "customer"},
        {"deliverable": "Data provided", "description": "Training and masterdata is handed over", "owner": "customer"},
    ],
    "PoC": [
        {"deliverable": "Configured Workflow", "description": "End-to-end processing for in-scope invoices incl. exceptions and routing", "owner": "Hypatos"},
        {"deliverable": "Insights Success Metrics Dashboard", "description": "STP, accuracy, cycle time, exceptions, volume; weekly reporting", "owner": "Hypatos"},
        {"deliverable": "UAT Pack", "description": "Test Playbook, entry/exit criteria, defect triage rules", "owner": "Hypatos"},
        {"deliverable": "Runbook + SOP", "description": "Operational guide, escalation path, ownership model", "owner": "Hypatos"},
        {"deliverable": "Dedicated Business and Tech Process Owner assigned", "description": "One person that combines business and tech knowledge needed for the onboarding is assigned or one person that can assign other person to perform tasks", "owner": "customer"},
        {"deliverable": "Data provided", "description": "Training and masterdata is handed over", "owner": "customer"},
    ],
    "Pilot": [
        {"deliverable": "Configured Workflow", "description": "End-to-end processing for in-scope invoices incl. exceptions and routing", "owner": "Hypatos"},
        {"deliverable": "Insights Success Metrics Dashboard", "description": "STP, accuracy, cycle time, exceptions, volume; weekly reporting", "owner": "Hypatos"},
        {"deliverable": "UAT Pack", "description": "Test Playbook, entry/exit criteria, defect triage rules", "owner": "Hypatos"},
        {"deliverable": "Runbook + SOP", "description": "Operational guide, escalation path, ownership model", "owner": "Hypatos"},
        {"deliverable": "Training", "description": "Admin + end user training; recordings/materials shared", "owner": "Hypatos"},
        {"deliverable": "Go-Live & Hypercare Report", "description": "Readiness checklist, hypercare outcomes, handover confirmation", "owner": "Hypatos"},
        {"deliverable": "Dedicated Business and Tech Process Owner assigned", "description": "One person that combines business and tech knowledge needed for the onboarding is assigned or one person that can assign other person to perform tasks", "owner": "customer"},
        {"deliverable": "Data provided", "description": "Training and masterdata is handed over", "owner": "customer"},
    ]
}


# Default objectives per use case (lists for multiselect pre-selection)
USE_CASE_OBJECTIVES = {
    "Invoice Processing Automation": [
        "Increase processing efficiency and flexibility by leveraging LLM-based document understanding, enabling rapid adaptation to customer-specific requirements and invoice variations.",
        "Achieve a high degree of touchless processing, targeting at least 80% straight-through processing for eligible invoices.",
    ],
    "Order to Cash Automation": [
        "Accelerate and standardize order-to-cash document processing by automating the extraction and validation of order-related documents using LLM-based intelligence.",
        "Reduce manual intervention in downstream processes by enabling touchless processing for the majority of standard order-to-cash transactions.",
    ],
    "Travel Expense Automation": [
        "Automate the extraction and classification of travel and expense documents to improve processing speed, accuracy, and policy compliance.",
        "Enable touchless handling of standard expense submissions, minimizing manual review effort while ensuring auditability and control.",
    ],
    "Delivery Note Automation": [
        "Improve the efficiency and reliability of delivery note processing by automating document capture and data extraction using AI-based models.",
        "Support automated matching and validation processes to reduce manual checks and increase straight-through processing rates for delivery documents.",
    ],
    "Order Confirmation Automation": [
        "Automate the processing of order confirmations to ensure timely, accurate capture of order data and alignment with purchase orders.",
        "Reduce manual reconciliation effort by enabling touchless processing and early detection of deviations between orders and confirmations.",
    ],
}


# Mapping of form fields to template variables
TEMPLATE_VARIABLE_MAPPING = {
    "customer_name": ["{{CustomerName}}", "{{CUS}}", "{{CUSTOMERFULL}}"],
    "vendor_name": ["{{VendorName}}"],  # This will be "Hypatos" by default
    "project_name": ["{{ProjectName}}"],
    "go_live_date": ["{{GoLiveDate}}"],
    "current_automation_percentage": ["{{STP_Target}}"],
    "success_criteria": ["{{Accuracy_Target}}"],
    "processing_time_minutes": ["{{CycleTime_Target}}"],
    "use_cases": ["{{InScopeLong}}"],
    # Add more mappings as needed
}
