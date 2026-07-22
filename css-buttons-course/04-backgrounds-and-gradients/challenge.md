# Challenge 04 — Three gradient buttons

**Task:** in a single blank `index.html`, build **three** distinct gradient buttons — a
linear CTA, a radial glossy button, and one with a **gradient-filled text label** — each
with a tasteful `:hover` state. No peeking at the solution until you've tried.

Start from the Module 00 baseline `.btn` (reset + `em` padding + `:focus-visible` +
`:disabled`), then give each variant its own fill.

## Requirements

1. **Linear CTA.** Fill it with a diagonal `linear-gradient()` (use an angle like
   `135deg`, at least two stops). Give it a `border-radius` and a soft `box-shadow`.
2. **Radial glossy.** Layer a **transparent-white** `radial-gradient()` highlight near the
   top over a solid base color — a comma-separated background list — so it reads as a lit,
   curved surface. (Fade to `rgba(255,255,255,0)`, not `transparent`.)
3. **Gradient text.** A button whose **label** is painted by a gradient using
   `-webkit-background-clip: text` + `background-clip: text` + a transparent text fill.
4. **Hover on all three.** Each button changes on `:hover` — swap the gradient, and/or add a
   `transform`/`box-shadow`. Remember: the gradient swap is instant; transition the
   `transform`/`box-shadow`, not the `background-image`.
5. **Keep `:focus-visible`** on every button, and **do not** leave a bare `outline: none`.
6. **Guard motion:** wrap any `transform`/transition in
   `@media (prefers-reduced-motion: reduce)` that reduces or disables it.

## Acceptance checklist

- [ ] The CTA uses a real `linear-gradient()` (an image), not `background-color`.
- [ ] The glossy button uses **layered** backgrounds and fades to zero-alpha white.
- [ ] The gradient-text label is visible and legible; its text fill is transparent.
- [ ] Every button has a visible keyboard focus ring; none rely on `outline: none` alone.
- [ ] With "reduce motion" enabled, the hover motion is calmed or removed.

## Stretch goals

- Add a **hard-stop** variant of the CTA (a crisp two-tone split or diagonal stripes with
  `repeating-linear-gradient()`).
- Give the glossy button a `conic-gradient()` sibling — a segmented ring or pie badge.
- Rotate the CTA's gradient **angle** on hover (e.g. `135deg` → `315deg`) for a
  "shifting light" feel.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
