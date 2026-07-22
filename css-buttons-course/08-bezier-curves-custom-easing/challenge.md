# Challenge 08 — Design your own motion language

**Task:** build a small set of buttons whose *feel* you designed on purpose. You'll define
your own easing tokens with `cubic-bezier()`, apply them to hover interactions, and be able
to explain — for each curve — which points were fixed and which coordinates *you* chose. No
peeking at the solution until you've tried.

## Requirements

1. Start a new `index.html` with a dark background (match the course shell) and at least
   **four** real `<button type="button">` elements.
2. In `:root`, define **at least three** custom easing tokens as CSS custom properties, e.g.
   `--ease-out-quart`, `--ease-out-back`, `--ease-in-out-cubic`. **One of them must be an
   overshoot "back" curve** — a control point with **Y > 1**.
3. Apply your tokens to **hover interactions** using `transition`. Show visible contrast:
   at minimum one button that decelerates cleanly and one that **overshoots** (pops past its
   target and settles). Good properties to animate: `transform: scale()` / `translateY()`.
4. Recreate **one built-in** keyword as an explicit `cubic-bezier()` and label it (e.g.
   `ease-out ≡ cubic-bezier(0, 0, 0.58, 1)`), so you prove you know what the keyword hides.
5. Include **one** `steps()`-driven element (a tick, a stepped progress fill, or a
   typewriter reveal) so you've used stepped motion, not just smooth curves.
6. In an HTML comment beside each token, **annotate the anatomy**: state that P0 (0,0) and
   P3 (1,1) are fixed, and name the exact coordinates *you* controlled for P1 and P2 — and,
   for your "back" curve, which Y value creates the overshoot.
7. Every interactive button has a visible **`:focus-visible`** ring (no bare `outline: none`).
8. **Guard all motion** with `@media (prefers-reduced-motion: reduce)` so the journey
   collapses (durations → ~0) while the end state is preserved.

## Acceptance checklist

- [ ] At least three easing tokens are defined in `:root`, one with a control-point Y > 1.
- [ ] Hovering shows a clear difference between a clean deceleration and a springy overshoot.
- [ ] One built-in keyword is written out as its `cubic-bezier()` equivalent and labeled.
- [ ] A `steps()` element flips in discrete jumps (no smooth interpolation).
- [ ] Each token has a comment identifying the fixed endpoints and the coordinates you chose.
- [ ] Tabbing shows a focus ring; clicking with the mouse does not.
- [ ] With "reduce motion" enabled, buttons still reach their hover state — just instantly.

## Stretch goals

- Add an **anticipation** curve (a control-point **Y < 0**) so one button winds up before it
  moves, and comment where the wind-up comes from.
- Add a `linear()` **multi-bounce** token with a `cubic-bezier()` fallback declared just
  above it, and note the browser-support caveat in a comment.
- Build a tiny **"motion scale"**: fast (~120 ms), standard (~250 ms), expressive (~450 ms)
  durations paired with your curves, and apply them to small / medium / large buttons.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
