# §15 — Accessibility (a11y) Standards

> **Back to index:** [00_index.md](./00_index.md)

---

## 15.1 Core Requirements

- **Contrast Ratios:** Maintain at least 4.5:1 for body and standard text against backgrounds; 3:1 for large headers and status icons.
- **Explicit Labels:** Every `<input>` must have a corresponding `<label for="id">` or an explicit `aria-label`. Placeholder text is not a label.
- **Focus Rings:** Never strip default focus styles without providing a distinct `:focus-visible` replacement (`outline: 2px solid var(--color-primary); outline-offset: 2px`).
- **Interactive Semantics:** Use `<button>` for actions and `<a>` for navigational URLs. Do not attach click handlers to `<div>` elements.

---

## 15.2 Screen-Reader Friendly HTMX Containers

```html
<!-- Live regions inform assistive technology when dynamic HTMX swaps complete -->
<div id="appointment-status" 
     aria-live="polite" 
     class="badge-status status-confirmed">
  Confirmed
</div>
```

