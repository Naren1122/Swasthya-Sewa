# §4 — Django and Django REST Framework Responsibilities

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

Use Django and DRF features appropriately rather than recreating built-in capabilities without a reason.

---

## 4.1 Component Responsibilities

| Component | Main Responsibility |
|---|---|
| **Models** | Persistence structure, relationships, model-level behavior |
| **Database constraints** | Enforce data integrity at the database level |
| **Serializers** | Validate and serialize API data |
| **Views / ViewSets** | Coordinate HTTP requests and responses |
| **Services** | Execute business operations and workflows |
| **Selectors / QuerySets** | Encapsulate reusable or complex data retrieval |
| **Permissions** | Enforce access rules |
| **Middleware** | Cross-cutting request/response processing |
| **Exception handler** | Standardize DRF exception responses |
| **Tasks / workers** | Execute asynchronous or long-running work |
| **Tests** | Verify behavior at appropriate boundaries |

> These are responsibilities, not mandatory folders. Use the smallest structure that keeps the code understandable.

---

## 4.2 View Rules

- Keep views thin and focused on HTTP concerns.
- Validate request data before executing business operations.
- Enforce authentication and permissions.
- Return appropriate status codes and response representations.
- Avoid embedding large business workflows or repeated query logic in views.

---

## 4.3 Serializer Rules

- Use serializers to validate untrusted API input.
- Use `validated_data` after successful validation.
- Implement field-level and object-level validation where appropriate.
- Do not treat serializer validation as a replacement for database constraints.
- Avoid putting complex multi-step business workflows into serializers.

---

## 4.4 Service Rules

- Use services for business operations that need reuse, transaction boundaries, or clear separation from HTTP.
- Keep services independent of request objects where practical.
- Pass required dependencies explicitly when this improves testability.
- Raise meaningful domain or application exceptions.
- Do not create a service layer for every trivial CRUD operation if it adds no value.

---

## 4.5 Selector and Query Rules

- Use QuerySets, managers, or selectors for reusable and complex reads.
- Keep query behavior understandable and measurable.
- Avoid hiding expensive queries behind properties or serializers.
- Make query performance visible in tests or profiling when it matters.

