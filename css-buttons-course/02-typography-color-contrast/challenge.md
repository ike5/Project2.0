# Challenge 02 — A token-driven semantic button set

**Task:** build a set of semantic buttons where each variant is defined by a **single base
color token**, and its hover/active states are **derived** from that base — not hand-picked.
One class per variant, one source of truth per color. No peeking at the solution first.

## Requirements

1. In `:root`, define **five** semantic base tokens as CSS custom properties:
   `--c-primary`, `--c-secondary`, `--c-success`, `--c-danger`, `--c-warning`.
2. Write **one** base `.btn` (carry your Module 00–01 baseline) that reads a per-variant
   `--base` custom property for its background. Each variant class (`.btn--success`, etc.)
   sets **only** `--base` — nothing else about the fill.
3. Derive `:hover` and `:active` for **all** variants from `--base` in a **single** rule set,
   using either `color-mix(in srgb, var(--base) …, black)` **or** an `hsl()` lightness tweak.
   Adding a sixth variant must require **zero** new hover/active CSS.
4. Give labels real typographic treatment: `font-weight`, a touch of `letter-spacing`, and
   `white-space: nowrap`. Include **one** uppercase variant with proper tracking and optical
   size adjustment.
5. Add a **truncating** button: a long label capped with `max-width` (use `ch`) that ends in
   an ellipsis instead of wrapping, with the full text in a `title`.
6. Make **contrast** correct: every variant's text must clear **4.5:1** against its fill.
   At least one *light* variant (e.g. warning/amber) must use **dark** text, not white.
7. Keep meaning off of color alone — give the success and danger buttons an icon or word
   (✓ / 🗑) in addition to the hue.
8. Include a `:focus-visible` ring and a `:disabled` state. No bare `outline: none`.

## Acceptance checklist

- [ ] Each variant class sets only `--base`; changing one token re-colors that variant *and*
      its hover/active with no other edits.
- [ ] A brand-new 6th variant needs just a token + a one-line class — no new state rules.
- [ ] Hover is visibly darker than base; active is darker still — for every variant.
- [ ] The uppercase label is legible (it has tracking); it isn't a cramped wall of caps.
- [ ] The long label truncates with `…` and never wraps or overflows its `max-width`.
- [ ] Every label passes 4.5:1 — verify in DevTools; the light variant uses dark text.
- [ ] Tabbing shows a focus ring; mouse-clicking does not.

## Stretch goals

- Add **soft/tinted** counterparts by mixing each base toward `transparent`
  (`color-mix(in srgb, var(--base) 15%, transparent)`) with matching colored text.
- Add a one-line **dark/light theme** toggle by redefining the five tokens under a
  `:root[data-theme="light"]` (or a `.theme-light` wrapper) — the buttons re-theme for free.
- Auto-pick text color: try `color: color-mix(in srgb, var(--base), white 90%)` vs a dark
  ink and pick per variant so every one passes contrast.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
