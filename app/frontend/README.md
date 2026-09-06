# hs-filter-frontend

The Hero Siege loot-filter picker SPA. React 19 + Vite + TypeScript, styled with
Tailwind v4 on the Endfield design tokens.

## Commands

```sh
pnpm install
pnpm dev            # vite dev server
pnpm check          # fmt:check, lint, typecheck, test — what CI runs
pnpm build          # tsc --noEmit && vite build
pnpm test:watch     # vitest watch
pnpm sync:endfield  # re-vendor src/styles/endfield.css (needs EF_SRC)
```

## Stack

| Concern   | Choice                                        |
| --------- | --------------------------------------------- |
| Framework | React 19 + Vite 8 (oxc JSX transform, no Babel) |
| Language  | TypeScript, native compiler (`tsc --noEmit`)  |
| Styling   | Tailwind v4 (`@tailwindcss/vite`) + `endfield.css` |
| Lint      | oxlint (`--deny-warnings`)                     |
| Format    | oxfmt                                          |
| Test      | Vitest + Testing Library (jsdom)              |

Prettier and ESLint are intentionally not installed.

## The styling split

`endfield.css` (vendored in `src/styles/`) owns **components and motifs** —
`.ef-card`, `.ef-gauge`, `.ef-slab`, the chamfer clip, HUD/DOC theming. Tailwind
owns **layout, spacing and one-off colour**.

`src/styles/theme.css` bridges them: the `--ef-*` tokens are mapped into
Tailwind's scale with `@theme inline`, so `bg-surface`, `border-line`,
`text-ink-2`, `font-mono` resolve to the live `--ef-*` values and follow the
`[data-theme]` swap. Tailwind's `rounded-*` scale is zeroed — Endfield is
radius-0.

```tsx
// components: the design system's classes
<div className="ef-card ef-brackets">…</div>

// layout: Tailwind, on the shared tokens
<div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">…</div>
```

## HUD ⇄ DOC

`useTheme()` reflects the surface onto `<html data-theme>` and remembers it per
browser. `index.html` ships `data-theme="dark"` so there's no flash. Endfield is
dark-first; `light` is the "DOC" document surface.

`src/styles/endfield.css` is a **vendored copy** of the Endfield design system —
run `pnpm sync:endfield` with `EF_SRC` pointed at the source to update it. Fonts
(Chakra Petch / Jost / JetBrains Mono) load from Google Fonts in `index.html`.
