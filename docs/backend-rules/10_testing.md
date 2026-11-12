# §10 — Testing Standards

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

Testing must happen **continuously**, not only after the entire application has been completed.

---

## 10.1 Required Feature Workflow

For each feature, follow this sequence:

1. **Requirement and acceptance criteria** — Confirm expected behavior, permissions, validation rules, and failure cases.
2. **Implementation** — Develop the smallest coherent feature slice.
3. **Unit testing** — Test isolated functions and business rules.
4. **Integration testing** — Test interactions between services, serializers, models, and the database.
5. **API testing** — Test actual HTTP behavior, status codes, response bodies, authentication, and permissions.
6. **E2E testing** — Test the complete user journey through the actual frontend and backend when the feature has a user-facing workflow.
7. **Code review and bug fixing** — Review correctness, security, readability, and performance; fix findings.
8. **Regression testing** — Rerun affected tests and relevant broader suites after fixes.

> Some test categories may overlap. Keep tests at the level that best verifies the behavior without unnecessary duplication.

---

## 10.2 Registration Feature Example

### A. Develop Registration API

- Create the registration endpoint.
- Implement the serializer and validation.
- Implement business logic.
- Hash passwords using Django's supported password utilities.
- Enforce unique email requirements at the database level where applicable.
- Ensure the response never returns the password or password hash.
- Define expected success and error responses.

### B. Unit Testing

Test individual rules and functions:

- Password validation.
- Email validation and normalization rules.
- Required-field validation.
- Password hashing behavior.
- Any isolated registration business rules.
- Custom validators and helper functions.

### C. Integration Testing

Test components working together:

- Serializer validation and service behavior.
- User creation and database persistence.
- Database uniqueness constraints.
- Transaction behavior where applicable.
- Signals or related side effects, if used.
- Failure behavior when a dependent operation fails.

### D. API Testing

Test the endpoint through HTTP requests:

- Valid registration.
- Invalid email.
- Weak or invalid password.
- Duplicate email.
- Missing required fields.
- Malformed request body.
- Unexpected or disallowed fields.
- Correct status codes and response structure.
- Password is not exposed in the response.
- Correct behavior for unauthenticated or authenticated access, according to the endpoint's design.
- Repeated submission behavior.

### E. E2E Testing

Use a browser automation tool such as Playwright:

- Open the real registration page.
- Enter valid details.
- Submit the form.
- Verify success feedback and expected navigation.
- Verify the account was created through an appropriate test assertion.
- Test validation messages for invalid inputs.
- Test duplicate registration behavior.
- Verify loading and error states.

### F. Code Review and Bug Fixing

Review:

- Security and password handling.
- Duplicate-account race conditions.
- Validation completeness.
- Authorization.
- Response consistency.
- Database constraints.
- Query behavior.
- Code organization and naming.

Fix issues and rerun relevant unit, integration, API, and E2E tests.

---

## 10.3 Testing Principles

- Test success paths, failure paths, boundary conditions, and permission boundaries.
- Keep tests deterministic and isolated.
- Use a test database and safe test settings.
- Mock external services in unit tests.
- Use integration tests when real component interaction matters.
- Avoid depending on production services or real user data.
- Test concurrent operations when the business flow is race-prone.
- Keep tests readable and focused on observable behavior.
- Do not test implementation details unnecessarily.
- Add regression tests for bugs that have been fixed.
- Run the smallest relevant test set during development and the broader suite before merging.

---

## 10.4 Suggested Testing Tools

| Tool | Purpose |
|---|---|
| `pytest` / Django test framework | Test runner |
| `pytest-django` | pytest integration for Django |
| DRF `APIClient` / `APITestCase` | API-level HTTP tests |
| Factory Boy / fixtures | Test data generation |
| Playwright | Browser E2E tests |
| `coverage.py` / `pytest-cov` | Coverage reporting |
| Locust | Load testing |

> Coverage percentage is a signal, not proof of test quality. Prioritize meaningful behavior and risk coverage.

