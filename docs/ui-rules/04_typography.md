# §4 — Typography System

> **Back to index:** [00_index.md](./00_index.md)

---

## 4.1 Font Setup (in `base.html` `<head>`)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
```

**Rule:** Maximum **2 typefaces** per project. Use weight + size variation within one family — never mix font families for hierarchy.

---

## 4.2 Type Scale Classes (add to `base.css`)

```css
/* Major Third ratio — 1.25× */
.text-display { font-size: 3.5rem;   font-weight: 800; line-height: 1.1;  letter-spacing: -0.02em; }
.text-h1      { font-size: 2.5rem;   font-weight: 700; line-height: 1.2;  letter-spacing: -0.015em; }
.text-h2      { font-size: 2rem;     font-weight: 700; line-height: 1.25; }
.text-h3      { font-size: 1.5rem;   font-weight: 600; line-height: 1.3; }
.text-h4      { font-size: 1.25rem;  font-weight: 600; line-height: 1.4; }
.text-body    { font-size: 1rem;     font-weight: 400; line-height: 1.6; }
.text-sm      { font-size: 0.875rem; line-height: 1.5; }
.text-xs      { font-size: 0.75rem;  line-height: 1.4; }
.text-label   { font-size: 0.75rem;  font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
```

---

## 4.3 Typography Rules

| Rule | Value |
|---|---|
| **Body font size** | `1rem` (16px) — never below `0.75rem` (12px) |
| **Body line-height** | `1.6` |
| **Line length** | `max-width: 70ch` on readable paragraphs |
| **Heading tracking** | Negative on large sizes (`-0.02em` for display) |
| **Label tracking** | Positive uppercase labels (`0.06em`) |
| **Font weights used** | 400 (body) · 500 (medium) · 600 (semibold) · 700 (bold) · 800 (display) |
| **Number of typefaces** | Max 2 — usually 1 (Inter) is enough |

---

## 4.4 Usage in Templates

```html
<!-- Page title -->
<h1 class="text-h2 text-[--color-text]">Patient List</h1>

<!-- Section label -->
<p class="text-label text-[--color-text-secondary]">Today's Appointments</p>

<!-- Body content -->
<p class="text-body max-w-[70ch]">
  MediCore manages your hospital's core workflows in one place.
</p>

<!-- Table column header -->
<th class="text-label text-[--color-text-secondary]">Patient Name</th>
```

