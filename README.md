# Swasthya-Sewa (स्वास्थ्य सेवा) 🏥
> Production-Grade Doctor Appointment & Teleconsultation Platform with Dual-Engine Architecture (HTMX Web App + DRF REST API), Celery, Redis, Cloudinary, and PostgreSQL.

---

## 📌 Project Overview
**Swasthya-Sewa** is an end-to-end healthcare booking and teleconsultation platform built for an internship portfolio. It features a **Dual-Engine Architecture**:
1. **Interactive Web App:** Server-driven dynamic UI powered by **HTMX + Tailwind CSS** with zero React/SPA overhead.
2. **First-Class Public REST API:** Decoupled RESTful API powered by **Django REST Framework (DRF) + Serializers + Swagger / OpenAPI** (`/api/docs/`) for future mobile applications (Flutter/React Native) and third-party healthcare partners.

It integrates real-time doctor availability calculation, atomic concurrency locks (`select_for_update`), pre-appointment payment validation via Nepal's digital wallets (eSewa & Khalti), and free in-browser HD video calling via Jitsi Meet.

---

## 🛠️ Technology Stack Matrix

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Core** | Django 5.x (Python 3.11+) | Business logic, ORM, and admin engine |
| **Identifier Strategy** | UUIDv4 (Sensitive) + SLUG (Public) | Eliminates IDOR attacks while retaining SEO URLs |
| **Global Error Handling** | 3-Tier (HTMX OOB Toasts + DRF JSON + Root 500) | Predictable, crash-proof error responses |
| **Web UI Rendering** | HTMX + Tailwind CSS + DaisyUI | Fast, server-driven reactive HTML swaps with prebuilt components |
| **REST API & Serializers** | Django REST Framework (DRF) | Serializers, API views, and JSON endpoints (`/api/v1/`) |
| **API Documentation** | `drf-spectacular` (Swagger & OpenAPI) | Interactive API sandbox for interviewers (`/api/docs/`) |
| **Database** | PostgreSQL 15+ | Relational schema with ACID row locks (`select_for_update`) |
| **Distributed Task Queue** | Celery + Redis | 10-min slot auto-release & 15-min scheduled reminders |
| **Payment Gateways** | eSewa (ePay v2) & Khalti (ePayment v2) | Pre-appointment digital wallet payments |
| **Video Teleconsultation** | Jitsi Meet IFrame API (100% Free) | In-browser HD audio/video consultation |
| **Media & File Storage** | Cloudinary | Medical reports, prescriptions, and avatar CDN |
| **Authentication (Web)** | Session-Based + CSRF (`HttpOnly` Cookies) | Immune to XSS token theft in browsers |
| **Authentication (API)** | JWT (`djangorestframework-simplejwt`) | Stateless Bearer token auth for mobile/API clients |
| **Social Authentication** | Google OAuth2 (`django-allauth`) | Role-pinned login (Doctor admin-only, Patient self-serve) |

---

## 📖 Complete Documentation & Specification

All architectural, data, roadmap, and coding standards are documented in:
* 📄 **[PROJECT_SPECIFICATION.md](file:///c:/Users/user/Desktop/Swasthya-Sewa/files/PROJECT_SPECIFICATION.md)** — PRD, Data Modeling, ER Diagrams, Architecture, and Invariants.
* 🗺️ **[ROADMAP.md](file:///c:/Users/user/Desktop/Swasthya-Sewa/files/ROADMAP.md)** — 8-phase implementation roadmap with deliverables and Definitions of Done (DoD).
* 🛡️ **[BACKEND_CODING_RULES.md](file:///c:/Users/user/Desktop/Swasthya-Sewa/docs/BACKEND_CODING_RULES.md)** — Senior engineering standards for scalability, N+1 query elimination, data normalization, concurrency locking, and Celery offloading.
* 🎨 **[UI_UX_DESIGN_STANDARDS.md](file:///c:/Users/user/Desktop/Swasthya-Sewa/docs/UI_UX_DESIGN_STANDARDS.md)** — Production UI/UX rules, DaisyUI + Tailwind prebuilt component snippets, color systems, and HTMX feedback patterns.

---

## 🚀 7-Day Implementation Schedule

- [ ] **Phase 0:** Environment & Scaffolding (PostgreSQL, Redis, Django, HTMX, DRF).
- [ ] **Phase 1:** Dual Auth (Session/CSRF for Web + SimpleJWT for API), Custom User, Google OAuth.
- [ ] **Phase 2:** Doctor Domain, Weekly Schedules, Leave Overrides, Pure Python Slot Engine.
- [ ] **Phase 3:** Patient Discovery, Dynamic HTMX Slot Picker & DRF Slot Endpoints.
- [ ] **Phase 4:** eSewa & Khalti Integrations, Atomic Slot Lock (`select_for_update`), Payment Callbacks.
- [ ] **Phase 5:** Jitsi Meet Video Call Embedding, Access Guards, Cloudinary Medical File Uploads.
- [ ] **Phase 6:** Celery & Redis Task Engine, 10-Minute Slot Auto-Release, Periodic Reminder Scheduler.
- [ ] **Phase 7:** Doctor Queue Desk, Prescription Editor, Swagger / OpenAPI Docs (`/api/docs/`), Seed Script.

---

## 👥 User Roles & Access Rules

1. **Patient:**
   - Self-registers via email/password or Google OAuth.
   - Searches doctors, checks real-time available slots, holds a slot for 10 minutes.
   - Settles consultation fee via eSewa or Khalti to confirm booking.
   - Joins 1-click HD video call (Jitsi) on appointment day.
   - Uploads prior medical records to Cloudinary.

2. **Doctor:**
   - **Admin-Provisioned ONLY** (Cannot self-register).
   - Configures recurring weekly shift hours and emergency leave.
   - Reviews daily appointment queue and patient pre-read documents.
   - Launches video consultation and issues digital prescriptions.

3. **Administrator:**
   - Provisions doctor accounts and verifies medical credentials (NMC ID).
   - Manages medical specialties and monitors transaction audit logs.
