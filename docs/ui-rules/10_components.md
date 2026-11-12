# §10 — Component Patterns

> **Back to index:** [00_index.md](./00_index.md)

---

## 10.1 `static/css/components.css`

```css
/* Card */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  transition: box-shadow var(--transition-base), transform var(--transition-base);
}
.card:hover { box-shadow: var(--shadow-hover); transform: translateY(-1px); }

/* Buttons */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem; font-weight: 600;
  border-radius: var(--radius-sm);
  border: 1.5px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  min-height: 2.5rem;
}
.btn:active { transform: scale(0.97); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; pointer-events: none; }
.btn-primary { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.btn-primary:hover { background: var(--color-primary-dark); }
.btn-secondary { background: transparent; color: var(--color-text); border-color: var(--color-border); }
.btn-secondary:hover { background: var(--color-bg); border-color: var(--color-primary); color: var(--color-primary); }
.btn-danger { background: var(--color-error); color: #fff; }
.btn-danger:hover { background: #dc2626; }
.btn-sm { padding: 0.375rem 0.75rem; font-size: 0.75rem; min-height: 2rem; }

/* Inputs */
.input {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  background: var(--color-surface);
  color: var(--color-text);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}
.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}
.input.error { border-color: var(--color-error); }

/* Form Group */
.form-group { display: flex; flex-direction: column; gap: var(--space-1); }
.form-label { font-size: 0.8125rem; font-weight: 600; color: var(--color-text-secondary); }
.form-error { font-size: 0.75rem; color: var(--color-error); display: flex; align-items: center; gap: 4px; }

/* Table */
.table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}
.table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.table th {
  padding: var(--space-3) var(--space-4);
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
  color: var(--color-text-secondary);
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}
.table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
}
.table tbody tr:hover { background: var(--color-bg); }

/* Stat Card */
.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}
.stat-value { font-size: 2rem; font-weight: 700; line-height: 1; }
.stat-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-secondary); }
```

