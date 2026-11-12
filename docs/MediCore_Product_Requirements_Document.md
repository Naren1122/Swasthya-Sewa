# Product Requirements Document
## MediCore — Hospital Management & Digital Healthcare Platform

| Field | Details |
|---|---|
| **Document version** | 1.0 — Initial product definition |
| **Date** | 8 November 2026 |
| **Product status** | Proposed / Planning |
| **Primary market** | Nepal (initial deployment) |
| **Document owner** | Product / Development Team |

---

### Product Summary

MediCore is a web-based hospital management platform that brings core hospital operations and selected digital healthcare services into one system. It is intended to help a hospital manage patients, doctors, appointments, consultations, laboratory workflows, pharmacy stock, billing and admissions, while giving patients a convenient way to access services online.

### Planning Assumptions

This PRD defines a practical first release for a single hospital, with a data model and architecture that can be extended to multiple hospitals later. The initial online consultation experience is text chat (not video). Both AI symptom guidance and medical-report explanation are included as assisted features, not as clinical diagnosis. Khalti is integrated in test mode for development and demonstration.

> [!NOTE]
> Treat this document as the agreed product baseline, not a complete implementation specification. Confirm workflows with a hospital representative before production use. For each development phase, convert the relevant requirements into detailed tasks, wireframes, database design, API contracts and test cases.

---

## Table of Contents

