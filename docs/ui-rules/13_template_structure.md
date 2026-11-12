# §13 — Django Template Structure

> **Back to index:** [00_index.md](./00_index.md)

---

## 13.1 Folder Organization

```text
templates/
├── base.html                     # Core authenticated shell (Navbar, Sidebar, Toast Container)
├── base_auth.html                # Clean shell for Login/Register/Password Reset
├── partials/                     # Global reusable UI partials
│   ├── _navbar.html
│   ├── _sidebar.html
│   ├── _messages.html
│   └── _pagination.html
├── components/                   # Micro-components included via {% include %}
│   ├── _stat_card.html
│   ├── _badge.html
│   └── _empty_state.html
└── apps/                         # App-specific templates or inside apps/<app>/templates/
    ├── patients/
    │   ├── list.html             # Full page view
    │   ├── detail.html
    │   └── partials/             # HTMX fragments only
    │       ├── _patient_row.html
    │       └── _patient_table.html
    └── appointments/
        ├── calendar.html
        └── partials/
            └── _slot_list.html
```

---

## 13.2 Naming Convention Rules

1. **`_prefix.html`:** Any template prefixed with an underscore is a partial or HTMX fragment. It should never be rendered as a standalone page.
2. **Concise Partials:** Aim for fewer than 60 lines per partial. If a partial becomes too large, decompose it into smaller functional components.
3. **No Business Logic in Templates:** Templates only render variables and iterate loops; calculations belong in model properties or selectors.

