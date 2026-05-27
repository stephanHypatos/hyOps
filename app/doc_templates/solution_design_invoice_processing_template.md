## Placeholder Reference List:

| Type          | Placeholder name                                                          | Link |
| ------------- | ----------------------------------------------------------------------- | ---- |
| handbooklink       | [LINK: HYPATOS Studio Login]                                            |      |
| handbooklink       | [LINK: HYPATOS Insights Login]                                          |      |
| handbooklink       | [LINK: HYPATOS Insights Tool]                                           |      |
| handbooklink       | [LINK: Studio Docs - User Creation]                                     |      |
| handbooklink       | [LINK: Studio Docs - Password Reset]                                    |      |
| handbooklink       | [LINK: Studio Docs - User Management]                                   |      |
| handbooklink       | [LINK: Studio Docs - Master Data Enrichment]                            |      |
| handbooklink       | [LINK: Studio Docs - Composite Enrichment]                              |      |
| handbooklink       | [LINK: Studio Docs - SAP Master Data Integration Configuration]         |      |
| handbooklink       | [LINK: Studio Docs - SAP Integration]                                   |      |
| handbooklink       | [LINK: AWS SES TLS Encryption Documentation]                            |      |
| handbooklink       | [LINK: Microsoft Exchange TLS Encryption Documentation]                 |      |
| handbooklink       | [LINK: Microsoft Exchange Attachment Type Classification Documentation] |      |
| handbook link | [LINK: HYPATOS Customer Handbook]                                       |      |
| handbooklink       | [LINK: HYPATOS Customer Care Portal]                                    |      |
| doclink       | [DOC: Technical Kick-Off Meeting]                                       |      |
| doclink       | [DOC: Requirements Workbook]                                            |      |
| doclink       | [DOC: Technical Workshop SAP]                                           |      |
| doclink       | [DOC: Datapoint List]                                                   |      |
| doclink       | [DOC: Statement of Work Annex]                                          |      |
| doclink       | [DOC: Studio Projects List]                                             |      |
| doclink       | [DOC: Cut-Over Plan]                                                    |      |
| doclink       | [DOC: Cut-Over Plan]                                                    |      |
| emaillink       | [EMAIL: HYPATOS Supporr lan]                                                    |      |

# Solution Design Document

## Introduction

The Solution Design Document (SDD) describes the proposed solution's design and technical approach. It serves as a reference for how the solution will be built, implemented, and maintained.

The SDD provides a shared understanding for all project stakeholders by outlining the solution's structure, functionality, and key technical considerations. It acts as a guiding document during implementation and as a reference for future operations, maintenance, and enhancements, ensuring alignment with business requirements and informed decision-making.

### References

| Document Name | Location |
|--------------|----------|
| Kick-off slide-deck | [DOC: Technical Kick-Off Meeting] |

---

## Business Requirements

Describes the specific business needs and objectives that the solution intends to address. This section may include functional and non-functional requirements, constraints, dependencies, and any relevant industry standards or regulations.

### References

| Document Name | Location |
|--------------|----------|
| Process Observation Workshop | [DOC: Requirements Workbook] |
| Technical Assessment Workshop | [DOC: Technical Workshop SAP] |

---

## Scope

### Documents in Scope

| Countries            |
|----------------------|
| {{go_live_regions}}  |

### Document Types

