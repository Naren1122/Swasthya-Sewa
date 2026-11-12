# §3 — Design Tokens (CSS Variables)

> **Back to index:** [00_index.md](./00_index.md)  
> Define once in `static/css/base.css` — reference everywhere. Never hardcode a value.

---

## 3.1 Full Token File — `static/css/base.css`

```css
/* ════════════════════════════════════════
   DESIGN TOKENS
   ════════════════════════════════════════ */
:root {

  /* ── Brand ── */
  --color-primary:       #3b82f6;
  --color-primary-dark:  #2563eb;
  --color-primary-light: #eff6ff;

  /* ── Semantic Status ── */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error:   #ef4444;
  --color-info:    #3b82f6;

  /* ── Neutrals ── */
  --color-bg:             #f8fafc;  /* page background  — never #fff */
  --color-surface:        #ffffff;  /* cards, panels    */
  --color-border:         #e2e8f0;  /* all borders      */
  --color-muted:          #94a3b8;  /* placeholder text */
  --color-text:           #0f172a;  /* body text        — never #000 */
  --color-text-secondary: #475569;  /* labels, captions */

  /* ── Spacing (8px grid) ── */
  --space-1:  0.25rem;  /*  4px */
  --space-2:  0.5rem;   /*  8px */
  --space-3:  0.75rem;  /* 12px */
  --space-4:  1rem;     /* 16px */
  --space-6:  1.5rem;   /* 24px */
  --space-8:  2rem;     /* 32px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */

  /* ── Border Radius ── */
  --radius-sm:   0.375rem; /*  6px — inputs, tags   */
  --radius-md:   0.75rem;  /* 12px — cards, buttons */
  --radius-lg:   1rem;     /* 16px — modals         */
  --radius-pill: 9999px;   /* badges                */

  /* ── Shadows ── */
  --shadow-card:  0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
  --shadow-hover: 0 4px 12px rgba(0,0,0,0.08), 0 12px 32px rgba(0,0,0,0.06);
  --shadow-float: 0 8px 24px rgba(0,0,0,0.10);
  --shadow-modal: 0 24px 48px rgba(0,0,0,0.18);

  /* ── Transitions ── */
  --transition-fast: 150ms ease-out;
  --transition-base: 200ms ease-out;
  --transition-slow: 300ms ease-out;

  /* ── Typography ── */
  --font-sans: "Inter", ui-sans-serif, system-ui;
  --font-mono: "JetBrains Mono", ui-monospace;
}


/* ════════════════════════════════════════
   GLOBAL RESETS
   ════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html {
  font-family: var(--font-sans);
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  scroll-behavior: smooth;
}

body {
  background-color: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
}

/* Custom focus ring — never remove without a replacement */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}

img, video { max-width: 100%; display: block; }

p, h1, h2, h3, h4, h5, h6 { overflow-wrap: break-word; }
```

