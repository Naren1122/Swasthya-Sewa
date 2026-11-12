# §5 — Spacing & Layout

> **Back to index:** [00_index.md](./00_index.md)

---

## 5.1 The 8px Grid — Non-Negotiable

Every spacing value must be a multiple of 4 (prefer multiples of 8):

| Value | px | Use |
|---|---|---|
| `var(--space-1)` / `p-1` | 4px | Micro gaps — icon-to-text, inline elements |
| `var(--space-2)` / `p-2` | 8px | Between small elements, label-to-input gap |
| `var(--space-3)` / `p-3` | 12px | Input internal padding (vertical) |
| `var(--space-4)` / `p-4` | 16px | Standard gap, form field spacing |
| `var(--space-6)` / `p-6` | 24px | Card internal padding (minimum) |
| `var(--space-8)` / `p-8` | 32px | Section heading margin |
| `var(--space-12)` / `p-12` | 48px | Between major sections |
| `var(--space-16)` / `p-16` | 64px | Hero / full-section padding |

---

## 5.2 Base Page Layout — `templates/base.html`

```html
<!DOCTYPE html>
<html lang="en" class="h-full">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}MediCore{% endblock %}</title>
  {% load static %}
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
  <link rel="stylesheet" href="{% static 'css/output.css' %}">
  <script src="https://unpkg.com/htmx.org@2/dist/htmx.min.js" defer></script>
  <script src="https://unpkg.com/alpinejs@3/dist/cdn.min.js" defer></script>
</head>
<body class="h-full"
      hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

  {% include "partials/_navbar.html" %}

  <div class="flex h-[calc(100vh-64px)]">
    {% block sidebar %}{% endblock %}

    <main class="flex-1 overflow-y-auto p-6 lg:p-8">
      <div class="mx-auto max-w-7xl">
        {% include "partials/_messages.html" %}
        {% block content %}{% endblock %}
      </div>
    </main>
  </div>

  {% block scripts %}{% endblock %}
</body>
</html>
```

---

## 5.3 Standard Layout Snippets

```html
<!-- Stats grid: 2-col mobile → 4-col desktop -->
<div class="grid grid-cols-2 gap-4 md:grid-cols-4">

<!-- Content + sidebar -->
<div class="flex flex-col gap-6 lg:flex-row">
  <aside class="lg:w-72 lg:flex-shrink-0">...</aside>
  <div class="flex-1 min-w-0">...</div>
</div>

<!-- Card grid: 1 → 2 → 3 col -->
<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">

<!-- Table: always wrap for horizontal scroll on mobile -->
<div class="overflow-x-auto rounded-xl border border-[--color-border]">
  <table class="table w-full">...</table>
</div>

<!-- Page header: title left, action right -->
<div class="page-header">
  <div>
    <h1 class="page-title">Patients</h1>
    <p class="page-subtitle">142 total patients</p>
  </div>
  <button class="btn btn-primary">Add Patient</button>
</div>
```

---

## 5.4 Proximity Rule

> Related elements are **close**. Unrelated elements have **generous gaps**.

```html
<!-- ✅ Correct — label and input are tight (8px), fields have space between (16px) -->
<div class="space-y-4">
  <div class="form-group">          <!-- label 8px above input -->
    <label class="form-label">Name</label>
    <input class="input">
  </div>
  <div class="form-group">
    <label class="form-label">Email</label>
    <input class="input">
  </div>
</div>
```

