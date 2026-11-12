# §8 — Security Standards

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

Apply **defense in depth** and **least privilege** throughout.

---

## 8.1 Authentication and Authorization

- Use Django's password hashing; never store plaintext passwords.
- Enforce authentication and authorization separately.
- Check object ownership and tenant boundaries on every relevant resource access.
- Use DRF permission classes and scoped querysets appropriately.
- Never trust user IDs, role values, prices, ownership fields, or permissions supplied by the client.

---

## 8.2 Secrets and Configuration

- Keep secrets in environment variables or a suitable secret manager.
- Set `DEBUG = False` in production.
- Configure `ALLOWED_HOSTS`, HTTPS, secure cookies, CSRF, and CORS correctly.
- Do not disable CSRF protection as a shortcut.
- Restrict CORS to required origins.

---

## 8.3 Input and File Handling

- Apply throttling/rate limits to sensitive or abuse-prone endpoints.
- Validate uploaded file size, type, content, and access permissions.
- Use ORM parameterization; do not build SQL from untrusted strings.

---

## 8.4 Ongoing Security Hygiene

- Keep dependencies patched and review security advisories.
- Avoid leaking whether sensitive accounts or records exist when that would create a security risk.
- Protect secrets and personal data in logs, fixtures, error messages, and test output.

---

## 8.5 Quick Checklist

- [ ] Passwords hashed, never plaintext
- [ ] Object-level authorization on every resource endpoint
- [ ] Secrets in environment variables, not source control
- [ ] `DEBUG = False` in production
- [ ] CSRF and CORS configured correctly
- [ ] Rate limiting on sensitive endpoints
- [ ] File uploads validated (size, type, content)
- [ ] No raw SQL from untrusted input
- [ ] Dependencies reviewed and patched
- [ ] No sensitive data in logs or test fixtures

