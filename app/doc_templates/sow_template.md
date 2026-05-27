# Statement of Work
## {{customer_name}} ({{customer_acronym}})
### {{project_name}}

**Document Version:** 1.0
**Date:** {{current_date}}
**Project Type:** {{project_type}}

---

## 1. Project Overview

**Customer:** {{customer_name}}
**Industry:** {{industry}}

{{#company_overview}}
**Company Background:**
{{company_overview}}
{{/company_overview}}

{{#project_background}}
**Project Background and Goals:**
{{project_background}}
{{/project_background}}


**Current Solution** 
Today, traditional Optical Character Recognition (OCR) and Robotic Process Automation (RPA) solutions are used for document processing and validation. These documents are then processed through existing enterprise management systems and workflows. However, this solution architecture does not achieve the currently expected higher level of automation using the latest technologies, such as Large Language Models (LLMs) and AI Agent frameworks.

**Expected Solution** 
The future solution leverages state-of-the-art technologies such as Large Language Models (LLMs), Retrieval-Augmented Generation (RAG) using a private knowledge base, and an AI Agent framework. This modern approach enables end-to-end automation of key document processing tasks, significantly accelerating workflows, reducing the volume of documents requiring manual intervention, and increasing data consistency through standardized task execution. Compared to the current OCR and RPA-based setup, this architecture delivers a higher degree of automation and operational efficiency by embedding AI capabilities directly into the process.


## 2. Use Case & Scope

{{#use_cases}}
### 2.1 Use Case to be Automated

- **{{use_cases}}**
{{/use_cases}}

### 2.2 Solution Scope & Description

#### 2.2.1 High Level Solution Description
* All documents for the regions or entities in scope will be routed to the AI processing platform. The AI Agent will autonomously perform all relevant processing tasks, including classification, data extraction, validation against master data, normalization, and compliance checks for the defined document types.

* Processed documents will be handled as follows based on project type:
  * **a. Pilot Project:** All documents processed in the background—either fully or partially—will be handed over to the ERP system for further processing and integration into existing workflows.
  * **b. Custom Demo or POC Project:** All documents processed in the background—either fully or partially—will be made available in the AI Platform User Interface (Hypatos Studio) for review and validation.

#### 2.2.2 Features and capabilities

The following features and capabilities are included in this project:

{{#professional_services}}
**Professional Services:**
{{#professional_services_list}}
- {{feature_name}}
{{/professional_services_list}}
{{/professional_services}}

{{#hypatos_studio}}
**Hypatos Studio:**
{{#hypatos_studio_list}}
- {{feature_name}}
{{/hypatos_studio_list}}
{{/hypatos_studio}}

{{#hypatos_insights}}
**Hypatos Insights:**
{{#hypatos_insights_list}}
- {{feature_name}}
{{/hypatos_insights_list}}
{{/hypatos_insights}}

{{#document_processing}}
**Document Processing:**
{{#document_processing_list}}
- {{feature_name}}
{{/document_processing_list}}
{{/document_processing}}

{{#translation_ai}}
**Translation AI:**
{{#translation_ai_list}}
- {{feature_name}}
{{/translation_ai_list}}
{{/translation_ai}}

{{#data_enrichment}}
**Data Enrichment:**
{{#data_enrichment_list}}
- {{feature_name}}
{{/data_enrichment_list}}
{{/data_enrichment}}

{{#integration}}
**Integration:**
{{#integration_list}}
- {{feature_name}}
{{/integration_list}}
{{/integration}}

{{#archiving}}
**Archiving:**
{{#archiving_list}}
- {{feature_name}}
{{/archiving_list}}
{{/archiving}}

## 3. Project Timeline & Milestones

**Earliest Project Start Date:** {{project_start_date}}
**Target Go-Live Date:** {{go_live_date}}

{{#go_live_regions}}
**Go-Live Region(s):** {{go_live_regions}}
{{/go_live_regions}}



## Timeline by Project Type

| Milestone | DEMO | POC | PILOT |
|-----------|------|-----|-------|
| Technical (PRE-)Kickoff Workshop | N/A | N/A | N/A |
| Data Transfer Confirmation | Week 1 | Week 1 | Week 1-2 |
| Business Kickoff Workshop | Week 2 | Week 2 | Week 2-3 |
| Solution Design Sign-Off | N/A | N/A | Week 3-4 |
| Studio Configured | Week 3 | Week 3 | Week 4-5 |
| Integration Configured | N/A | N/A| Week 5-6 |
| User Training Completed | Week 3 | Week 3 | Week 6-7 |
| UAT Approved & Go-Live (or Pilot) Decision | Week 4 | Week 4 | Week 7-8 |
| Hypercare Closing & Handover to Customer Care | N/A | N/A | Week 8-10 |

**Total Duration:** 
- **DEMO:** ~4 weeks
- **POC:** ~4 weeks  
- **PILOT:** ~8-10 weeks

## 4. Success Criteria & Exit Criteria

The project will be considered successful when the following criteria are met:

{{#success_criteria_list}}
### 4.{{index}} {{criterion_name}}

{{criterion_definition}}

{{/success_criteria_list}}

{{#success_criteria_custom}}
### Additional Criteria

{{success_criteria_custom}}
{{/success_criteria_custom}}

## 5. Deliverables

The following deliverables are required to achieve the success criteria:

{{#deliverables}}
| Deliverable | Description | Owner |
|-------------|-------------|-------|
{{#deliverables_list}}
| {{deliverable_name}} | {{deliverable_description}} | {{deliverable_owner}} |
{{/deliverables_list}}
{{/deliverables}}

{{#is_pilot}}
## 6. Technical Integration

**Target ERP System:** {{target_erp}}

{{#current_workflow}}
**Current Workflow Solution:** {{current_workflow}}
{{/current_workflow}}

{{#integration}}
**Integration Points:**
{{#integration_list}}
- {{feature_name}}
{{/integration_list}}
{{/integration}}

**User Interface:** {{user_interface}}

{{/is_pilot}}
## 7. Project Stakeholders

### 7.1 {{customer_name}} Team

{{#project_sponsor_name}}
**Project Sponsor:**
- Name: {{project_sponsor_name}}
{{#project_sponsor_email}}- Email: {{project_sponsor_email}}{{/project_sponsor_email}}
{{/project_sponsor_name}}

{{#project_lead_name}}
**Project Lead:**
- Name: {{project_lead_name}}
{{#project_lead_email}}- Email: {{project_lead_email}}{{/project_lead_email}}
{{/project_lead_name}}

{{#business_lead_name}}
**Business Lead:**
- Name: {{business_lead_name}}
{{#business_lead_email}}- Email: {{business_lead_email}}{{/business_lead_email}}
{{/business_lead_name}}

{{#technical_lead_name}}
**Technical Lead:**
- Name: {{technical_lead_name}}
{{#technical_lead_email}}- Email: {{technical_lead_email}}{{/technical_lead_email}}
{{/technical_lead_name}}

{{#ap_accountants_lead_name}}
**AP Accountants Lead:**
- Name: {{ap_accountants_lead_name}}
{{#ap_accountants_lead_email}}- Email: {{ap_accountants_lead_email}}{{/ap_accountants_lead_email}}
{{/ap_accountants_lead_name}}

### 7.2 Hypatos Team

{{#ae_name}}
**Account Executive:**
- Name: {{ae_name}}
{{#ae_email}}- Email: {{ae_email}}{{/ae_email}}
{{/ae_name}}

{{#sa_name}}
**Solutions Architect:**
- Name: {{sa_name}}
{{#sa_email}}- Email: {{sa_email}}{{/sa_email}}
{{/sa_name}}

{{#pm_name}}
**Project Manager:**
- Name: {{pm_name}}
{{#pm_email}}- Email: {{pm_email}}{{/pm_email}}
{{/pm_name}}

{{#csm_name}}
**Customer Success Manager:**
- Name: {{csm_name}}
{{#csm_email}}- Email: {{csm_email}}{{/csm_email}}
{{/csm_name}}

## 8. Project Delivery & PMO Services

### 8.1 Project Management

Hypatos will provide comprehensive project management services including:

- Project planning and scheduling
- Regular status updates and reporting
- Risk and issue management
- Change request management
- Stakeholder communication and coordination

### 8.2 Project Language & Documentation

**Language Requirements:** {{language_constraints}}

{{#is_german}}
_Note: German language requirements may impact project costs and timeline. All project documentation and meetings will be conducted in German as requested._
{{/is_german}}
{{^is_german}}
All project documentation, meetings, and materials will be provided in English.
{{/is_german}}

{{#project_risks}}
## 9. Project Risks & Mitigation

{{project_risks}}
{{/project_risks}}


## 10. Learning Portal - Hypatos Academy 

Hypatos will grant access to the Hypatos Learning Portal based on the number of licensed users. The Learning Portal offers on-demand, accessible training for the Hypatos Platform 


## 11. Prerequisites
To ensure successful project implementation and optimal platform performance, the following prerequisites must be met:

### Data Access and System Integration
{{customer_name}} must provide access to the relevant data at the beginning of the project, or Hypatos must be permitted to install the certified connctor (SAP Conector, Coupa Connector, Cloud Connector, etc.) on the target ERP system.

### Document Submission Standards
To achieve the expected automation performance and maintain document integrity, the following conditions are required:

File Quality: Scanned documents must meet a minimum resolution of 300–600 dpi to support accurate data extraction.
File Format: Documents must be provided in the filetypes, that the Hypatos Platform supports.
File Size: Email attachments must not exceed 40 MB and must be submitted as file attachments, not embedded in the email body.
Document Integrity: Documents must be complete, unaltered, and untruncated, with no encryption, or restrictive security settings.
PDF Compatibility: PDFs containing dynamic content (e.g., active fields, XFA form data, markups, sticky notes) cannot be processed correctly and must be excluded.

These prerequisites are essential for the Hypatos platform to function as intended and achieve the anticipated automation outcomes.

---

## Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Customer Sponsor | | | |
| Hypatos Account Executive | | | |
| Hypatos Solutions Architect | | | |

---

---
# Appendix - Change Order Form

## 1. Introduction

A change order documents any changes to the resource requirements, engagement scope, or schedule that materially change Hypatos' estimated fees and must be mutually agreed by the parties ("Change Order"). A Change Order will require a review of the SOW and financial arrangements as follows:

1. Each party must mutually agree to any changes to the SOW scope or deliverables and review the workday impact. Hypatos will determine the cost impact based on the additional work required.
2. Any mutually agreed and approved changes to the SOW scope or deliverables will be reflected in addenda to this SOW, or in a new SOW, which shall be duly executed by each party.
3. Changes will only be accepted in writing according to the Change Order process. Verbal changes are not accepted as formal approved changes.

## 2. Change Request Process

All significant changes must be documented using the Change Order Form, which ensures mutual agreement among the parties. The Change Order serves as a contractual amendment to this SOW and must be approved in writing by both parties before any changes are implemented.

---

## Change Order Form

| Field | Value |
|-------|-------|
| **Change Order Number** | |
| **Change Order Date** | |
| **Requester Name** | |
| **Requester Title** | |
| **SOW Name/Reference #/Date** | |
| **PO Number** | |

### {{customer_name}} Project Manager

- **Name:** _______________________________
- **Email:** _________________________________________


### Hypatos Project Manager

- **Name:** ________________________________________
- **Email:** _________________________________________

---

**Cost Change:** Yes ☐ No ☐  
**If Yes, how much:** $______ (Not to exceed amount of Change Order)

---

Upon execution by the Parties, this change order ("Change Order") will become part of the Statement of Work referenced above ("SOW") pursuant to the agreement referenced above ("Agreement"). All Services and Deliverables provided pursuant to this Change Order will be subject to the terms and conditions of the SOW and the Agreement. All undefined terms will have the meanings set forth in the SOW and Agreement.

---

### Detailed Description of Change

**Reason for Change/Impact of not changing:**

---

### New or Changed Resources

| Change Item | Change Reason | Impact on Resources and/or Deliverables | Impact on Cost (Fees and Expenses) | Impact on Schedule and Other Tasks |
|-------------|---------------|----------------------------------------|-----------------------------------|-----------------------------------|
| | | | | |
| | | | | |
| | | | | |

---

**ACCEPTED AND AGREED TO THIS ___ day of ___________, 20__**
---


_Generated by Hypatos Onboarding Automation System on {{generated_timestamp}}_
