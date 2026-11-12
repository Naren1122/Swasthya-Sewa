# §12 — Production and Deployment Standards

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 12.1 Configuration and Secrets

- Separate development, test, staging, and production configuration.
- Keep secrets out of source control.
- Run Django's deployment checks: `python manage.py check --deploy`.

---

## 12.2 Server and HTTPS

- Use a production-ready WSGI or ASGI server (e.g., Gunicorn, Uvicorn).
- Configure HTTPS and secure cookies.
- Do not run Django's development server in production.

---

## 12.3 Database and Migrations

- Apply database migrations through a controlled deployment process.
- Back up databases and periodically verify restoration.
- Have a rollback or recovery plan.

---

## 12.4 Observability

- Configure structured logs, metrics, error monitoring, and health checks.
- Monitor database performance, request latency, background jobs, and error rates.

---

## 12.5 Dependencies

- Keep dependencies updated through a reviewed process.

---

## 12.6 Deployment Checklist

- [ ] Secrets in environment variables / secret manager
- [ ] `python manage.py check --deploy` passes
- [ ] Production WSGI/ASGI server configured
- [ ] HTTPS and secure cookies enabled
- [ ] Migrations applied through controlled process
- [ ] Database backup verified and restoration tested
- [ ] Rollback plan documented
- [ ] Structured logging and error monitoring active
- [ ] Health checks configured
- [ ] Dependencies reviewed and up to date

