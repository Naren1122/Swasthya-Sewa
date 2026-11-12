# §6 — API Design Standards

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 6.1 General Rules

- Use resource-oriented, consistent endpoint naming.
- Use HTTP methods according to their semantics (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
- Return appropriate HTTP status codes.
- Keep success and error response structures consistent.
- Validate all client-supplied data.
- Use pagination for potentially large collections.
- Support filtering and sorting only where useful and safely implemented.
- Document request and response schemas, preferably with an OpenAPI specification.
- Version APIs when compatibility requirements justify it.
- Avoid exposing internal model fields or sensitive information.
- Design critical write operations to be idempotent where retries or duplicate submissions are possible.
- Use idempotency keys for operations such as payments when appropriate.
- Do not assume that `PUT`, `PATCH`, or `POST` requests are automatically safe to retry.

---

## 6.2 Standard Error Response Contract

Choose a response format for the project and use it consistently:

```json
{
  "success": false,
  "message": "The submitted data is invalid.",
  "errors": {
    "email": ["Enter a valid email address."]
  }
}
```

> [!CAUTION]
> Do not expose stack traces, SQL errors, secrets, or internal implementation details to API clients.

