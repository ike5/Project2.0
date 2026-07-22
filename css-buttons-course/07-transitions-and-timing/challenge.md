# Challenge 07 — A button that moves *right*

**Task:** build one hover button whose motion feels deliberately designed. It should
transition **both** a `transform` and its `background` with **well-chosen, different**
durations, and it must feel **different entering vs. leaving** (asymmetric in/out). Guard all
motion with `prefers-reduced-motion`. No peeking at the solution until you've tried.

## Requirements

1. Start a new `index.html` with a real `<button type="button">` on the dark demo
   background. Reuse the Module 00 reset (`appearance`, `border`, `font: inherit`,
   `cursor: pointer`).
2. On `:hover`, change **two** things at once:
   - a **`transform`** — a lift (`translateY`), a `scale`, or both; and
   - the **`background`** (color or gradient).
3. Give those two properties **different durations**, written as an **explicit comma list** —
   *not* `transition: all`. A snappy background (~120–160ms) with a slower move
   (~250–320ms) is a good target.
4. Make it **asymmetric**: put the **"out"** transition (leaving hover) on the **base rule**
   and override it with a **quicker "in"** transition on **`:hover`**. Use
   **`ease-out` entering** and **`ease-in` leaving**.
5. Only transition **`transform`** and **`background`/`box-shadow`** — do **not** animate
   `top`, `width`, `height`, or `margin`.
6. Add a `:focus-visible` ring and an `:active` press. Do **not** leave a bare
   `outline: none`.
7. Wrap all motion in `@media (prefers-reduced-motion: reduce)` — remove the `transform`
   and the transition; the color change may stay.

## Acceptance checklist

- [ ] Hovering moves the button *and* changes its background.
- [ ] The two properties visibly finish at **different times** (different durations).
- [ ] Entering hover feels **quicker/crisper** than leaving it (asymmetry is noticeable).
- [ ] You used an explicit property list — searching your CSS for `transition: all` finds
      nothing.
- [ ] Nothing that triggers layout (`top`/`width`/`margin`…) is being animated.
- [ ] Tabbing shows a focus ring; a mouse click does not.
- [ ] With OS "reduce motion" on, the button no longer moves.

## Stretch goals

- **Stagger** an icon and the label with different `transition-delay`s (icon leads).
- Add a subtle **`box-shadow`** that grows with the lift (a third comma-list entry) to sell
  the height.
- Build a **secondary variant** that reuses the base class but flips *which* property is the
  fast one — a good way to feel how much duration choice changes the personality.
- Race your own button against `ease` vs. `ease-out` and pick the curve that feels most
  "arrived."

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
