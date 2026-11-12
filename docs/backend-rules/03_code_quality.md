# §3 — Code Quality and Maintainability

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 3.1 Single Responsibility Principle (SRP)

- Give each module, class, and function a clear responsibility.
- Keep views focused on HTTP request/response coordination.
- Keep serializers focused on input validation and representation.
- Put reusable business operations in service functions or service classes when useful.
- Put complex reusable data retrieval in selectors, custom QuerySets, or managers where appropriate.
- Avoid "God classes", oversized views, and files that mix unrelated business domains.

---

## 3.2 DRY — Don't Repeat Yourself

- Reuse genuinely shared business rules, validators, permissions, and query logic.
- Extract repeated behavior when there is one stable concept or rule to maintain.
- Avoid copy-pasting authorization or validation rules across endpoints.
- Do not force unrelated logic into a generic helper just because two code blocks look similar.
- Prefer clear duplication over a complicated abstraction when the behaviors are likely to evolve differently.

---

## 3.3 KISS and YAGNI

- Choose the simplest design that meets current requirements.
- Do not add features, packages, abstractions, or infrastructure without a current need.
- Avoid speculative generalization and premature optimization.
- Prefer readable code over clever or overly compact code.

---

## 3.4 SOLID and Related Design Principles

Apply these where they improve the design:

| Principle | Guidance |
|---|---|
| **SRP** | One clear responsibility per class/function. |
| **OCP** | Extend behavior without repeatedly modifying stable code, where practical. |
| **LSP** | Subtypes should honor the contracts of their base types. |
| **ISP** | Prefer focused interfaces over oversized interfaces. |
| **DIP** | Depend on stable abstractions where useful; avoid unnecessary tight coupling. |
| **High cohesion** | Keep related responsibilities together. |
| **Low coupling** | Minimize unnecessary dependencies between modules. |
| **Encapsulation** | Keep implementation details behind clear interfaces. |
| **Composition over inheritance** | Prefer composing smaller components when that is simpler. |
| **Explicit over implicit** | Make important behavior and dependencies understandable. |

---

## 3.5 File Size and Readability

- Keep files focused and easy to navigate.
- Split files when they contain multiple responsibilities or become difficult to review.
- There is no mandatory industry-wide line limit; do not split files just to hit an arbitrary number.
- Use descriptive names, small functions, consistent formatting, and type hints where they improve clarity.
- Avoid deeply nested conditionals and unnecessarily complex functions.
- Add comments to explain intent or non-obvious decisions, not to restate the code.

---

## 3.6 Dependency Management

- Reuse existing project dependencies where possible.
- Add a dependency only when it provides clear value.
- Check compatibility, maintenance status, security implications, and licensing before adding packages.
- Pin or constrain dependencies using the project's dependency-management approach.
- Do not silently upgrade major dependencies as part of an unrelated feature.