{{#document_processing}}
**Document Types:**
{{#document_processing_list}}
- {{feature_name}}
{{/document_processing_list}}
{{/document_processing}}

---

## Solution Overview - Features

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

---

## System Architecture

Hypatos will deploy a dedicated Hypatos Environment that has its own unique Id, Name, Database and API credentials.
A full list can be found in the document:


### References

| Document Name   | Location |
|-----------------|----------------------------------------|
| Studio Projects | [DOC: Studio Projects List] |
| Email Service | Email Service |
| REST API | HYPATOS REST API (redoc.ly) |
| SAP Connector | [LINK: Studio Docs - SAP Integration] |

---

## Application Components

Provides detailed descriptions of each technical component of the solution. This includes software, databases, APIs, and third-party integrations. It may specify the versions, configurations, and any customization or development requirements for each component.

{{application_components_sections}}

---

## Data Points

The following chapter describes the data points that HYPATOS will generate for document creation in ERP / SAP.

Reference: [DOC: Datapoint List SAP Addon]

---

## Custom Requirements

All custom/project specific requirements that deviating from the HYPATOS Standard Accounts Payable document Processing Workflow are documented the following sheet:

Reference: [DOC: Requirements Workbook] Sheet: "Special Documents"

---

## System Integration

Outlines the integration with external systems, such as the SAP Add-on data flows, integration services, and required databases. It specifies the protocols, data formats, security considerations, and any transformation or mapping requirements for data exchange.

{{system_integration_sections}}

---

## Monitoring and Reporting

Outlines the strategies and tools that will be used to monitor and report on the performance and health of the implemented solution. It focuses on ensuring the availability, reliability, and efficiency of the system, as well as providing valuable insights for decision-making and optimization.

### Requirements

| Requirement | Description |
|-------------|-------------|
| Reporting, including total amount of documents processed pre-filled fully automatically | A tool that displays Key Performance Indicators related to document processing in HYPATOS.<br>A tool that validates what data has been sent to and received from the ERP system in order to simplify incident handling.<br>A tool that validates what data has been sent to and received from the ERP system in order to simplify incident handling. |
| Monitoring of | Based on inbound channels (= projects)<br>Based on usernames or IDs<br>Based on specified time periods or point in time<br>Based on supplier IDs or other datapoints defined in the datapoint requirements list<br>Based on metadata<br>Based on document status (e.g., Auto-completed, manually completed, transferred, transfer failed, etc.) |

### Solution

| Requirement | Solution |
|-------------|----------|
| The tool provides functionality to validate what data has been sent to and received from the ERP system in order to simplify incident handling. | **HYPATOS Insights BI Platform:** Insights builds the foundation for our reporting dashboards. Insights is a business intelligence tool known for its flexibility and ease of use. It enables us to create powerful and user-friendly dashboards that cater to various reporting requirements.Filtering is done on: Based on inbound channels (= projects) Based on usernames or IDs Based on specified time periods or point in time Based on supplier IDs or other datapoints defined in the datapoint requirements list Based on metadata Based on document status (e.g., Auto-completed, manually completed, transferred, transfer failed, etc.)**Metrics:** Auto-Completion Rate (= no human intervention required) Straight-through-processing (STP) Rate. This represents the percentage of documents processed straight through the system from start to finish (without any manual intervention). It is a critical metric for understanding the system's ability to handle documents autonomously. Field level accuracy rate (average rate of correctly captured cases divided by all cases on a field level for a specified period of time)Each dashboard's reports can be downloaded, with a limitation of up to 10,000 lines. If larger reports need to be downloaded this would require a custom query which is out of scope until requested separately. In addition to the standard dashboard, it is possible to create custom queries on top of the given data (such as positions per document and others) |
| A tool that validates what data has been sent to and received from the ERP system in order to audits handling. | HYPATOS insights provides a full audit trail including timestamps. |

### References

| Document Name | Location |
|--------------|----------|
| HYPATOS Insights tool | [LINK: HYPATOS Insights Tool] |
| Statement of Work | [DOC: Statement of Work Annex] |
| Functional Requirements | [DOC: Datapoint List SAP Addon] |
| Functional Requirements | [DOC: Requirements Workbook] |

---

## Implementation and Deployment

Describes the deployment architecture, installation procedures, configuration steps, and any dependencies or prerequisites for deploying the solution. It may also include a rollout plan and strategies for data migration or system cutover.

### Functional Design Specification

Each Hypatos environment ( TEST & PROD ) will be connected to the Q and PROD environment of the ERP target system.

**TEST**
- Environment responsible for the implementation of project scope
- Connected with TEST/Non-PROD environment
- Multiple test projects
- Multiple users

**PROD**
- Environment responsible to receive new AP documents from suppliers throughout the predefined queues
- Connected with PROD environment
- Only document inbound/outbound projects
- Restricted users with assigned seat in HY Studio

The implementation and further validation of project scope must be done in the TEST environment. After SIT and UAT being confirmed, HY COE team will be responsible to set up PROD environment with the latest configurations applied in the TEST environment.

Further developments must follow the same flow. Any change request or bug fixing will be performed first in the TEST environment. After confirmation of test results, HY team will ensure the synchronization from TEST to PROD.

No data (= document) will be moved from TEST to PROD. It means the test documents will not be moved to PROD. However, for testing purpose and potentially fix an issue or implement a new change request, a PROD document might be moved to TEST project. A PROD document might also be moved to TEST environment for QA or training purpose.

### Technical Design Specification

**Studio Schema Management**

HYPATOS will maintain a centralized repository for schemas, organized on a client and project basis.

This repository will house up to ten versions of the most recent schemas, regularly updated from HYPATOS' Center of Excellence (COE).

Additionally, the repository will store up to 3 versions of schemas that have been updated through the user interface (UI) and differ from the existing schemas. Please note that the schema is only saved once per day at end of day.

**AI Models Deployment**

AI model deployments are manual as soon as the Model QA phase is completed.

- For new projects, both customer and HYPATOS can assign an available model as per requirements
- For changing a model in an existing project, a service desk ticket needs to be raised for updating the model via HYPATOS backend.

**Studio Schema Deployment**

The deployment of schemas from the testing environment to the production environment follows an internal automated process, which can also accommodate bulk deployments when necessary.

A rollback feature for schemas will be accessible exclusively for internal use within HYPATOS.

### References

| Document Name | Location |
|--------------|----------|
| Roll-out/Cut-over plan | [DOC: Cut-Over Plan] |

---

## Maintenance and Support

Outlines the ongoing maintenance, monitoring, and support requirements for the solution. It may include details on bug tracking, change management, version control, and system documentation.

### References

| Document Name | Location |
|--------------|----------|
| Change Request Form | |
| Customer handbook | [LINK: HYPATOS Customer Handbook] |
| HYPATOS Customer Care Portal | [LINK: HYPATOS Customer Care Portal] |
| Support by email | [EMAIL: HYPATOS Support] |
