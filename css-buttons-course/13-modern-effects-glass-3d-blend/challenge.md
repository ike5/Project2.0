# Challenge 13 — Glass + a physical push button

**Task:** build two showpiece buttons in one `index.html`: a **glassmorphic** button that
frosts a colorful backdrop, and a **physical 3D push button** with a genuinely satisfying
pressed state. No JavaScript.

## Requirements

1. Create a **vivid backdrop** — a gradient (or layered radial gradients) panel — and place
   your glass button **on top of it**. (Glass over a flat color is invisible; you need
   something busy behind it.)
2. Build a **glass button**:
   - a **semi-transparent** background (e.g. `rgba(255,255,255,0.12)`),
   - `backdrop-filter: blur() saturate()` **with** the `-webkit-backdrop-filter` prefix,
   - a **1px light border** and an **inner top highlight** (`box-shadow: inset 0 1px 0 …`),
   - rounded corners,
   - an **`@supports` fallback** that makes the button legible (more opaque) where
     `backdrop-filter` isn't supported.
3. Build a **physical push button**:
   - a **solid bottom edge** made with a hard (0-blur) `box-shadow` or a stacked pseudo-element,
   - a soft ambient/ground shadow underneath,
   - on **`:active`**, the face **drops down** (`translateY`) by the edge height while the edge
     shadow shrinks in lockstep — so it reads as a real key press,
   - a fast transition (~`.06s`) so the press feels instant.
4. Give **both** buttons a visible **`:focus-visible`** ring — and no bare `outline: none`.
5. Wrap all motion in **`@media (prefers-reduced-motion: reduce)`**: disable/shorten the
   transitions but keep a small press cue and the static glass look.

## Acceptance checklist

- [ ] The glass button clearly frosts the gradient behind it (blur + saturate visible).
- [ ] Removing `backdrop-filter` support (or in an old browser) still leaves a legible button.
- [ ] The push button's face travels down by the **same distance** the edge shadow shrinks.
- [ ] Pressing the push button feels instant and tactile — not slow or mushy.
- [ ] Tabbing to either button shows a focus ring; a mouse click does not.
- [ ] With reduced-motion on, nothing lurches; the glass and edge still look right.

## Stretch goals

- **3D tilt hover:** wrap a third button in a `perspective` parent and tilt it with
  `rotateX/rotateY` on hover, floating its label forward with `translateZ` inside a
  `transform-style: preserve-3d` face.
- Add a `mix-blend-mode: difference` label over your gradient so it inverts against the
  backdrop, and contain it with `isolation: isolate`.
- Give the push button a second **re-skin** (different edge color) using only a modifier
  class, proving the pattern is reusable.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
