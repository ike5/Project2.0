# Challenge 00 — Your baseline button

**Task:** from a blank HTML file, build one accessible baseline button of your own — no
peeking at the solution until you've tried.

## Requirements

1. Start a new `index.html` with a single real `<button type="button">` labeled
   **"Get started"**.
2. Reset the browser defaults (`appearance`, `border`, `font: inherit`).
3. Give it: a background color, white text, comfortable **`em`-based** padding, a
   `border-radius`, and `cursor: pointer`.
4. Add **three** states: `:hover`, `:active`, and `:disabled`.
5. Add a **`:focus-visible`** ring — and make sure you did **not** leave a bare
   `outline: none` anywhere.
6. Prove the em trick: add a second copy of the button with `font-size: 1.4rem` and confirm
   it grows proportionally with **no other change**.

## Acceptance checklist

- [ ] Tabbing to the button with the keyboard shows a visible focus ring.
- [ ] Clicking with the mouse does **not** show that ring (that's `:focus-visible` working).
- [ ] The disabled copy looks unmistakably non-interactive.
- [ ] The large copy used only `font-size` — nothing else changed.

## Stretch goals

- Add an inline SVG or emoji icon before the label and space it with `gap`.
- Make a "secondary" variant (transparent background, colored border + text) by adding a
  second class, reusing the same base `.btn`.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
