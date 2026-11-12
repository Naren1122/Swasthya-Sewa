# §16 — UI/UX Quick Reference Cheat Sheet

> **Back to index:** [00_index.md](./00_index.md)

---

## At a Glance

| Category | Golden Rule | Standard Values |
|---|---|---|
| **Spacing** | 8px Grid | `4px` · `8px` · `12px` · `16px` · `24px` · `32px` · `48px` · `64px` |
| **Radius** | Predictable Scale | `6px` (Inputs) · `12px` (Cards/Buttons) · `16px` (Modals) · `9999px` (Pills) |
| **Shadows** | 4-Tier Hierarchy | `card` $\rightarrow$ `hover` $\rightarrow$ `float` $\rightarrow$ `modal` |
| **Colors** | 60-30-10 Distribution | 60% Bg (`#f8fafc`), 30% Surface (`#ffffff`), 10% Accent (`#3b82f6`) |
| **Typography** | Max 2 Typefaces | Inter (Sans), JetBrains Mono (Mono). Body: `1rem` / `1.6` line-height |
| **Motion** | Fast & Subtle | 150–200ms `ease-out` on enter, 100–150ms `ease-in` on exit |
| **HTMX** | Target Small Partials | Use `outerHTML` for single-element updates, `innerHTML` for list bodies |
| **Templates** | Prefix Partials | `_filename.html` for fragments; keep partials under 60 lines |

