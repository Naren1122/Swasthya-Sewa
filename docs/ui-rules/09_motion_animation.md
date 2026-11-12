# §9 — Motion, Transitions & Micro-Interactions

> **Back to index:** [00_index.md](./00_index.md)

---

## 9.1 Global Transition Utilities

```css
/* static/css/utilities.css */
.transition-fast { transition: all var(--transition-fast); } /* 150ms ease-out */
.transition-base { transition: all var(--transition-base); } /* 200ms ease-out */
.transition-slow { transition: all var(--transition-slow); } /* 300ms ease-out */

/* Card hover lift */
.hover-lift {
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}
.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

/* Button click tactile feedback */
.press-effect:active {
  transform: scale(0.97);
}

/* HTMX swapped element entrance */
.htmx-added {
  animation: fadeIn var(--transition-base);
}

/* Loading Shimmer Skeleton */
@keyframes shimmer {
  from { background-position: -200% 0; }
  to   { background-position:  200% 0; }
}
.skeleton {
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

/* HTMX Spinner Indicator */
.htmx-indicator {
  display: none;
  width: 1.25rem; height: 1.25rem;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 600ms linear infinite;
}
.htmx-request .htmx-indicator { display: inline-block; }
.htmx-request.htmx-indicator  { display: inline-block; }
```

---

## 9.2 Key Animation Principles

1. **Enter Fast, Exit Faster:** 150–200ms for entering components, 100–150ms for exiting components.
2. **Purposeful Only:** Animations communicate state changes or focus shifts, not decorative fluff.
3. **Respect Reduced Motion:** Provide `@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }`.

