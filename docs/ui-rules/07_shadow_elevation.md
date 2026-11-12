# §7 — Shadow & Elevation System

> **Back to index:** [00_index.md](./00_index.md)

---

## 7.1 Four-Level Elevation System

Use exactly **4 shadow levels**. Never invent new shadow values.

| Level | Variable | Value | Use |
|---|---|---|---|
| **0 — Flat** | none | — | Tables, page background sections |
| **1 — Raised** | `--shadow-card` | `0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)` | Cards, inputs, panels |
| **2 — Floating** | `--shadow-float` | `0 8px 24px rgba(0,0,0,0.10)` | Dropdowns, sticky nav, popovers |
| **3 — Modal** | `--shadow-modal` | `0 24px 48px rgba(0,0,0,0.18)` | Dialogs, drawers, full modals |

Hover upgrade: `--shadow-card` → `--shadow-hover` (`0 4px 12px rgba(0,0,0,0.08), 0 12px 32px rgba(0,0,0,0.06)`)

---

## 7.2 Shadow Utility Classes (add to `utilities.css`)

```css
.shadow-card   { box-shadow: var(--shadow-card); }
.shadow-hover  { box-shadow: var(--shadow-hover); }
.shadow-float  { box-shadow: var(--shadow-float); }
.shadow-modal  { box-shadow: var(--shadow-modal); }
```

---

## 7.3 Card Hover Pattern

```css
/* components.css */
.card {
  box-shadow: var(--shadow-card);
  transition: box-shadow var(--transition-base), transform var(--transition-base);
}
.card:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-1px);
}
```

---

## 7.4 Rules

- Never combine shadow + gradient + border on the same element — pick 2 max.
- Navbar uses `--shadow-float` when scrolled (add with Alpine.js scroll listener).
- Modals always use `--shadow-modal` + `backdrop-filter: blur(4px)` on the overlay.
- Disabled / inactive cards: `opacity: 0.6` — do not change their shadow.

