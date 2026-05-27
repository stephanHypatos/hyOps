## Placeholder Reference List:

[LINK: HYPATOS Studio Login]
[LINK: HYPATOS Insights Login]
[LINK: HYPATOS Insights Tool]
[LINK: Studio Docs - User Creation]
[LINK: Studio Docs - Password Reset]
[LINK: Studio Docs - User Management]
[LINK: Studio Docs - Master Data Enrichment]
[LINK: Studio Docs - Composite Enrichment]
[LINK: Studio Docs - SAP Master Data Integration Configuration]
[LINK: Studio Docs - SAP Integration]
[LINK: AWS SES TLS Encryption Documentation]
[LINK: Microsoft Exchange TLS Encryption Documentation]
[LINK: Microsoft Exchange Attachment Type Classification Documentation]
[LINK: HYPATOS Customer Handbook]
[LINK: HYPATOS Customer Care Portal]

[DOC: Technical Kick-Off Meeting]
[DOC: Requirements Workbook]
[DOC: Technical Workshop SAP]
[DOC: Datapoint List]
[DOC: Statement of Work Annex]
[DOC: Studio Projects List]
[DOC: Cut-Over Plan]

[EMAIL: HYPATOS Support]

# Solution Design Document

## 1. Introduction

The Solution Design Document (SDD) describes the proposed solution’s design and technical approach. It serves as a reference for how the solution will be built, implemented, and maintained.

The SDD provides a shared understanding for all project stakeholders by outlining the solution’s structure, functionality, and key technical considerations. It acts as a guiding document during implementation and as a reference for future operations, maintenance, and enhancements, ensuring alignment with business requirements and informed decision-making.

### References

| Document Name | Location |
|--------------|----------|
| Kick-off slide-deck | [DOC: Technical Kick-Off Meeting] |

---

## 2. Business Requirements

Describes the specific business needs and objectives that the solution intends to address. This section may include functional and non-functional requirements, constraints, dependencies, and any relevant industry standards or regulations.

### References

| Document Name | Location |
|--------------|----------|
| Process Observation Workshop | [DOC: Requirements Workbook] |
| Technical Assessment Workshop | [DOC: Technical Workshop SAP] |

---

## 3. Scope

### Documents in Scope 

| Countries            | 
|----------------------|
| {{go_live_regions}}  | 

### Document Types 

