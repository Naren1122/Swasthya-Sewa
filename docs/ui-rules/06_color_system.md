# §6 — Color System

> **Back to index:** [00_index.md](./00_index.md)

---

## 6.1 The 60-30-10 Rule

| Role | % | Tailwind / Variable | Description |
|---|---|---|---|
| **Background (neutral)** | 60% | `bg-[--color-bg]` / `#f8fafc` | Page background — never pure white |
| **Surface** | 30% | `bg-[--color-surface]` / `#ffffff` | Cards, panels, navbar |
| **Brand accent** | 10% | `bg-[--color-primary]` / `#3b82f6` | Buttons, links, highlights — sparingly |

> **Never** use pure `#000000` or `#ffffff`. Use `--color-text` (`#0f172a`) and `--color-bg` (`#f8fafc`).

---

## 6.2 Status Color System

Add to `static/css/base.css`. Used for appointment/payment/lab status badges — **consistent across all components**.

```css
/* Status modifier classes — pair with .badge-status */
.status-confirmed  { --s-bg: #dcfce7; --s-text: #15803d; --s-dot: #22c55e; }
.status-pending    { --s-bg: #fef9c3; --s-text: #a16207; --s-dot: #eab308; }
.status-cancelled  { --s-bg: #fee2e2; --s-text: #b91c1c; --s-dot: #ef4444; }
.status-expired    { --s-bg: #f1f5f9; --s-text: #64748b; --s-dot: #94a3b8; }
.status-inprogress { --s-bg: #eff6ff; --s-text: #1d4ed8; --s-dot: #3b82f6; }
.status-completed  { --s-bg: #f0fdf4; --s-text: #166534; --s-dot: #16a34a; }
.status-held       { --s-bg: #faf5ff; --s-text: #7e22ce; --s-dot: #a855f7; }
.status-no-show    { --s-bg: #fff7ed; --s-text: #c2410c; --s-dot: #f97316; }

/* One reusable badge — works for ALL statuses */
.badge-status {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-pill);
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--s-bg);
  color: var(--s-text);
}
.badge-status::before {
  content: "";
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--s-dot);
  flex-shrink: 0;
}
```

**Usage:**
```html
<span class="badge-status status-confirmed">Confirmed</span>
<span class="badge-status status-pending">Pending</span>
<span class="badge-status status-cancelled">Cancelled</span>
```

---

## 6.3 Semantic Palette Reference

| Semantic Role | Color | Hex | Use |
|---|---|---|---|
| Primary | Blue | `#3b82f6` | CTAs, links, focus rings |
| Success | Green | `#22c55e` | Confirmed, paid, complete |
| Warning | Amber | `#f59e0b` | Pending, low stock, expiry |
| Error | Red | `#ef4444` | Cancelled, failed, overdue |
| Info | Blue | `#3b82f6` | Informational alerts |
| Neutral | Slate | `#94a3b8` | Expired, inactive, disabled |

---

## 6.4 Contrast Rules (WCAG AA)

| Text type | Minimum ratio |
|---|---|
| Body / UI text | **4.5 : 1** |
| Large text (≥18px bold) | **3 : 1** |
| Icon-only indicators | **3 : 1** |

> Check every foreground/background pair at [a11y.dev/contrast](https://a11y.dev/contrast)

