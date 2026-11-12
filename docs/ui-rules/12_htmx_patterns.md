# §12 — HTMX UI Patterns

> **Back to index:** [00_index.md](./00_index.md)

---

## 12.1 Core Directives & Standards

1. **Target Precision:** Always specify targeted element IDs with `hx-target="#element-id"`. Avoid body replacements.
2. **Swap Strategy:**
   - `hx-swap="outerHTML"` for updating an element in place (e.g., status badges, table rows).
   - `hx-swap="innerHTML"` for lists or modal bodies.
   - `hx-swap="beforeend"` / `afterbegin` for infinite scroll or prepending new records.
3. **Always Show Indicators:** Use `hx-indicator="#loading-spinner"` on all network requests.
4. **CSRF Safety:** Include `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'` on `<body/>` or the form.

---

## 12.2 Practical Snippets

### Instant Search (Debounced)
```html
<div class="relative">
  <input type="search"
         name="q"
         placeholder="Search by patient name, phone, or ID..."
         class="input"
         hx-get="{% url 'patients:search' %}"
         hx-trigger="keyup changed delay:300ms, search"
         hx-target="#search-results"
         hx-indicator="#search-spinner">
  <span id="search-spinner" class="htmx-indicator absolute right-3 top-3"></span>
</div>
<div id="search-results" class="mt-2"></div>
```

### Async Form Submission with Server-Side Validation
```html
<form hx-post="{% url 'appointments:book' %}"
      hx-target="#appointment-modal-content"
      hx-swap="innerHTML"
      hx-indicator="#submit-spinner"
      class="space-y-4">
  {% csrf_token %}
  
  <div class="form-group">
    <label class="form-label">Doctor Availability Slot</label>
    {{ form.slot }}
    {% if form.slot.errors %}
      <p class="form-error">{{ form.slot.errors.0 }}</p>
    {% endif %}
  </div>

  <div class="flex justify-end gap-2 pt-2">
    <span id="submit-spinner" class="htmx-indicator"></span>
    <button type="submit" class="btn btn-primary press-effect">Confirm Booking</button>
  </div>
</form>
```

### Confirmation Modal on Destructive Actions
```html
<button class="btn btn-sm btn-danger press-effect"
        hx-delete="{% url 'appointments:cancel' appointment.id %}"
        hx-target="#appointment-row-{{ appointment.id }}"
        hx-swap="outerHTML swap:200ms"
        hx-confirm="Are you sure you want to cancel this appointment?">
  Cancel
</button>
```