{{#document_types}}
**Document Types:**
{{#document_types_list}}
- {{document_name}} 
{{/document_types_list}}
{{/document_types}}

---

## 4. Solution Overview - Features

The following features and capabilities are included in this project:

{{#core_features}}
**Core Capabilities:**
{{#core_features_list}}
- {{feature_name}}
{{/core_features_list}}
{{/core_features}}

{{#validation_features}}
**Validation Features:**
{{#validation_features_list}}
- {{feature_name}}
{{/validation_features_list}}
{{/validation_features}}

{{#integrations}}
**System Integrations:**
{{#integrations_list}}
- {{integration_name}}
{{/integrations_list}}
{{/integrations}}

{{#governance_features}}
**Governance & Compliance:**
{{#governance_features_list}}
- {{feature_name}}
{{/governance_features_list}}
{{/governance_features}}

---

## 5. System Architecture

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

## 6. Application Components

Provides detailed descriptions of each technical component of the solution. This includes software, databases, APIs, and third-party integrations. It may specify the versions, configurations, and any customization or development requirements for each component.

## 6.1 Studio User Management

### Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| User access management | Users must be able to access HYPATOS Studio based on assigned roles and company affiliation. | Must |
| Single sign-on (SSO) | User authentication must be performed via an enterprise single sign-on mechanism. | Must |
| Role-based access | Different user roles must be supported to control permissions and responsibilities. | Must |
| Access audit logging | All login attempts and user access activities must be logged for audit purposes. | Must |
| Secure authentication | Authentication and authorization must follow industry security standards. | Must |

### Solution

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| User access management | Users are created and assigned to a HYPATOS Studio company via the HYPATOS Studio user interface, including role assignment. | Customer |
| Single sign-on (SSO) | HYPATOS Studio integrates with an enterprise SSO solution using SAML-based authentication. | HYPATOS |
| Role-based access | Access permissions are managed via predefined roles configurable in HYPATOS Studio by admin users. | HYPATOS |
| Access audit logging | All successful and failed access attempts are logged with user identification, timestamp, IP address, and actions performed. | HYPATOS |
| Secure authentication | Authentication is handled via a centralized identity provider with configuration managed through controlled change processes. | HYPATOS |

### Description

User access to HYPATOS Studio is managed through user provisioning combined with single sign-on authentication.  
Users must first be created and associated with the relevant HYPATOS Studio company, including role assignment. Authentication is then performed via the configured enterprise SSO solution.

User creation and maintenance are managed by designated customer administrators through an internal request process. Upon creation, users receive an invitation email to join the HYPATOS Studio company.

During login, users enter their email address on the HYPATOS Studio login page. Based on the email domain, the user is redirected to the enterprise SSO platform for authentication and, upon success, redirected back to HYPATOS Studio.

Access to HYPATOS Insights is managed separately and granted by HYPATOS administrators based on approved access requests and assigned roles.

---

## 6.2 Studio User Roles & Responsibilities

### Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Role-based permissions | The system must support role-based access to control user permissions. | Must |
| Separation of responsibilities | User roles must reflect operational, supervisory, and administrative responsibilities. | Must |
| Project-level access | Access to projects and data must be restricted based on assigned roles. | Must |
| Administration capabilities | Administrative roles must be able to manage users, projects, and system configuration. | Must |

### Solution

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Role-based permissions | HYPATOS provides predefined application roles for Studio and Insights. | HYPATOS |
| Separation of responsibilities | Each role has clearly defined permissions aligned with operational and governance needs. | HYPATOS |
| Project-level access | Access to projects, queues, and data is controlled via role and project assignment. | HYPATOS |
| Administration capabilities | Admin users can manage users, roles, projects, and configuration via the HYPATOS user interface. | HYPATOS |

### Roles & Responsibilities

| Application | Application Role | Typical User Roles | Responsibilities |
|-------------|-----------------|-------------------|------------------|
| HYPATOS Studio | Clerk | Data Entry Clerk | - View assigned projects Process documents Escalate unresolved cases Filter processing queues |
| HYPATOS Studio | Clerk | Business Owner | - View assigned projects Filter processing queues |
| HYPATOS Studio | Manager | Data Entry Manager<br>Product Owner | - Review documents Resolve cases, including bypassing validation rules Manage projects and users |
| HYPATOS Studio | Admin | Application Admin<br>Development Users | - Create, edit, and delete projects Manage users and roles Configure datapoint schemas |
| HYPATOS Insights | Analyst | Business Analyst<br>Business Owner<br>Product Owner | - View and filter reports Download reporting results |
| HYPATOS Insights | Admin | Application Admin<br>Development Users | - Create, edit, and delete dashboards Manage reports and analytics configuration |

#### References

| Document Name | Location |
|--------------|----------|
| User Roles & Responsibilities | [LINK: Studio Docs - User Management] |
| Statement of Work | [DOC: Statement of Work Annex] |
| Functional Requirements | [DOC: Datapoint List SAP Addon] |
| Functional Requirements | [DOC: Requirements Workbook] |

### 6.3 Document Input

#### Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Manual upload | document can be uploaded manually to HYPATOS. | Must |
| Upload via email | documents attached to an email are uploaded to HYPATOS automatically upon receival of the email. | Must |
| Attachment processing | The following attachment types are processed by HYPATOS for the creation of a document: pdf, jpeg, png, tiff, xml | Must |
| Email body processing | HYPATOS considers all information from the content of the email. If an email without attachments is received, HYPATOS does not process the provided email. | Must |
| Out-of-scope documents | Documents that are not in scope are not transferred to the the downstream system. | Must |

#### Solution

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Manual upload | Users upload documents to HYPATOS Studio via their browser. | Hy |
| Upload via email | Forwarding rule is configured for upload of emailed documentss | {{customer_name}} |
| Attachment processing | HYPATOS creates a single document per received email. The information from all attachments is considered during processing. | Hy |
| Email body processing | HYPATOS only processes emails with attachments as a single document. Information from the email body can be used for extraction and enrichment purposes. | Hy |
| Out-of-scope documents | HYPATOS will route out-of-scope documents to a dedicated HYPATOS Studio project that is not integrated with the downstream system. | Hy |

### 6.4 Document Extraction

#### Requirements

| Requirement | Description |
|-------------|-------------|
| Extraction of document data | [DOC: Datapoint List SAP Addon] |
| Continuous improvement of extraction | Extraction quality improves over time based on user training. |

#### Solution Design

| Description | Solution |
|-------------|----------|
| Extraction of document data | HYPATOS will extract all required data points using AI capabilities. The extraction is supported by prompt instructions to increase extraction quality. |
| Continuous improvement of extraction | ERP key users gain access to HYPATOS Studio for labelling of trouble-maker documents from key customers. Prompts can continuously be improved with additional instructions to further improve extraction accuracy. |

### 6.5 Document Enrichment

This chapter describes all features related to the enrichment of documentdata.

#### Company Master Data Enrichment

**Requirements**

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Company Code enrichment | Enrichment of the company Code to the document based on SAP master data. | Must |
| Company Code data synching | Enrichment of Company Code data takes place on data that is updated daily from the ERP. | Must |
| Handling of non-existing Company Codes | documentss by suppliers without any master data record reach the ERP workflow. | Must |

**Solution Design**

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Company Code enrichment | HYPATOS uses extracted recipient data (from document) and the document layout to enrich the correct SAP ID of the company Code to the document header. | Hy |
| Company Code data synching | HYPATOS SAP Connector transfers required SAP company master data to HYPATOS cloud on a daily basis | Hy |
| Handling of non-existing Company Codes | In the case that no matching company code could be enriched, HYPATOS does not provide the ID of the company. The document is still created in the ERP. The assignment of the document to the correct company code is done manually. | Hy |

**References**

| Document Name | Location |
|--------------|----------|
| Master Data Enrichment Approach | [LINK: Studio Docs - Master Data Enrichment] |
| Composite Enrichment | [LINK: Studio Docs - Composite Enrichment] |
| HYPATOS SAP Connector, Master Data Integration | [LINK: Studio Docs - SAP Master Data Integration Configuration] |

#### Supplier Master Data Enrichment

**Requirements**

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Supplier Master Data enrichment | Enrichment of the Supplier Master data to the document based on SAP master data. | Must |
| Supplier Master data synching | Enrichment of Supplier Master data takes place on data that is updated daily from SAP. | Must |
| Handling of non-existing Supplier Master data | documentss by suppliers without any master data record reach the ERP workflow. | Must |

**Solution Design**

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Supplier Master data enrichment | HYPATOS uses extracted sender data (from document) and the document layout to enrich the correct SAP ID of the supplier the documents header. | Hy |
| Supplier Master data synching | HYPATOS SAP Connector transfers required SAP Supplier Master data to HYPATOS cloud on a daily basis (see chapter 8.2 for further details on master data integration) | Hy |
| Handling of non-existing Supplier Master data | In the case that no matching Supplier Master data could be enriched, HYPATOS does not provide the ID of the supplier. The document is still created in ERP. The assignment of the document to the correct Supplier Master data is done manually. | Hy |

**References**

| Document Name | Location |
|--------------|----------|
| Master Data Enrichment Approach | [LINK: Studio Docs - Master Data Enrichment] |
| Composite Enrichment | [LINK: Studio Docs - Composite Enrichment] |
| HYPATOS SAP Connector, Master Data Integration | [LINK: Studio Docs - SAP Master Data Integration Configuration] |

#### PO LINE Enrichment

**Requirements**

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Purchase Order Number Matching | A Purchase Order number is detected on the processed document and validated against the purchase order data | Must |
| Purchase Order Line Matching | Purchase Order lines from purchase order data are matched to invoice items. | Must |
| Invoiced quantities | The quantity related to an invoiced product is extracted from the document. | Must |
| Invoiced Prices | The price related to an invoiced product is extracted from the document. | Must |
| Unsuccessful PO Line matching | If no matching po line could be found, extracted invoice items without a matched po line are transferred. | Must |
| PO data synching | Purchase Order Data matching takes place on data that is updated daily from SAP. | Must |

**Solution Design**

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Purchase Order Number Matching | HYPATOS matches extracts a purchase order number by a given and valid PO Number pattern and validates the extracted Purchase Order against the given Purchase Order Master Data. (SAP EKKO – EBELN) | Hy |
| Purchase Order Line Matching | HYPATOS matches the purchase order line to the extracted document line items based on extracted document item details (material numbers, descriptions, quantities etc.). PO line items with a match, are enriched with the SAP EKPO ID (EBELP). | Hy |
| Invoiced quantities | HYPATOS extracts the invoiced quantity of each item. | Hy |
| Invoiced Prices | In case of a price deviation between the invoiced item and the matched PO LINE item, HYPATOS transfers the prices of the PO LINE. | Hy |
| Unsuccessful PO Line matching | HYPATOS transfers extracted purchase order number (SAP EKKO – EBELN) to ERP.<br>HYPATOS transfers extracted document items excluding SAP EKPO ID (EBELP) to ERP. | Hy |
| PO data synching | HYPATOS SAP Connector transfers required SAP Purchase Order Data to HYPATOS cloud on a daily basis (see chapter 8.2 for further details on master data integration) | Hy |

#### Accounting Coding GL Account Enrichment

**Requirements**

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Creation of GL Line for FI Invoices including: GL Account | The uploaded invoice (invoiceType: NON-PO (FI)) is enriched with a GL Account. | Must |
| GL Account master & posting data synching | GL Account enrichment takes place on data that is updated daily from SAP. | Must |

**Solution Design**

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Creation of GL Line for FI Invoices including: GL Account | HYPATOS enriches accounting attributes – GL Account - to incoming invoice documents based on historical data that is stored in SAP (BSEG&BKFP) and the contextual understanding of the items invoiced on the processed document. It also uses accounting guidelines (Chart of Accounts and description) to enrich invoice documents with no historical data available. | Hy |
| GL Account master & posting data synching | HYPATOS SAP Connector transfers required master and posting to HYPATOS cloud on a daily basis (see chapter 8.2 for further details on master data integration) | Hy |

#### Accounting Coding Cost Center Enrichment

**Requirements**

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Creation of GL Line for FI Invoices including: Cost Center | The uploaded document (invoiceType: NON-PO (FI)) is enriched with a Cost Center. | Must |
| Cost Center master & posting data synching | Cost Center enrichment takes place on data that is updated daily from SAP. | Must |

**Solution Design**

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Creation of GL Line for FI Invoices including: Cost Center | HYPATOS enriches accounting attributes – cost center - to incoming documents based on historical data that is stored in SAP (BSEG&BKFP) and the contextual understanding of the items invoiced on the processed document. | Hy |
| Cost Center master & posting data synching | HYPATOS SAP Connector transfers required master and posting to HYPATOS cloud on a daily basis (see chapter 8.2 for further details on master data integration) | Hy |

#### Accounting Coding Tax Code Enrichment

**Requirements**

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Tax Code enrichment | The uploaded document (invoiceType: NON-PO (FI) & PO (MM)) is enriched with a taxcode. | Must |
| Tax Code data synching | Tax Code Masterdata synch takes place on data that is created in the beginning of the project. | Must |

**Solution Design**

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Tax Code enrichment | HYPATOS enriches accounting attributes – tax code - to incoming documents based on extracted and enriched datapoints and derives the correct taxcode from a lookup table.In case of a constellation that does not exists in the lookup table the taxcode enrichment will remain empty.The relevant datapoints are: vendor.country: the country of the supplier stored in the masterdata items.taxRate: the taxrate as per item on the document items.category: the nature of the invoiced item: service | goods recipient.country: the country of the recipient extracted from the invoice items.taxExemptionIndicator: true \| false as per invoice item | Hy |
| Tax Code data synching | HYPATOS will create a lookup table containing all the relevant taxcodes as per country. | Hy |

### 6.6 Document Validation & Verification

#### Requirements

| Requirement | Solution Summary | Priority |
|-------------|------------------|----------|
| Detection of duplicate documents | HYPATOS identifies uploaded duplicate documents. | Must |
| Validation on empty data points | The user in ERP must be informed about key empty data points that need to be populated (see chapter 7 for overview on data points and validations). | Must |
| Creation and Transfer of Error Codes to SAP or to stop documents in HYPATOS Studio | HYPATOS creates Error Codes based on predefined Validation rules (among others §14 Invoice verification). HYPATOS is able to transfer error codes to ERP and or stop documents based on a defined list of Error Codes | Must |
| Document verification by end-users | Verification of documents with failed validations takes place in ERP. | Must |

#### Solution

| Requirement Description | Solution Summary | Responsible |
|------------------------|------------------|-------------|
| Detection of duplicate Orders | HYPATOS does not process the same file more than once. If a file is uploaded more than once, it runs into a processing error in HYPATOS, which will be displayed in the HYPATOS Studio UI. | Hy |
| Validation on empty data points | ERP standard functionality for highlighting missing information is used. For all information that is not covered by the ERP standard, HYPATOS will provide an error code (see chapter 7 for overview on data points and validations). | Hy |
| Creation and Transfer of Error Codes to SAP or to stop documents in HYPATOS Studio | HYPATOS will create Error Codes based on predefined Validation rules (see references). HYPATOS will transfer error codes to ERP and or stop documents based on a defined list of Error Codes. | Hy |
| Document verification by end-users | HYPATOS process all incoming documents in a fully automated way and document data is transferred to ERP after processing is completed. Error codes are handed over to ERP to make users aware of required verifications on the document (see chapter 7 for overview on data points and validations). | Hy |

#### References

| Document Name | Location |
|--------------|----------|
| ErrorCodes - Sheet | [DOC: Datapoint List SAP Addon] |

---

## 7. Data Points

The following chapter describes the data points that HYPATOS will generate for document creation in ERP / SAP.

Reference: [DOC: Datapoint List SAP Addon]

---

## 8. Custom Requirements

All custom/project specific requirements that deviating from the HYPATOS Standard Accounts Payable document Processing Workflow are documented the following sheet:

Reference: [DOC: Requirements Workbook] Sheet: "Special Documents"

---

## 9. System Integration

Outlines the integration with external systems, such as the SAP Add-on data flows, integration services, and required databases. It specifies the protocols, data formats, security considerations, and any transformation or mapping requirements for data exchange.

### 9.1 Transfer of Documents to HYPATOS

#### Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| Transfer of emailed documents to HYPATOS | In scope documents received through the email channel are transferred to HYPATOS. | Must |
| Limit transfer to company codes in scope | Only documents from countries/company codes in scope are transferred to HYPATOS. | Must |
| Limit transfer to suppliers in scope | Only documents from suppliers in scope are transferred to HYPATOS. | Must |

#### Solution

| Requirement | Solution | Responsible |
|-------------|----------|-------------|
| Transfer of emailed documents to HYPATOS | An Email forwarding rule for in scope email inboxes is configured to forward emails and their attachments to HYPATOS Studio. Forwarded emails are moved to subfolder of the email inbox. | {{customer_name}} |
| Limit transfer to countries/company codes in scope | Email forwarding is limited to email inboxes related to countries/company codes in scope. | {{customer_name}} |
| Limit transfer to supplier in scope | Email forwarding is limited to sender addresses of supplier in scope. | {{customer_name}} |

#### Limitations

- HYPATOS creates one transaction for each received email
- HYPATOS can process the email body with and without attachments
- Supported attachment types: pdf, jpeg, png, tiff
- Unsupported attachment types are not processed by HYPATOS
- Format of electronic documents is PDF or PDF/A, XML
- Email size must not exceed 30 MB
- Attachments must not have any password protection or encryption
- PDF must not contain security settings that restrict access to the data contained in the PDF file
- Active dynamic content in PDFs will not be rendered
- XFA form data content in PDFs may not be rendered
- Markups, comments and "sticky notes" in the PDF will not be rendered

#### References

| Document Name | Location |
|--------------|----------|
| Amazon Simple Email Service TLS Encryption | [LINK: AWS SES TLS Encryption Documentation] |
| Microsoft Exchange TLS Encryption | [LINK: Microsoft Exchange TLS Encryption Documentation] |
| Email Attachment Type Classification | [LINK: Microsoft Exchange Attachment Type Classification Documentation] |
| Studio Project List | [DOC: Studio Projects List] |

### 9.2 Transfer of ERP Data to HYPATOS

#### Requirements

| Requirement Description | Description |
|------------------------|-------------|
| Transferal of Masterdata | HYPATOS transfers SAP masterdata to the HYPATOS platform |
| Transferal of Transactional Data (Feedback loop of orders created in SAP) | HYPATOS transfers SAP transactional data (posting data) to the HYPATOS platform. |

#### Solution

| Requirement Description | Solution |
|------------------------|----------|
| Transferal of Masterdata | HYPATOS will provide a cloud-based connector for integration with the SAP platform. HYPATOS SAP connector will be responsible for fetching master and transactional data, stored in SAP and transferring this data to the HYPATOS platformThe masterdata is used during the enrichment phase in HYPATOS Studio. |
| Transferal of Transactional Data (Feedback loop of documents created in SAP) | HYPATOS will provide a cloud-based connector for integration with the SAP platform. HYPATOS SAP connector will be responsible for fetching master and transactional data, stored in SAP and transferring this data to the HYPATOS platformThe data is used during the enrichment phase in HYPATOS Studio. |

#### Data Objects & Transfer Intervals

| Category | SAP Objects | Intervals |
|----------|-------------|-----------|
| Suppliers | LFA1, LFB1, LFBK, ADRC | Initial migration: every 10 minutes until all suppliers are transferred<br>Subsequently: daily during night-time (UTC) |
| Companies | T001, ADRC | Weekly |
| Purchase Orders | EKKO, BSEG, EKKN, KONV | Daily during night-time (UTC) |
| Posting Data | BKPF, BSEG, BSET | Daily during night-time (UTC) |
| Chart of Accounts | SKAT | Weekly |
| Document Images (Studio – SAP) | N/A | every 5 minutes |
| Document Data | N/A | every 5 minutes |

#### References

| Document Name | Location |
|--------------|----------|
| SAP documentation | [LINK: Studio Docs - SAP Integration] |
| SAP – HY Datapointlist Mapping | [DOC: Datapoint List SAP Addon] |

### 9.3 Transfer of Document Data to Workflow

#### Requirements

| Requirement | Description |
|-------------|-------------|
| Transfer Document (HYPATOS Platform - (SAP)) | HYPATOS can transfer extracted, enriched and serialized document data to SAP on a regular basis. |
| Email attachments are transferred to SAP | HYPATOS can transfer valid email attachments to SAP. |
| Email body is transferred to SAP | HYPATOS can transfer the original eml file to SAP. |

#### Solution

| Requirement | Solution |
|-------------|----------|
| Transfer Document (HYPATOS Platform - (SAP)) | HYPATOS will provide a cloud-based connector for integration with SAP platform. HYPATOS SAP connector will be responsible for fetching completed Studio documents and transferring their data to SAP, along with the original document image that was uploaded to HYPATOS for processing.A SAP Connector BAdI enhancement that uses the ERP function modules takes care of the creation of a new record in ERP. A dedicated CronJob is scheduled to collect completed documents from HY Studio. |
| Email attachments are transferred to SAP | HYPATOS will provide a cloud-based connector for integration with SAP platform. HYPATOS SAP connector will be responsible for fetching completed Studio documents and transferring their data to SAP, along with the original document image that was uploaded to HYPATOS for processing.A SAP Connector BAdI enhancement that uses the ERP function modules takes care of the creation of a new record in ERP.A dedicated CronJob is scheduled to collect completed documents from HY Studio. |
| Email body is transferred to SAP | HYPATOS will provide a cloud-based connector for integration with SAP platform. HYPATOS SAP connector will be responsible for fetching completed Studio documents and transferring their data to SAP, along with the original document image that was uploaded to HYPATOS for processing.A SAP Connector BAdI enhancement that uses the ERP function modules takes care of the creation of a new record in ERP. A dedicated CronJob is scheduled to collect completed documents from HY Studio. |

#### Data Objects & Transfer Intervals

| Category | SAP Objects | Intervals |
|----------|-------------|-----------|
| Document Images (Studio – SAP) | N/A | every 5 minutes |
| Document Data | N/A | every 5 minutes |

#### References

| Document Name | Location |
|--------------|----------|
| SAP documentation | [LINK: Studio Docs - SAP Integration] |
| SAP – HY Datapointlist Mapping | [DOC: Datapoint List SAP Addon] |

---

## 10. Monitoring and Reporting

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

## 11. Implementation and Deployment

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

## 12. Maintenance and Support

Outlines the ongoing maintenance, monitoring, and support requirements for the solution. It may include details on bug tracking, change management, version control, and system documentation.

### References

| Document Name | Location |
|--------------|----------|
| Change Request Form | |
| Customer handbook | [LINK: HYPATOS Customer Handbook] |
| HYPATOS Customer Care Portal | [LINK: HYPATOS Customer Care Portal] |
| Support by email | [EMAIL: HYPATOS Support] |