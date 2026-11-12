# §5 — Database Design and Integrity

> **Source:** Django Backend Engineering Standards  
> **Back to index:** [00_index.md](./00_index.md)

---

## 5.1 Data Modeling

- Design relationships intentionally: one-to-one, one-to-many, and many-to-many.
- Choose appropriate field types, nullability, defaults, and deletion behavior.
- Use explicit `related_name` values when they improve clarity.
- Use a custom user model at the beginning of a new project if the application needs one.
- Avoid storing derived or duplicated values unless there is a documented reason, such as a historical snapshot or performance requirement.
- Document intentional denormalization and how it stays consistent.

---

## 5.2 Normalization and Duplication

- Normalize relational data to reduce unnecessary redundancy and update anomalies.
- Do not confuse database normalization with DRY: normalization concerns data structure; DRY concerns repeated knowledge or logic.
- Use foreign keys and shared reference records instead of copying the same mutable information into many rows.
- Preserve historical snapshots intentionally when business requirements require the original value to remain unchanged.

---

## 5.3 Constraints and Transactions

> [!IMPORTANT]
> Database constraints are the final integrity boundary. Never rely on frontend or serializer validation alone.

- Enforce important invariants in the database using `UniqueConstraint`, `CheckConstraint`, foreign keys, and appropriate field constraints.
- Use `transaction.atomic()` when related writes must succeed or fail together.
- Consider `select_for_update()` and database constraints for race-prone operations.
- Handle `IntegrityError` deliberately and return a safe, meaningful response.
- Make critical operations safe under concurrent requests.

---

## 5.4 Migrations

- Commit migrations with the code changes that require them.
- Review generated migrations before applying them.
- Avoid editing an already-applied migration in a shared environment.
- Plan potentially destructive or large migrations carefully.
- Consider backward-compatible expand-and-contract changes for deployments where old and new application versions may overlap.
- Test migrations against representative data when the change is risky.

---

## 5.5 Query Performance

- Watch for N+1 queries.
- Use `select_related()` for suitable foreign-key and one-to-one relationships.
- Use `prefetch_related()` for many-to-many and reverse relationships.
- Retrieve only necessary fields when it helps.
- Paginate large result sets.
- Add indexes based on real query patterns and query plans, not by default on every field.
- Use `QuerySet.explain()` and PostgreSQL query plans to investigate slow queries.
- Use bulk operations when appropriate and understand their behavior, including signals and model `save()` calls.
- **Measure before optimizing.**

