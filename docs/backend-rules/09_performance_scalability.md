# §9 — Performance and Scalability

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 9.1 General Rules

- **Profile before optimizing.**
- Avoid N+1 queries and unnecessary database round trips.
- Paginate large responses.
- Cache only data that benefits from caching.
- Define cache expiration and invalidation behavior.
- Be careful not to leak user-specific or permission-sensitive cached data across users.

---

## 9.2 Asynchronous and Background Work

- Move long-running tasks out of request/response handling.
- Use Celery or another task system when asynchronous job processing is justified.
- Make background tasks retry-safe and preferably idempotent.
- Use retry with backoff for transient failures, not permanent validation failures.

---

## 9.3 External Services and Database

- Set timeouts for external HTTP/API calls.
- Avoid holding database transactions open while waiting on slow external services.
- Manage database connections according to the deployment environment.

---

## 9.4 Static Assets and Load Testing

- Use a CDN for suitable static and media assets.
- Load test important workflows and investigate bottlenecks.
- Scale the architecture based on measured requirements.

> [!WARNING]
> Do not add Redis, Celery, microservices, or complex infrastructure without a real requirement. Add complexity only when it solves a measured problem.

