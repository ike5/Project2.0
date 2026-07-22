# Challenge 03 — Shapes: pill, circle, and a custom cut

**Task:** from a blank HTML file, build **three** buttons that show off the shape layer — a
pill, a circular icon button, and one custom `clip-path` shape (an arrow *or* a ticket).
No peeking at the solution until you've tried.

## Requirements

1. Start a new `index.html`. Reuse a small base `.btn` (reset + `inline-flex` centering +
   `:focus-visible` ring), then build the three variants as separate classes on top of it.
2. **Pill button.** Use `border-radius: 999px` and confirm it stays a pill when you make the
   label longer — do *not* hardcode a radius equal to half the height.
3. **Circular icon button.** Make the box square (fixed `width`/`height` **or**
   `aspect-ratio: 1`) with `border-radius: 50%`, containing a single emoji or inline SVG.
   Give it a meaningful **`aria-label`** and mark the glyph `aria-hidden="true"`.
4. **Custom shape.** Build either an **arrow "Next"** button or a **ticket/tag** using
   `clip-path: polygon()`. Add extra padding on the pointed side so the label never touches
   the point.
5. Every button must show a visible **`:focus-visible`** ring when tabbed to — including the
   clipped shape (remember: `outline` is drawn outside the clip, so it survives).
6. Add `:hover` and `:active` feedback to all three, and guard any transition with
   `@media (prefers-reduced-motion: reduce)`.

## Acceptance checklist

- [ ] The pill stays a pill with a short label *and* a long one — no manual half-height math.
- [ ] The icon button is a **true circle** (equal width & height, or `aspect-ratio: 1`).
- [ ] Tabbing to the icon button, a screen reader would announce a real name (`aria-label`).
- [ ] The custom shape reads clearly and its label doesn't collide with the point/notch.
- [ ] Every button — clipped one included — shows a focus ring on keyboard focus.
- [ ] Nothing shifts layout on hover (borders, if any, exist at rest).

## Stretch goals

- Make the icon button use `border: 2px solid currentColor` as a **ghost** circle, filling
  on hover with no layout jump.
- Add a punched-hole or notch to the ticket with a `::before` pseudo-element.
- Give the custom shape an elliptical corner somewhere with the `40px / 20px` slash syntax.
- Tease a gradient edge with a `::before` layer behind the button (the real technique is
  Module 12 — don't overbuild it here).

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
