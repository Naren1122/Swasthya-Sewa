# §2 — Project Planning and Architecture

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 2.1 Plan Globally, Design Locally

Before implementation, establish enough understanding of the whole product to avoid incompatible decisions. Do not attempt to specify every implementation detail upfront.

**Initial planning should normally include:**

- Product Requirements Document (PRD).
- Target users, roles, and permissions.
- MVP scope and out-of-scope items.
- Main user journeys and workflows.
- High-level system architecture.
- Initial entity-relationship diagram (ERD).
- Main API boundaries and integration requirements.
- Security, privacy, and performance requirements.
- Development milestones and overall testing strategy.

**Before each feature or module, refine:**

- Detailed user flow and acceptance criteria.
- Relevant models, relationships, constraints, and migrations.
- Serializer and API contract.
- Business rules and service operations.
- Authorization and ownership rules.
- Unit, integration, API, and E2E test cases.
- Dependencies, failure modes, and edge cases.

Update diagrams and documentation when implementation decisions or requirements change.

---

## 2.2 Prefer an Appropriately Simple Architecture

- Prefer a modular monolith for a typical portfolio or early production application unless requirements justify distributed services.
- Organize Django apps around business domains, such as `accounts`, `appointments`, or `inventory`.
- Keep responsibilities clear between HTTP handling, validation, business operations, data access, and persistence.
- Avoid unnecessary layers, abstractions, generic frameworks, and microservices.
- Use architecture patterns when they solve a real maintainability or testing problem.

---

## 2.3 Suggested Feature-Oriented Structure

Adapt this to the size and conventions of the existing project:

```text
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── asgi.py
├── apps/
│   ├── accounts/
│   │   ├── models/
│   │   ├── serializers/
│   │   ├── views/
│   │   ├── services/
│   │   ├── selectors/
│   │   ├── permissions/
│   │   ├── urls.py
│   │   ├── tests/
│   │   └── ...
│   └── appointments/
├── requirements/
├── manage.py
└── docs/
```

Use separate packages or files when a module becomes difficult to navigate. Do not split every tiny function into its own file. Django's conventional `models.py`, `views.py`, and similar files are also acceptable for small apps.

