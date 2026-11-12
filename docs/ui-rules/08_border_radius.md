# §8 — Border Radius System

> **Back to index:** [00_index.md](./00_index.md)

---

## 8.1 Scale & Usage

| Token | CSS Variable | px | Usage |
|---|---|---|---|
| `--radius-sm` | `0.375rem` | 6px | Inputs, inline badges, tags |
| `--radius-md` | `0.75rem` | 12px | Cards, buttons, tables, standard containers (Default) |
| `--radius-lg` | `1rem` | 16px | Modals, prominent drawers, floating sheets |
| `--radius-pill` | `9999px` | Pill | Status badges, avatar rings, filter chips |

---

## 8.2 Golden Rules

- **Standard Card Radius:** Pick `12px` (`--radius-md`) and stick with it across all cards and containers.
- **Nested Corner Rule:** Outer radius must be greater than inner radius ($r_{inner} = r_{outer} - padding$).
- **Never Mix Arbitrary Radii:** Always reference tokens rather than arbitrary Tailwind `rounded-[7px]`.

