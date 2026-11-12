# §1 — Libraries & Setup

> **Back to index:** [00_index.md](./00_index.md)

---

## 1.1 Core Stack

| Library | Version | Purpose |
|---|---|---|
| **Tailwind CSS** | v4 | Utility-first CSS framework |
| **HTMX** | v2.x | Hypermedia / partial HTML swaps |
| **Alpine.js** | v3.x | Minimal JS reactivity (dropdowns, modals, toggles) |
| **DaisyUI** | v5 | Pre-built Tailwind component plugin |
| **Lucide Icons** | latest | Consistent SVG icon set |
| **django-htmx** | latest | Django middleware + HTMX helpers |
| **whitenoise** | latest | Static file serving in production |
| **django-compressor** | latest | CSS/JS minification |

## 1.2 Optional Enhancements

| Library | Purpose |
|---|---|
| **hyperscript** (`_hyperscript`) | Inline scripting companion to HTMX |
| **Tom Select** | Beautiful select / autocomplete inputs |
| **flatpickr** | Lightweight date & time picker |
| **Chart.js** | Dashboard charts (small footprint) |
| **htmx-ext-loading-states** | Auto loading states on HTMX requests |
| **htmx-ext-response-targets** | Target different elements on success/error |
| **Toastify.js** | Toast notifications (~2 KB) |

---

## 1.3 Install Commands

### Python / Django
```bash
pip install django-htmx whitenoise django-compressor
```

### Node / CSS
```bash
npm i tailwindcss@next daisyui@next @tailwindcss/forms @tailwindcss/typography
npm i -D prettier prettier-plugin-tailwindcss
```

---

## 1.4 CDN Scripts (in `base.html`)

```html
<script src="https://unpkg.com/htmx.org@2/dist/htmx.min.js" defer></script>
<script src="https://unpkg.com/alpinejs@3/dist/cdn.min.js" defer></script>
```

---

## 1.5 `tailwind.config.js`

```js
export default {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        mono: ["JetBrains Mono", "ui-monospace"],
      },
      colors: {
        brand: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",   // primary
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
      },
      animation: {
        "fade-in":    "fadeIn 200ms ease-out",
        "slide-up":   "slideUp 250ms ease-out",
        "slide-down": "slideDown 200ms ease-out",
      },
      keyframes: {
        fadeIn:    { from: { opacity: 0 },
                     to:   { opacity: 1 } },
        slideUp:   { from: { opacity: 0, transform: "translateY(8px)" },
                     to:   { opacity: 1, transform: "translateY(0)" } },
        slideDown: { from: { opacity: 0, transform: "translateY(-8px)" },
                     to:   { opacity: 1, transform: "translateY(0)" } },
      },
      boxShadow: {
        "card":       "0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.08), 0 12px 32px rgba(0,0,0,0.06)",
        "float":      "0 8px 24px rgba(0,0,0,0.10)",
        "modal":      "0 24px 48px rgba(0,0,0,0.18)",
      },
    },
  },
  plugins: [
    require("daisyui"),
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
}
```

