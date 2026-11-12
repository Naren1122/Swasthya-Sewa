# §14 — AI Agent Work Protocol

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

For every coding task, the agent should follow this protocol.

---

## 14.1 Before Coding

1. Inspect relevant files and existing tests.
2. Identify the requirement and acceptance criteria.
3. Trace the current request/data flow.
4. Identify affected apps, models, APIs, permissions, and dependencies.
5. Identify risks and edge cases.
6. Propose a concise implementation plan for non-trivial changes.

---

## 14.2 While Coding

1. Make small, focused changes.
2. Follow existing conventions.
3. Keep business rules in the appropriate layer.
4. Add or update tests with the implementation.
5. Add migrations only when required.
6. Avoid unrelated refactoring.
7. Keep security and data integrity in mind.

---

## 14.3 After Coding

1. Run relevant unit tests.
2. Run relevant integration tests.
3. Run relevant API tests.
4. Run E2E tests for affected user journeys when applicable.
5. Run linting, formatting, type checks, and Django checks configured by the project.
6. Review the diff for accidental or unrelated changes.
7. Fix failures and rerun affected tests.
8. Summarize changed files, behavior, test commands and results, migrations, and remaining risks.

---

## 14.4 Required Completion Report

At the end of each task, provide:

```text
Implementation:
- What was added or changed.

Files:
- List the important files changed.

Database:
- Migrations added or changed, if any.

Tests executed:
- Unit:
- Integration:
- API:
- E2E:
- Other checks:

Results:
- Passed:
- Failed:
- Not run (with reason):

Risks / follow-up:
- Remaining issues or recommended next steps.
```

