# §1 — Instructions for AI Agents

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 1.1 Agent Responsibilities

When working on this codebase, agents must:

1. Read the existing project structure, settings, dependencies, conventions, and tests before changing code.
2. Follow the project's established architecture unless there is a clear reason to improve it.
3. Avoid rewriting unrelated code or introducing unnecessary dependencies.
4. Clarify ambiguous requirements rather than inventing business rules.
5. Make small, focused changes that are easy to review.
6. Implement tests alongside each feature; do not postpone all testing until the end.
7. Run the relevant tests and quality checks after changes.
8. Report what changed, what tests were run, their results, and any remaining risks.
9. Never claim a test passed unless it was actually executed successfully.
10. Do not weaken, delete, skip, or rewrite tests merely to make a failing build pass. Fix the underlying issue or explain why a test needs to change.
11. Never expose secrets, credentials, personal data, or sensitive production information in code, logs, test fixtures, or responses.
12. Do not make broad architectural changes without explaining the trade-offs and obtaining approval when the change materially affects the project.

---

## 1.2 Definition of Done

A feature is not complete merely because its code has been written. It is complete when:

- [ ] Requirements and acceptance criteria are met.
- [ ] Input validation and authorization are implemented.
- [ ] Relevant unit, integration, and API tests pass.
- [ ] Relevant frontend E2E tests pass when the feature has a user-facing workflow.
- [ ] Database migrations are included and checked.
- [ ] Linting, formatting, and applicable static checks pass.
- [ ] Error handling and logging are appropriate.
- [ ] Documentation is updated where needed.
- [ ] Code review findings are resolved.
- [ ] Known limitations and follow-up work are documented.

