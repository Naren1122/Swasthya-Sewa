# §11 — Code Review Standards

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 11.1 Review Checklist

Review each change for:

- [ ] Correctness against requirements and acceptance criteria
- [ ] Simplicity and readability
- [ ] Appropriate separation of responsibilities
- [ ] Validation and authorization
- [ ] Data integrity and concurrency
- [ ] Query performance
- [ ] Consistent API behavior
- [ ] Error handling and logging
- [ ] Test quality and missing edge cases
- [ ] Migration safety
- [ ] Security and privacy
- [ ] Unnecessary dependencies or unrelated changes

---

## 11.2 Reviewer Conduct

- A reviewer should explain **why** a change is needed and suggest a concrete improvement.
- Do not make purely stylistic changes that conflict with established project conventions without a good reason.

