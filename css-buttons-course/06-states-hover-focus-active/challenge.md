# Challenge 06 — A button that responds to everything

**Task:** build one polished button that correctly implements *every* interactive state, in
the right source order — plus a toggle variant that holds its state. No peeking at the
solution until you've tried.

## Requirements

1. Start a fresh `index.html` with a real `<button type="button">` labeled **"Follow"**.
2. Reset the browser defaults and give it a background, white text, `em`-based padding, and a
   `border-radius` (reuse your Module 00 baseline).
3. Write the states in the **correct source order**: normal → `:hover` → `:focus-visible` →
   `:active` → `:disabled`. Add a comment noting *why* `:active` comes after `:hover`.
4. **Gate `:hover`** behind `@media (hover: hover) and (pointer: fine)` so it can't stick on
   touch devices. Leave `:active` ungated.
5. Give `:active` real pressed feedback — a small `translateY`/`scale` and/or an inset shadow.
6. Add a **`:focus-visible`** ring with `outline-offset`. Do **not** leave a bare
   `outline: none` anywhere.
7. Add a **disabled** copy using the real `disabled` attribute, styled so it's unmistakably
   non-interactive.
8. Add an **`aria-pressed` toggle variant** (e.g. a second "Notifications" button) whose
   *look* is driven entirely by `[aria-pressed="true"]` — a clearly different "on" state.
9. Wrap any motion in `@media (prefers-reduced-motion: reduce)`.

## Acceptance checklist

- [ ] Tabbing shows a focus ring; clicking with the mouse does **not**.
- [ ] While pressing and holding, the pressed look wins over the hover look.
- [ ] Hover styles live inside the `@media (hover: hover)` block (nothing else does).
- [ ] The disabled button can't be tabbed to or clicked.
- [ ] The toggle's "on" appearance comes from the `aria-pressed` attribute, not a separate
      class — verify by editing the attribute value in DevTools and watching it restyle.
- [ ] There is no bare `outline: none` without a `:focus-visible` replacement.

## Stretch goals

- Add an **`aria-busy` loading** variant with a CSS-only spinner and a dimmed label; block
  re-clicks with `pointer-events: none`.
- Build a **custom double focus ring** with `box-shadow` plus a transparent `outline`
  fallback, and confirm a ring still appears under `@media (forced-colors: active)`.
- Add an **`aria-disabled="true"`** button next to the real `disabled` one and observe the
  difference: the aria one stays focusable (add a `title` explaining why it's off).

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
