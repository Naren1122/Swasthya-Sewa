# §11 — Responsive Design Rules

> **Back to index:** [00_index.md](./00_index.md)

---

## 11.1 Mobile-First Philosophy

Always define base styles for mobile screens first, then progressively enhance layout via `sm:`, `md:`, `lg:`, `xl:`.

```html
<!-- Mobile: 1 column -> Tablet: 2 columns -> Desktop: 4 columns -->
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
```

---

## 11.2 Standard Breakpoint Reference

| Prefix | Min Width | Target Devices | Key Layout Role |
|---|---|---|---|
| (default) | `0px` | Phones (<640px) | Single column, full-width inputs, tap targets $\ge 44px$ |
| `sm:` | `640px` | Large phones / phablets | 2-column cards, modal dialogs centered |
| `md:` | `768px` | Tablets | Drawer sidebar toggleable, table views |
| `lg:` | `1024px` | Laptops / Desktops | Persistent sidebar (250px), multi-column grids |
| `xl:` | `1280px` | Large Monitors | Max content container capped at `max-w-7xl` |

---

## 11.3 Mobile Sidebar Pattern (Alpine.js)

```html
<div x-data="{ sidebarOpen: false }">
  <!-- Mobile Header Button -->
  <button @click="sidebarOpen = true" class="lg:hidden btn btn-ghost p-2" aria-label="Open navigation">
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
  </button>

  <!-- Mobile Backdrop -->
  <div x-show="sidebarOpen" 
       @click="sidebarOpen = false"
       x-transition:enter="transition-opacity ease-linear duration-200"
       x-transition:enter-start="opacity-0"
       x-transition:enter-end="opacity-100"
       x-transition:leave="transition-opacity ease-linear duration-200"
       x-transition:leave-start="opacity-100"
       x-transition:leave-end="opacity-0"
       class="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden"
       style="display: none;"></div>

  <!-- Sidebar -->
  <aside :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
         class="fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-slate-200 transition-transform duration-200 ease-in-out lg:static lg:translate-x-0">
    <div class="p-4 border-b border-slate-100 flex items-center justify-between">
      <span class="font-bold text-lg text-slate-800">MediCore</span>
      <button @click="sidebarOpen = false" class="lg:hidden text-slate-400 hover:text-slate-600">✕</button>
    </div>
    <!-- Links -->
  </aside>
</div>
```