1. [Project Overview and Problem Statement](#1-project-overview-and-problem-statement)
2. [Goals and Objectives](#2-goals-and-objectives)
3. [Target Users and Roles](#3-target-users-and-roles)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [User Stories and Acceptance Criteria](#6-user-stories-and-acceptance-criteria)
7. [Technical Requirements](#7-technical-requirements)
8. [Feature Prioritization](#8-feature-prioritization)
9. [Scope and Out of Scope](#9-scope-and-out-of-scope)
10. [Success Metrics](#10-success-metrics)
- [Appendix A: Key Workflows and Business Rules](#appendix-a-key-workflows-and-business-rules)
- [Appendix B: Risks, Assumptions and Open Decisions](#appendix-b-risks-assumptions-and-open-decisions)

---

## 1. Project Overview and Problem Statement

### 1.1 Project Overview

MediCore is a centralized hospital operations and patient-service platform. It provides role-based workspaces for administrators, reception staff, doctors, laboratory staff, pharmacists and patients. The system is designed to reduce fragmented record keeping, improve visibility across departments and make selected services accessible online.

The first release focuses on reliable core workflows: patient registration, doctor and department management, appointment scheduling, consultations, laboratory requests and results, pharmacy inventory, billing and basic admissions. Digital services include appointment-based text chat with a doctor, a guarded AI symptom assistant, AI-assisted explanations of uploaded reports, and Khalti test payments.

### 1.2 Problem Statement

Many hospitals and clinics rely on disconnected registers, spreadsheets, paper files, phone calls and separate tools for appointments, billing and departmental work. This can create duplicate records, slow information retrieval, scheduling conflicts, limited operational visibility and avoidable administrative effort. Patients may also need to visit or call the hospital for routine booking and follow-up activities.

MediCore aims to address these problems through a shared, permission-controlled system and a consistent set of workflows. It should improve coordination without replacing clinical judgement or claiming to automate medical decisions.

### 1.3 Product Principles

- Patient safety and privacy take priority over convenience or feature breadth.
- Use clear role-based access: users should see only the information required for their work.
- Keep clinical records traceable; important changes should be attributable to a user and timestamp.
- Prefer reliable, understandable workflows over excessive automation.
- AI output is informational support and must not be presented as a confirmed diagnosis.
- Build the MVP for one hospital while avoiding unnecessary design choices that prevent future expansion.

### 1.4 Product Boundaries

MediCore is an administrative and patient-service platform. It is **not** an electronic prescribing authority, a medical-device diagnostic system, an emergency response service or a substitute for a hospital's clinical governance, professional judgement and legal obligations.

---

## 2. Goals and Objectives

### 2.1 Product Goals

- Centralize essential hospital workflows in one web application.
- Make patient registration, appointment booking and consultation management more consistent.
- Give doctors and authorized staff timely access to relevant patient and visit information.
- Support laboratory, pharmacy, billing and admission workflows with traceable records.
- Offer patients online access to appointment booking, consultation chat and selected report information.
- Demonstrate a secure, maintainable, testable full-stack architecture suitable for an incremental production build.

### 2.2 Measurable Objectives for the MVP

| Objective | Initial Target / Definition |
|---|---|
| **Appointment workflow** | A patient or authorized staff member can create, view, reschedule and cancel an appointment without creating overlapping confirmed bookings. |
| **Patient record integrity** | Each patient has one unique system identity; duplicate detection and controlled record updates are supported. |
| **Consultation session** | A confirmed paid online consultation can enter a time-bounded text-chat session and close automatically at the configured end time. |
| **Payment verification** | A payment is marked successful only after server-side verification with the payment provider. |
| **Department workflows** | A lab order can be created, processed, verified and made visible to authorized users; pharmacy stock changes are recorded. |
| **Auditability** | Important actions are recorded with actor, action, target and timestamp. |
| **Quality** | Critical workflows have automated tests and no known unresolved critical/high-severity defects at release. |

> [!NOTE]
> Targets are proposed starting points and should be validated with actual hospital users and baseline measurements.

---

## 3. Target Users and Roles

MediCore uses role-based access control (RBAC). A user may hold more than one role only when explicitly granted by an authorized administrator. Access to patient data must be checked on the server for every relevant request.

| Role | Primary Responsibilities | Typical Access |
|---|---|---|
| **Hospital administrator** | Configure hospital profile, departments, staff accounts, permissions, service catalog and operational settings. | Administrative settings, user management, reports and authorized operational records. |
| **Receptionist / front desk** | Register patients, maintain demographic details, book appointments, manage check-ins and assist with billing. | Patient demographics, appointment schedule, check-in and permitted billing views. |
| **Doctor** | Review assigned patients, manage availability, conduct consultations, create clinical notes, prescriptions and lab requests. | Assigned/authorized patient records, schedules, consultations and clinical workflows. |
| **Nurse / clinical staff** | Support patient intake, observations, care activities and admissions as assigned. | Assigned patient encounters and permitted clinical observations. |
| **Laboratory technician** | Receive test orders, record samples, enter results and submit results for verification. | Lab orders, sample workflow and result entry; restricted clinical record access. |
| **Pharmacist** | Manage medicine catalog, stock, batches, expiry and dispensing against authorized prescriptions. | Pharmacy inventory, dispensing and prescription details required for fulfillment. |
| **Patient** | Manage own profile, book appointments, view own appointments, access released results and use digital services. | Own profile, own bookings, released records and own payment history. |
| **Billing staff** | Prepare invoices, record payments, track balances and issue receipts. | Billing records and the minimum patient/visit information needed to bill. |
| **System operator / support** | Monitor technical health and troubleshoot system operation. | Technical logs and operational metadata; no routine access to clinical content. |

> [!NOTE]
> The MVP may combine some operational roles in a small demonstration environment, but the permission model should keep them logically separate.

---

## 4. Functional Requirements

**Priority labels:** `Must` = required for the defined MVP; `Should` = valuable but can follow the first usable release; `Could` = optional enhancement. Requirement IDs should be retained in tickets and tests.

| ID | Feature | Priority | Requirement |
|---|---|---|---|
| **FR-01** | Authentication and account management | Must | Users can sign in and sign out securely. Authorized users can create, activate, deactivate and manage staff accounts. Password reset and email verification can be enabled where the deployment supports email delivery. |
| **FR-02** | Role-based authorization | Must | The system enforces permissions on the server for pages, APIs and object-level data. A user cannot access another patient's records by changing an identifier in a URL or request. |
| **FR-03** | Patient registration and profile | Must | Authorized staff can create and update patient profiles, assign a unique patient number, capture contact and emergency-contact details, and search for existing patients to reduce duplicates. |
| **FR-04** | Patient medical record | Must | Authorized clinicians can record relevant history, allergies, encounter notes, diagnoses entered by clinicians, prescriptions and attachments. Changes to important clinical data are traceable. |
| **FR-05** | Department and doctor management | Must | Administrators can manage departments, doctor profiles, specialties, consultation fees and active/inactive status. |
| **FR-06** | Doctor availability | Must | Doctors or authorized staff can define weekly availability, exceptions, breaks, holidays and online-consultation availability. |
| **FR-07** | Appointment booking | Must | Patients or staff can view available slots and create, view, reschedule or cancel appointments according to configured rules. The system prevents overlapping confirmed bookings. |
| **FR-08** | Appointment check-in and status | Should | Reception staff can mark arrivals and update visit status. Authorized staff can view daily schedules by doctor and department. |
| **FR-09** | Online text consultation | Must | A patient can book an available online consultation slot, pay where required, and join a text-chat room during the confirmed session window. The doctor can respond and add a consultation summary. |
| **FR-10** | Consultation time enforcement | Must | The session has a defined start and end time (initially 10 minutes). When the session ends, sending new messages is disabled and the conversation remains available only to authorized participants according to retention policy. |
| **FR-11** | Khalti payment integration | Must | The system creates a pending payment, initiates Khalti test-mode checkout, verifies the transaction server-side and updates payment/booking state idempotently. Client-side redirect alone is never proof of payment. |
| **FR-12** | AI symptom assistant | Should | The patient can describe symptoms and answer follow-up questions. The assistant provides general information, highlights emergency warning signs and suggests appropriate next steps, without claiming a definitive diagnosis or prescribing medication. |
| **FR-13** | Medical report upload and explanation | Should | A patient can upload supported report files. The system validates file type, size and ownership, stores the file privately, processes it asynchronously and displays an AI-generated plain-language explanation with limitations. |
| **FR-14** | Laboratory management | Should | Doctors can request tests from a catalog. Lab staff can track order/sample status, enter results and submit them for verification. Released results become visible to authorized clinicians and the relevant patient. |
| **FR-15** | Pharmacy inventory | Should | Authorized pharmacy staff can manage medicines, suppliers, batches, quantities and expiry dates; record purchases and dispensing; and receive low-stock/expiry alerts. |
| **FR-16** | Billing and invoices | Must | Authorized staff can generate invoices for configured services, record payment status and amounts, show outstanding balances and issue a receipt or printable invoice. |
| **FR-17** | Admissions and bed management | Could | Authorized staff can register admissions, allocate available beds/rooms, record transfers and discharge patients. |
| **FR-18** | Notifications | Should | The system can create in-app notifications and send configured email/SMS reminders for appointments, payments or released results. Delivery failures are logged and retryable. |
| **FR-19** | Dashboards and reports | Should | Authorized roles can view relevant operational summaries such as appointments, patient counts, revenue, lab workload, pharmacy stock and bed occupancy where those modules are enabled. |
| **FR-20** | Audit log | Must | The system records important security and business events, including account/permission changes, access-sensitive updates, payment state changes and clinical record modifications. |
| **FR-21** | Search and filtering | Must | Users can search and filter records within their permissions, with pagination for large result sets. |
| **FR-22** | File and document access | Must | Uploaded documents are private by default. Access is authorized and time-limited where signed links are used; public URLs must not expose sensitive health documents. |

### 4.1 Key Status Models (Initial Proposal)

| Entity | Suggested Statuses |
|---|---|
| **Appointment** | `REQUESTED`, `HELD`, `CONFIRMED`, `CHECKED_IN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `EXPIRED`, `NO_SHOW` |
| **Payment** | `PENDING`, `COMPLETED`, `FAILED`, `CANCELLED`, `REFUNDED` |
| **Lab order** | `ORDERED`, `SAMPLE_COLLECTED`, `PROCESSING`, `RESULT_ENTERED`, `VERIFIED`, `RELEASED`, `CANCELLED` |
| **Admission** | `PLANNED`, `ADMITTED`, `TRANSFERRED`, `DISCHARGED`, `CANCELLED` |
| **Medicine batch** | `ACTIVE`, `LOW_STOCK`, `EXPIRED`, `DEPLETED`, `INACTIVE` |

> [!IMPORTANT]
> Exact states and permitted transitions should be enforced in the backend service layer rather than relying on frontend controls.

---

## 5. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Security** | Use HTTPS in deployed environments; hash passwords with a suitable password-hashing algorithm; protect sessions/tokens; validate input server-side; apply CSRF/CORS protections appropriate to the authentication design; rate-limit sensitive endpoints; store secrets outside source control. |
| **Privacy and confidentiality** | Apply least-privilege access, private file storage, secure backups and defined retention/deletion rules. Avoid exposing patient details in URLs, logs, analytics or error messages. |
| **Performance** | For normal dashboard and CRUD operations, target a 95th-percentile response time under 2 seconds under the agreed MVP test load, excluding external provider latency and large report processing. |
| **Availability and resilience** | Design for graceful failure of external services. Payment callbacks, background tasks and notifications must be retryable without duplicate charges or duplicate business actions. |
| **Data integrity** | Use database constraints and transactions for critical workflows, including slot reservation, payment updates, stock deduction and invoice totals. |
| **Usability and accessibility** | Provide responsive layouts for desktop, tablet and mobile; clear validation and error messages; keyboard-accessible controls; readable contrast and consistent navigation. |
| **Maintainability** | Use feature-based modules, clear service boundaries, documented APIs, environment-based configuration, code formatting/linting and automated tests. |
| **Scalability** | Support pagination, indexed queries, background processing and stateless application instances where practical. Avoid premature microservices for the MVP. |
| **Compatibility** | Support current stable versions of major browsers (Chrome, Edge, Firefox and Safari) and modern mobile browsers. |
| **Observability** | Capture structured application logs, error traces, task failures and basic health checks without logging passwords, tokens or unnecessary patient content. |
| **Backup and recovery** | Define automated database backup frequency, retention and restoration procedure before production use; test restoration rather than assuming backups work. |
| **Localization** | Initial interface language may be English. Keep date, currency and locale formatting configurable; support NPR and Nepal-local operational conventions. |

> [!NOTE]
> These are proposed acceptance targets for planning. Confirm final thresholds, legal requirements, hosting capacity and retention periods before a real hospital deployment.

---

## 6. User Stories and Acceptance Criteria

The following stories define the expected user-visible outcomes. Acceptance criteria are written as testable conditions and can be expanded into detailed test cases.

### US-01 Patient Registration

> *As a receptionist, I want to register a patient so that the hospital can maintain a consistent patient record.*

- Given I am authorized, when I submit valid required details, then the system creates a patient record and unique patient number.
- If a likely duplicate exists, the system warns me and lets me review the matching record before creating another.
- A user without patient-management permission cannot create or edit patient records.

### US-02 Book an Appointment

> *As a patient, I want to see a doctor's available slots and book one so that I can plan a visit.*

- Only slots within the doctor's configured availability and booking rules are shown as available.
- When two users attempt to book the same slot, at most one booking becomes confirmed.
- The patient receives a clear confirmation or failure message and can view the appointment status.

### US-03 Pay for Online Consultation

> *As a patient, I want to pay for an online consultation so that my booking can be confirmed.*

- The backend creates a pending payment linked to the correct booking and unique reference.
- A successful client redirect without server-side verification does not mark the payment complete.
- Repeated callbacks or verification requests do not create duplicate payment records or duplicate confirmations.

### US-04 Join a 10-Minute Doctor Chat

> *As a patient, I want to chat with my doctor during my booked session so that I can ask a focused question remotely.*

- Only the patient and assigned doctor (plus explicitly authorized support roles) can access the room.
- The room accepts messages only during the permitted session window and applies the configured late-join policy.
- At the end time, the room becomes read-only and the conversation/summary is retained according to policy.

### US-05 Review a Patient's Record

> *As a doctor, I want to review relevant patient history before a consultation so that I can make an informed clinical assessment.*

- The doctor can access only patients/encounters they are authorized to view.
- The record displays relevant history, allergies and prior encounters with clear dates and authors.
- Clinical updates are attributed to the acting user and timestamp.

### US-06 Use AI Symptom Guidance

> *As a patient, I want general guidance about symptoms so that I can understand possible next steps.*

- The assistant clearly states it is not a diagnosis and does not replace a clinician.
- The assistant identifies configured red-flag symptoms and directs the user to urgent/emergency care where appropriate.
- The assistant does not prescribe medication, dosage or advise stopping prescribed treatment.

### US-07 Upload and Understand a Report

> *As a patient, I want a plain-language explanation of an uploaded report so that I can better understand its contents.*

- Only allowed file types and sizes are accepted, and the upload is linked to the authenticated patient.
- The report is private and accessible only to authorized users.
- The explanation identifies uncertainty and advises discussing interpretation with a qualified clinician; original report values remain distinguishable from AI commentary.

### US-08 Process a Lab Test

> *As a lab technician, I want to process an ordered test and enter results so that the clinician can review them.*

- The technician sees only lab work they are permitted to process.
- A result cannot be released until required fields and verification steps are complete.
- The system records who entered and verified the result and when.

### US-09 Dispense Medicine

> *As a pharmacist, I want to dispense prescribed medicine and update stock so that inventory remains accurate.*

- Dispensing is linked to an authorized prescription or permitted workflow.
- Stock deduction is atomic; a failed dispense does not partially reduce inventory.
- The system blocks or warns on expired or insufficient stock according to policy.

### US-10 Create an Invoice

> *As billing staff, I want to generate an invoice for a visit so that charges and payments can be tracked.*

- Invoice line items, totals and balance are calculated on the server.
- A payment entry updates the invoice balance without overwriting historical payment records.
- The invoice and receipt can be viewed or printed by authorized users.

### US-11 Audit Sensitive Changes

> *As a hospital administrator, I want important changes recorded so that I can investigate mistakes and misuse.*

- The audit record includes actor, action, target and timestamp.
- Ordinary users cannot alter or delete audit records.
- Sensitive values such as passwords, tokens and full payment credentials are not written to audit logs.

---

## 7. Technical Requirements

### 7.1 Proposed Architecture

Use a separated frontend and backend API. Next.js provides the patient and staff web interfaces; Django REST Framework exposes authenticated APIs and owns business rules. PostgreSQL is the durable source of truth. Redis supports transient coordination and background infrastructure; it must not be treated as the permanent record store.

| Layer | Proposed Technology | Responsibility |
|---|---|---|
| **Frontend** | Next.js (React), JavaScript or TypeScript, Tailwind CSS, shadcn/ui | Responsive patient portal and staff dashboards; form state, client-side UX and API consumption. |
| **Backend API** | Python, Django, Django REST Framework | Authentication/authorization, validation, business rules, API endpoints and orchestration. |
| **Database** | PostgreSQL | Persistent users, patients, appointments, clinical records, payments, inventory, invoices and audit data. |
| **ORM / data access** | Django ORM | Models, relationships, migrations, query construction and database constraints. |
| **Real-time communication** | Django Channels + Redis | WebSocket text chat, presence/session events and real-time updates. |
| **Background jobs** | Celery + Redis | Reminders, report-processing jobs, expiry tasks and retryable notifications. |
| **Payments** | Khalti test environment initially | Checkout initiation and server-side payment verification. |
| **File storage** | Private object storage for health documents; Cloudinary only for public/general media if needed | Secure report and document storage; separate from sensitive patient documents. |
| **Testing** | Pytest / pytest-django; frontend component and E2E tests (e.g. Playwright) | Unit, API, integration, permission, payment and end-to-end workflow coverage. |
| **Deployment** | Docker; managed PostgreSQL/Redis; HTTPS reverse proxy | Repeatable environments, deployment and operational configuration. |

### 7.2 High-Level Request Flow

- **Browser → Next.js UI → Django REST API → PostgreSQL** for normal application operations.
- **Real-time chat:** browser WebSocket → Django Channels → Redis channel layer; messages and session state that must persist are stored in PostgreSQL.
- **Background processing:** Django enqueues Celery tasks → Redis broker → worker processes notifications/report jobs → results and status are persisted.
- **Payment:** frontend requests checkout creation → backend creates pending transaction → Khalti checkout → backend verifies provider transaction → backend updates payment and booking atomically.

### 7.3 Core Data Domains (Initial)

| Domain | Representative Entities |
|---|---|
| **Identity and access** | User, Role, Permission, UserRole, StaffProfile, PatientProfile |
| **Hospital setup** | Hospital, Department, DoctorProfile, Specialty, Service |
| **Scheduling** | DoctorAvailability, AvailabilityException, Appointment, SlotHold |
| **Clinical** | PatientHistory, Allergy, Encounter, ClinicalNote, Prescription, PrescriptionItem |
| **Consultation** | ConsultationRoom, ChatMessage, ConsultationSummary |
| **AI services** | AIConversation, AIMessage, UploadedReport, ReportAnalysis, ProcessingJob |
| **Laboratory** | LabTest, LabOrder, LabSample, LabResult, ResultVerification |
| **Pharmacy** | Medicine, Supplier, MedicineBatch, StockMovement, Dispense |
| **Finance** | Invoice, InvoiceItem, Payment, Refund |
| **Admissions** | Ward, Room, Bed, Admission, BedAssignment |
| **Platform** | Notification, AuditEvent, FileAsset |

### 7.4 Architecture and Implementation Rules

- Organize backend code by feature/domain (for example `patients`, `appointments`, `billing`), not as one large global collection of unrelated files.
- Keep request parsing and HTTP response handling in API views; place multi-step business rules and transactions in service functions/classes.
- Use serializers for API input/output validation, and database constraints for invariants that must hold under concurrency.
- Use UUIDs as internal/public identifiers where appropriate. Use slugs only where human-readable URLs add value; a slug is not a security control.
- Use database transactions and appropriate locking/unique constraints for slot booking, payment state changes and stock deduction.
- Keep payment provider credentials, AI API keys, Django secret key and database credentials in environment/secret management.
- Version and document APIs; return consistent error formats and avoid leaking stack traces or sensitive data to clients.
- Use migrations as the source of truth for schema changes; review migrations and test them before deployment.

### 7.5 Security, Privacy and Safety Controls

> [!CAUTION]
> Never rely on frontend checks for role permissions, payment success, consultation timing or file ownership.

- Apply server-side object-level authorization to every patient, report, appointment, message and invoice endpoint.
- Use private storage and short-lived authorized access for medical reports; do not place sensitive files in public media folders.
- Record consent and the purpose of AI processing where required; disclose that uploaded content may be processed by an external AI provider if applicable.
- Minimize patient data sent to third-party AI services; assess provider retention, data-use and regional processing terms before production.
- Define retention, deletion, export, breach response and backup policies with qualified local legal/compliance advice before real patient data is used.
- AI symptom guidance must include emergency escalation, limitations and clinician follow-up; report explanations must not alter or replace the original report.

### 7.6 Key Integrations

**Khalti:** Begin with test credentials and sandbox transactions. Implement initiation, callback handling, server-side verification, idempotency and reconciliation. Do not store card or wallet credentials.

**AI provider:** Wrap the selected provider behind an internal service interface so the provider can be changed. Store input/output metadata needed for traceability while minimizing sensitive content retention.

**File processing:** Validate file extension, MIME type, file size and ownership; scan files where practical; process asynchronously; keep original uploads immutable and private.

---

## 8. Feature Prioritization

Prioritization is based on delivering a coherent, demonstrable product without spreading effort across too many incomplete modules.

| Release | Features | Reason |
|---|---|---|
| **MVP — Must** | Authentication and RBAC; hospital/department/doctor setup; patient registration; doctor availability; appointments; 10-minute text consultation; Khalti test payment; basic billing; audit logging; responsive core UI. | Establishes the complete patient-to-appointment-to-consultation journey and the security/data foundations. |
| **MVP+ — Should** | AI symptom assistant; report upload and explanation; laboratory workflow; pharmacy inventory; notifications; operational dashboards; stronger search and exports. | Adds differentiated digital healthcare and important hospital department workflows after core scheduling/payment reliability. |
| **Later — Could** | Admissions and bed management; video consultation; multi-hospital tenant administration; advanced analytics; integrations with external hospital systems; multilingual interface; advanced inventory/procurement. | These increase complexity and should be guided by user feedback, compliance review and operational need. |

### Recommended Build Order

1. **Foundation:** repository, environments, database, authentication, RBAC, audit foundation and shared UI.
2. **Master data:** hospital settings, departments, doctors, services and availability.
3. **Patient and appointment journey:** patient profiles, slot generation, booking, rescheduling, cancellation and concurrency tests.
4. **Payments and online consultation:** pending payment, Khalti verification, room access, 10-minute lifecycle and chat tests.
5. **Billing and operational records:** invoices, receipts and basic encounter notes.
6. **AI features:** symptom assistant and report explanation with safety and privacy controls.
7. **Laboratory and pharmacy workflows;** then notifications and dashboards.
8. **Deployment hardening:** security review, backup/restore test, monitoring, accessibility and end-to-end regression.

> [!IMPORTANT]
> Do not begin all modules at once. Complete and test one vertical workflow at a time, while documenting the overall architecture and data boundaries early.

---

## 9. Scope and Out of Scope

### 9.1 In Scope for the Planned Product

- One hospital deployment with configurable departments, staff and services.
- Patient and staff authentication with role-based permissions.
- Patient registration, profiles and authorized clinical history.
- Doctor profiles, specialties, schedules and appointment booking.
- Paid, time-limited 10-minute text consultations using Khalti test payments.
- Basic billing and invoice/payment records.
- AI symptom guidance and AI-assisted report explanation, subject to safety and privacy controls.
- Laboratory order/result workflow and pharmacy stock workflow as staged features.
- Notifications, audit logs and basic operational reporting.
- Responsive browser-based interface and automated tests for critical workflows.

### 9.2 Out of Scope for the Initial Release

- Video consultations, voice calls and telemedicine recording.
- AI diagnosis, treatment decisions, medication recommendations or autonomous clinical triage.
- Direct integration with national health information systems, insurance providers or external hospital systems unless separately specified.
- Production payment settlement before merchant onboarding, provider approval and end-to-end verification are complete.
- Full accounting/ERP, payroll, procurement, insurance claims and advanced revenue-cycle management.
- Medical device integration, remote patient monitoring and IoT workflows.
- Multi-hospital SaaS tenant billing and cross-hospital patient identity management in the first release.
- Native iOS/Android applications; the initial product is a responsive web application.
- Use of real patient data in development, demos or testing without an approved legal, privacy and security basis.

### 9.3 MVP Completion Definition

The MVP is complete when an authorized staff member can register a patient, configure a doctor and availability, book an appointment, complete a Khalti test payment, and conduct a permission-controlled 10-minute text consultation; the system prevents double booking, records auditable state changes, and passes agreed automated tests in a deployable staging environment.

---

## 10. Success Metrics

> [!NOTE]
> Metrics should be collected in a staging pilot first and then reviewed with hospital stakeholders. Avoid collecting unnecessary patient-identifiable analytics.

| Area | Metric | Initial Success Signal |
|---|---|---|
| **Adoption** | Weekly active staff users by role | Intended staff roles use the system during the pilot; no role is blocked by a missing core workflow. |
| **Patient access** | Share of eligible appointments booked digitally | A measurable proportion of eligible bookings can be completed without staff re-entering the same information. |
| **Scheduling reliability** | Double-booking incidents | Zero confirmed double bookings in acceptance and concurrency tests; investigate any production incident. |
| **Payment reliability** | Verified payment success / reconciliation mismatch rate | All successful test transactions reconcile to one payment record; no booking is confirmed solely by redirect. |
| **Consultation reliability** | Sessions correctly opened and closed at scheduled time | At least 99% of test sessions enforce the configured access window; exceptions are logged. |
| **Workflow efficiency** | Median time to register a patient and book an appointment | Baseline and post-pilot time show improvement without increasing data-entry errors. |
| **Data quality** | Duplicate patient records and incomplete required fields | Downward trend in duplicates; required fields validated consistently. |
| **System quality** | API error rate, p95 response time and uptime | Meet agreed staging targets; critical workflows remain usable during expected test load. |
| **Security** | Unauthorized access test results and unresolved critical findings | All planned permission tests pass; no unresolved critical/high security findings before pilot. |
| **User satisfaction** | Short staff and patient feedback score | Collect baseline feedback and identify the top three usability improvements per review cycle. |

> Metric definitions, baselines and numeric targets should be finalized after observing the first pilot; the signals above are acceptance-oriented starting points.

---

## Appendix A: Key Workflows and Business Rules

### A.1 Appointment and Payment Workflow

1. Patient selects a doctor and an available slot.
2. Backend validates the slot against doctor availability and existing bookings, then creates a short-lived hold if payment is required.
3. Backend creates a pending payment with a unique merchant reference and initiates Khalti checkout.
4. After checkout, backend verifies the transaction with Khalti using the provider's documented verification mechanism.
5. On verified success, a database transaction marks payment complete and confirms the appointment exactly once; on failure/expiry, the hold is released.
6. Send confirmation notification and make the consultation room accessible only to the assigned patient and doctor.

### A.2 Ten-Minute Chat Rules to Decide Before Implementation

- Define whether the 10 minutes begin at the scheduled time or when both participants join; **recommended default:** scheduled start time with a clearly defined grace period.
- Define a late-join policy and whether unused time is lost or extended; do not let the frontend decide this.
- Define cancellation, refund and no-show rules with the hospital and payment provider.
- Define whether the doctor can end early and whether a summary is required.
- Persist messages and status transitions according to a documented retention policy; restrict access after completion.

### A.3 AI Safety Rules

> [!WARNING]
> AI features must never claim to provide clinical diagnosis or replace professional medical judgement.

- Clearly label all AI responses as informational and not a diagnosis.
- Detect configured emergency red flags and advise immediate local emergency care rather than continuing routine chat.
- Do not provide prescription medication or dosage instructions; do not advise stopping current treatment.
- Do not invent report values. Separate extracted values, reference ranges and generated explanations.
- Show uncertainty, encourage clinician review and provide a way to book/contact a clinician.
- Log model/provider version and processing timestamp where appropriate, while minimizing retained sensitive prompt content.

### A.4 Transaction and Concurrency Rules

- Use database transactions and constraints for booking, payment confirmation and stock movement.
- Make provider callbacks and background jobs idempotent using stable external references and unique constraints.
- Treat Redis locks/holds as temporary coordination only; PostgreSQL constraints remain the final protection against duplicate bookings.
- Never decrement inventory or confirm a booking before the relevant transaction succeeds.

---

## Appendix B: Risks, Assumptions and Open Decisions

| Item | Current Assumption / Risk | Decision Needed |
|---|---|---|
| **Hospital workflow fit** | The exact operational workflow varies by hospital. | Validate registration, billing, lab, pharmacy and admission steps with at least one representative user per role. |
| **Single vs multi-hospital** | Initial release is single-hospital; design may allow a future hospital identifier boundary. | Confirm whether tenant isolation is required from day one before finalizing schema and authorization. |
| **Clinical and legal compliance** | Health data is sensitive and local obligations may apply. | Obtain qualified Nepal-specific legal, privacy and clinical governance review before production use. |
| **AI provider and data use** | AI features may send data to a third-party provider. | Select provider only after reviewing data retention, training use, region, security and contractual terms. |
| **Khalti production** | Test integration is for development/demo only. | Complete merchant onboarding, provider approval, refund and reconciliation testing before live payments. |
| **Chat timing** | 10-minute session is requested, but start/grace/cancellation details are not finalized. | Agree exact session timing, late-join, no-show and refund rules. |
| **Storage** | Medical documents must be private. | Choose storage provider, encryption, access logging, backup and retention policy. |
| **Notifications** | Email/SMS provider and costs are not yet selected. | Select channels and provider after estimating local delivery reliability and cost. |
| **Language and calendar** | English-first interface is assumed; Nepal-local formatting may be needed. | Decide Nepali language support and AD/BS date display requirements. |
| **Operational support** | Production use requires monitoring and incident response. | Assign an owner for backups, access reviews, support, security patches and incident handling. |

---

## Document Status and Change Control

This is **version 1.0** and should be revised when stakeholder interviews, prototype testing or technical discovery changes a requirement. Record each change with date, owner, reason and affected requirement IDs.

> [!CAUTION]
> Do not silently change payment, clinical, privacy or access-control rules.

---

*End of Document*

