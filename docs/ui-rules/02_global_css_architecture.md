# §2 — Global CSS Architecture

> **Back to index:** [00_index.md](./00_index.md)

---

## 2.1 File Structure — Keep It Flat (5 files max)

```
static/
└── css/
    ├── input.css         ← Tailwind entry point (@import all below)
    ├── base.css          ← CSS variables, resets, global rules
    ├── components.css    ← Reusable component classes (@apply or plain CSS)
    └── utilities.css     ← One-off helpers not covered by Tailwind
```

---

## 2.2 `static/css/input.css`

```css
@import "tailwindcss";
@import "./base.css";
@import "./components.css";
@import "./utilities.css";
```

---

## 2.3 Build Command

```bash
# Development (watch mode)
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch

# Production (minified)
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify
```

---

## 2.4 Django Static Settings

```python
# settings/base.py
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Production — whitenoise
MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    ...
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

---

## 2.5 Golden Rules

| Rule | Reason |
|---|---|
| **Never write `style=""`** | Unmaintainable and unsearchable |
| **Never hardcode hex colors** | Use CSS variables from `base.css` |
| **Never repeat a Tailwind combo > 3×** | Extract to `components.css` |
| **One `output.css` served to browser** | Built from `input.css` — never edit output directly |

