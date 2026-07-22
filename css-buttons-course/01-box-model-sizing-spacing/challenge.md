# Challenge 01 — A sized, spaced button system

**Task:** from a blank HTML file, build a small but *correct* sizing system: a three-size
button scale, a full-width variant, and a properly spaced button group — all clearing the
44px hit-target rule. No peeking at the solution until you've tried.

## Requirements

1. Start `index.html` with `*, *::before, *::after { box-sizing: border-box; }` at the top
   of your CSS. Everything below assumes it.
2. Build one base `.btn` with **`em`-based padding** and a **`min-height: 44px`** (and
   `min-width: 44px`) floor. Center the label with `display: inline-flex; align-items:
   center; justify-content: center` and keep `line-height` tight (≈`1.2`).
3. Add a **three-size scale** — `.btn--sm`, `.btn--md`, `.btn--lg` — built the §4a way:
   change **only `font-size`** and let the `em` padding scale everything else. No duplicated
   padding values across the three.
4. Add a **`.btn--block`** full-width variant: `display: flex; width: 100%`. Drop it inside a
   `max-width` container and confirm it fills the container with **no horizontal overflow**.
5. Build a **button group** of at least three buttons spaced with a flex container and
   **`gap`** (in `rem`) — *not* margins on the buttons. Give it `flex-wrap: wrap` so it wraps
   cleanly when the viewport narrows.
6. Include a `:focus-visible` ring on `.btn`, and make sure you did **not** leave a bare
   `outline: none` anywhere. Any transition must be wrapped in
   `@media (prefers-reduced-motion: reduce)`.

## Acceptance checklist

- [ ] Every button — including the smallest — is at least **44px** tall and wide.
- [ ] The three sizes differ by **`font-size` only**; grepping your CSS shows a single
      `padding` value on the base rule.
- [ ] The `.btn--block` button spans its container fully with **no** horizontal scrollbar
      (thanks to `border-box` + `width: 100%`).
- [ ] The button group's spacing comes from the container's `gap`; removing a button leaves
      no orphaned margin, and no edge (first/last) has stray outer space.
- [ ] Tabbing shows a focus ring; clicking with the mouse does not.

## Stretch goals

- Add the **§4b** padding-token scale as a second row (`--btn-pad-y/x` custom properties)
  with `font-size` held steady, and put it beside the §4a row to compare the two behaviors.
- Make the block CTA **responsive**: auto-width on desktop, full-width only under
  `@media (max-width: 30rem)`.
- Build a **toolbar** of icon-only buttons (emoji) that are each ≥44px, with one action
  pushed to the far right using `margin-left: auto` on a spacer.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
