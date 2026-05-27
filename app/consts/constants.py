"""
Feature Matrix and Constants for AP Onboarding Automation
"""

# Industry options for dropdown
INDUSTRY_OPTIONS = [
    "Manufacturing",
    "Financial Services",
    "Healthcare",
    "Retail",
    "Technology",
    "Energy & Utilities",
    "Professional Services",
    "Government",
    "Other"
]

# Project types
PROJECT_TYPES = ["POC", "Pilot", "Production"]

# Compliance framework options
COMPLIANCE_FRAMEWORKS = [
    "GDPR",
    "SOX",
    "ISO 27001",
    "PCI-DSS",
    "HIPAA",
    "SOC 2"
]

# Feature Categories and Definitions
# Each feature includes:
# - name: Display name
# - description: Feature description
# - default_accuracy: Default accuracy target (for document types)
# - template_section: Placeholder for conditional sections
# - required: Whether feature must be selected
# - requires_config: Whether feature needs additional configuration
# - config_fields: List of configuration fields needed
# - impacts: Which documents are affected

FEATURE_CATEGORIES = {
    "document_types": {
        "name": "Document Types",
        "description": "Types of documents to process",
        "features": {
            "invoice": {
                "name": "Standard Invoices",
                "description": "Regular supplier invoices without PO reference",
                "default_accuracy": 95.0,
                "template_section": "section_invoice_processing",
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "po_based": {
                "name": "PO-based Invoices",
                "description": "Invoices with purchase order reference",
                "default_accuracy": 97.0,
                "template_section": "section_po_processing",
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "credit_note": {
                "name": "Credit Notes",
                "description": "Credit memos and adjustments",
                "default_accuracy": 94.0,
                "template_section": "section_credit_note",
                "impacts": ["success_contract", "solution_design"]
            },
            "receipt": {
                "name": "Receipts / Proof of Delivery",
                "description": "Delivery receipts and confirmations",
                "default_accuracy": 92.0,
                "template_section": "section_receipt",
                "impacts": ["solution_design"]
            },
            "utility_bill": {
                "name": "Utility Bills",
                "description": "Recurring utility invoices",
                "default_accuracy": 93.0,
                "template_section": "section_utility_bill",
                "impacts": ["solution_design"]
            }
        }
    },
    "core_capabilities": {
        "name": "Core Processing Capabilities",
        "description": "Fundamental processing capabilities",
        "features": {
            "classification": {
                "name": "Document Classification",
                "description": "Automatically classify incoming documents by type",
                "template_section": "section_classification",
                "required": True,
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "extraction": {
                "name": "Data Extraction (OCR)",
                "description": "Extract header and field data from documents",
                "template_section": "section_extraction",
                "required": True,
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "line_items": {
                "name": "Line Item Extraction",
                "description": "Extract table data and line items",
                "template_section": "section_line_items",
                "required": False,
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "matching_2way": {
                "name": "2-Way Matching",
                "description": "Match invoice to purchase order",
                "template_section": "section_2way_matching",
                "required": False,
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "matching_3way": {
                "name": "3-Way Matching",
                "description": "Match invoice, PO, and goods receipt",
                "template_section": "section_3way_matching",
                "required": False,
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "duplicate_detection": {
                "name": "Duplicate Detection",
                "description": "Identify and flag duplicate invoices",
                "template_section": "section_duplicate_detection",
                "required": False,
                "impacts": ["success_contract", "solution_design"]
            }
        }
    },
    "validation": {
        "name": "Validation Features",
        "description": "Advanced validation capabilities",
        "features": {
            "business_rules": {
                "name": "Business Rules Engine",
                "description": "Custom validation rules and logic",
                "template_section": "section_business_rules",
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "master_data": {
                "name": "Master Data Validation",
                "description": "Validate against vendor master, GL accounts, cost centers",
                "template_section": "section_master_data",
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "tolerance_checking": {
                "name": "Tolerance Checking",
                "description": "Check values against defined tolerance limits",
                "template_section": "section_tolerance",
                "impacts": ["success_contract", "solution_design"]
            },
            "tax_verification": {
                "name": "Tax Calculation Verification",
                "description": "Verify tax amounts and rates",
                "template_section": "section_tax_verification",
                "impacts": ["success_contract", "solution_design"]
            }
        }
    },
    "integrations": {
        "name": "System Integrations",
        "description": "External system connections",
        "features": {
            "sap": {
                "name": "SAP Integration",
                "description": "Post documents to SAP ECC/S4HANA",
                "template_section": "section_sap_integration",
                "requires_config": True,
                "config_fields": ["sap_version", "sap_modules"],
                "impacts": ["success_contract", "sow", "solution_design"]
            },
            "email": {
                "name": "Email Integration",
                "description": "Receive documents via email",
                "template_section": "section_email",
                "impacts": ["sow", "solution_design"]
            },
            "vendor_portal": {
                "name": "Vendor Portal Integration",
                "description": "Connect to vendor submission portal",
                "template_section": "section_vendor_portal",
                "impacts": ["sow", "solution_design"]
            },
            "archive": {
                "name": "Archive System",
                "description": "Connect to document archive system",
                "template_section": "section_archive",
                "impacts": ["solution_design"]
            },
            "payment_system": {
                "name": "Payment System Integration",
                "description": "Connect to payment processing system",
                "template_section": "section_payment",
                "impacts": ["solution_design"]
            }
        }
    },
    "governance": {
        "name": "Governance & Compliance",
        "description": "Security and compliance features",
        "features": {
            "audit_trail": {
                "name": "Complete Audit Trail",
                "description": "Full logging of all processing activities",
                "template_section": "section_audit_trail",
                "impacts": ["success_contract", "solution_design"]
            },
            "rbac": {
                "name": "Role-Based Access Control",
                "description": "Granular permissions and roles",
                "template_section": "section_rbac",
                "impacts": ["solution_design"]
            },
            "gdpr": {
                "name": "GDPR Compliance",
                "description": "Data privacy and protection features",
                "template_section": "section_gdpr",
                "impacts": ["success_contract", "solution_design"]
            },
            "sox": {
                "name": "SOX Compliance",
                "description": "Financial controls and segregation of duties",
                "template_section": "section_sox",
                "impacts": ["success_contract", "solution_design"]
            },
            "multi_entity": {
                "name": "Multi-Entity Support",
                "description": "Support for multiple legal entities",
                "template_section": "section_multi_entity",
                "impacts": ["solution_design"]
            }
        }
    }
}

# Template Variables Registry
# Defines all variables that can be used in templates
TEMPLATE_VARIABLES = {
    # Basic Info
    "customer_name": {
        "description": "Customer company name",
        "type": "text",
        "required": True,
        "example": "Acme Corporation"
    },
    "project_name": {
        "description": "Project name",
        "type": "text",
        "required": True,
        "example": "AP Automation Implementation"
    },
    "project_type": {
        "description": "Type of project",
        "type": "text",
        "options": PROJECT_TYPES,
        "required": True
    },
    "industry": {
        "description": "Industry vertical",
        "type": "text",
        "required": False
    },
    "project_duration_months": {
        "description": "Project duration in months",
        "type": "number",
        "required": False
    },

    # Dates
    "go_live_date": {
        "description": "Target go-live date",
        "type": "date",
        "format": "%B %d, %Y",
        "required": False
    },
    "current_date": {
        "description": "Document generation date",
        "type": "date",
        "format": "%B %d, %Y",
        "auto_generated": True
    },

    # Stakeholders - Client
    "client_sponsor_name": {"description": "Client sponsor name", "type": "text"},
    "client_sponsor_email": {"description": "Client sponsor email", "type": "text"},
    "technical_lead_name": {"description": "Client technical lead name", "type": "text"},
    "technical_lead_email": {"description": "Client technical lead email", "type": "text"},
    "business_lead_name": {"description": "Client business lead name", "type": "text"},
    "business_lead_email": {"description": "Client business lead email", "type": "text"},

    # Stakeholders - Our Team
    "ae_name": {"description": "Account Executive name", "type": "text", "required": True},
    "ae_email": {"description": "Account Executive email", "type": "text", "required": True},
    "sa_name": {"description": "Solutions Architect name", "type": "text", "required": True},
    "sa_email": {"description": "Solutions Architect email", "type": "text", "required": True},
    "pm_name": {"description": "Project Manager name", "type": "text"},
    "pm_email": {"description": "Project Manager email", "type": "text"},

    # Technical Scope
    "estimated_document_volume_monthly": {
        "description": "Estimated monthly document volume",
        "type": "number"
    },
    "primary_erp_system": {
        "description": "Primary ERP system",
        "type": "text"
    },

    # Success Metrics
    "overall_accuracy_target": {
        "description": "Overall accuracy target percentage",
        "type": "number",
        "format": "%.1f%%"
    },
    "processing_speed_target": {
        "description": "Target processing speed",
        "type": "text"
    },

    # Derived/Complex Fields
    "document_types_list": {
        "description": "Comma-separated list of document types",
        "type": "text",
        "derived": True
    },
    "document_types_table": {
        "description": "Table of document types with accuracy targets",
        "type": "table",
        "derived": True
    },
    "core_capabilities_list": {
        "description": "Bulleted list of core capabilities",
        "type": "list",
        "derived": True
    },
    "integration_summary": {
        "description": "Summary of system integrations",
        "type": "text",
        "derived": True
    },
    "compliance_list": {
        "description": "List of compliance requirements",
        "type": "list",
        "derived": True
    },

    # Boolean Flags (for conditional sections)
    "has_sap_integration": {
        "description": "Whether SAP integration is included",
        "type": "boolean",
        "derived": True
    },
    "has_email_integration": {
        "description": "Whether email integration is included",
        "type": "boolean",
        "derived": True
    },
    "has_matching": {
        "description": "Whether 2-way or 3-way matching is enabled",
        "type": "boolean",
        "derived": True
    },
    "has_line_items": {
        "description": "Whether line item extraction is enabled",
        "type": "boolean",
        "derived": True
    },

    # Configuration fields
    "sap_version": {
        "description": "SAP version (e.g., ECC 6.0, S/4HANA)",
        "type": "text",
        "derived": True
    },
    "sap_modules": {
        "description": "SAP modules (e.g., FI, MM, CO)",
        "type": "text",
        "derived": True
    }
}
