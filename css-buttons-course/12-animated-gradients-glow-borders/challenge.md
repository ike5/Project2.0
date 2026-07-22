# Challenge 12 — Flowing gradient CTA + a gradient border

**Task:** build two attention-grabbing buttons on a dark background — a CTA whose gradient
*flows*, and a button with a *true* gradient border — then (stretch) add a shine sweep.
No peeking at the solution until you've tried.

## Requirements

1. Start a new `index.html` on a **dark** background (`#0e1116` or similar), with reset
   `<button type="button">` elements.
2. **Flowing gradient CTA:** a pill button with a **3+ color** `linear-gradient`, sized
   `background-size: 200%–400%`, whose `background-position` animates in an **infinite
   `@keyframes` loop** so the colors flow. Repeat the first color at the end so the loop is
   seamless.
3. **Gradient border button:** a button with a **transparent border** and a real gradient
   showing through it — use the double-background
   `padding-box` / `border-box` `background-clip` technique (or the masked `::before`).
   The corners must stay **rounded**.
4. Give **both** a `:hover` state that changes the effect (speed up the flow, shift the
   border's gradient — your call) and a visible **`:focus-visible`** ring.
5. **Reduced-motion safe:** wrap a `@media (prefers-reduced-motion: reduce)` block that
   stops the flowing loop and leaves a **static** gradient — the button must still look good,
   just not move.

## Acceptance checklist

- [ ] The CTA's gradient visibly flows in a smooth, seamless loop (no color "jump" on wrap).
- [ ] The gradient-border button shows the gradient *only* in the border, with rounded corners
      and a solid/dark fill inside.
- [ ] Both buttons respond on hover and show a focus ring when tabbed to.
- [ ] With OS "reduce motion" on, the flow **stops** but the button still looks intentional.
- [ ] No JavaScript, no images — pure HTML + CSS, works from `file://`.

## Stretch goals

- **Shine sweep:** add a skewed translucent-white `::before` band that `translateX`-sweeps
  across one button on hover (remember `overflow: hidden` on the button).
- **Rotating conic border:** register `@property --angle` and spin a
  `conic-gradient(from var(--angle))` behind a button for a spinning edge — with a static
  fallback under reduced motion.
- **Pulsing glow:** add a breathing colored glow (animate a blurred `::after`'s opacity) that
  intensifies on hover.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
