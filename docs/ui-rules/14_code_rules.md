# §14 — Code Rules & Minimalism

> **Back to index:** [00_index.md](./00_index.md)

---

## 14.1 Less Lines of Code (LOC) Strategies

1. **Extract Repeated Utility Sequences:** If you write `px-4 py-2 text-sm font-medium rounded-lg border border-slate-200` more than three times, extract it to a `.btn-secondary` or `.input` class in `components.css`.
2. **Alpine.js for Client State Only:** Use Alpine only for local toggles (modals, dropdowns, tabs). Do not re-implement data fetching or client routing in Alpine; let HTMX handle data swaps.
3. **Template Includes Over Duplication:** Pass arguments into `components/_stat_card.html` rather than duplicating markup blocks.

---

## 14.2 Tailwind Class Ordering Standards

To ensure readable and diff-friendly templates, follow the standard box-model order (enforced automatically via `prettier-plugin-tailwindcss`):

$$\text{Display/Layout} \longrightarrow \text{Box Model (Width/Height)} \longrightarrow \text{Spacing (Margin/Padding)} \longrightarrow \text{Typography} \longrightarrow \text{Background/Colors} \longrightarrow \text{Borders/Effects} \longrightarrow \text{Transitions/State}$$

```html
<!-- Example of standard class ordering -->
<div class="flex items-center justify-between w-full p-4 text-sm font-semibold text-slate-800 bg-white border border-slate-200 rounded-xl shadow-card hover:shadow-hover transition-all duration-200">
```

