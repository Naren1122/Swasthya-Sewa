# §7 — Global Error Handling and Logging

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 7.1 Centralized DRF Exception Handling

- Configure a custom DRF exception handler for consistent API error formatting.
- Handle known validation, authentication, permission, not-found, throttling, and conflict errors appropriately.
- Define custom exception classes for meaningful application-specific failures.
- Preserve the correct HTTP status code and useful error details.
- Avoid returning a generic success status for failed operations.

---

## 7.2 Understand the Exception-Handler Boundary

DRF's configured exception handler processes exceptions raised through DRF's exception handling flow. It does not automatically catch every exception in every part of the application.

- Let Django handle unhandled request errors through its normal error mechanisms.
- Configure logging for unexpected exceptions.
- Use monitoring/error-reporting tools in production.
- Do not use middleware as a substitute for DRF's exception handler.
- Do not silently swallow exceptions.

---

## 7.3 Logging

> [!CAUTION]
> Never log passwords, access tokens, refresh tokens, secrets, or sensitive personal/medical data.

- Use Python's `logging` module rather than `print()` for application logs.
- Configure log levels and handlers by environment.
- Include useful context such as request ID, operation, and relevant non-sensitive identifiers.
- Log unexpected failures with enough context to investigate them.
- Avoid logging the same exception repeatedly at every layer.

