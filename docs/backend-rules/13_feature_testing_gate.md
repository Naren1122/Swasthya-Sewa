# §13 — Feature Development and Testing Gate

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

Use this repeatable checklist for every feature or development phase.

---

## 13.1 Feature Checklist

```text
[ ] Requirements and acceptance criteria understood
[ ] User flow and edge cases reviewed
[ ] Data model and migration reviewed, if needed
[ ] API contract and permissions defined
[ ] Implementation completed
[ ] Unit tests written and passed
[ ] Integration tests written and passed
[ ] API tests written and passed
[ ] E2E tests written and passed, if user-facing
[ ] Security and data-integrity checks completed
[ ] Code review completed
[ ] Bugs fixed
[ ] Relevant tests rerun after fixes
[ ] Documentation updated
[ ] Ready to merge
```

---

## 13.2 Testing Gate Rules

> [!IMPORTANT]
> Do not move a feature to "done" while required tests are failing.

- Do not skip a test category silently. If a category is not applicable, record why.
- If a test cannot run because an environment or dependency is unavailable, report that clearly; do not mark it as passed.
- After changing code to fix a bug, rerun the tests that cover the affected behavior.
- Before merging, run the project's required quality checks and relevant regression suite.
- For high-risk changes, require additional review and broader testing.

