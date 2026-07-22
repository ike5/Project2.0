# Challenge 10 — The juicy call-to-action

**Task:** build one show-stopping **call-to-action button** that feels genuinely alive — it
springs on hover, bounces on press, and makes an elastic entrance when the page loads — all
driven by a custom overshoot easing, and all safe under reduced motion. This is the button
you'd put at the top of a landing page.

Start from a blank `index.html` with a single real
`<button type="button">` — labeled something like **"Start free trial 🚀"** — on a dark
background, reusing the accessible baseline from Module 00.

## Requirements

1. **Define one overshoot easing** as a custom property, e.g.
   `--spring: cubic-bezier(0.34, 1.56, 0.64, 1)`, and reuse it — don't scatter magic
   numbers.
2. **Elastic entrance:** on load, the button animates in with a `@keyframes` that scales
   `0 → past 1 → under 1 → 1` (e.g. `1.1` then `0.95`) plus a fade. Use
   `animation-fill-mode: both` so it never flashes at the wrong size.
3. **Springy hover:** on `:hover` **and** `:focus-visible`, the button lifts
   (`translateY`) and grows (`scale`) on the `--spring` curve so it overshoots and settles.
4. **Growing shadow:** the hover also grows a bigger, softer `box-shadow` so the lift reads
   as real elevation. Transition it on the same curve.
5. **Bounce on press:** on `:active`, scale **down** quickly (fast, un-bouncy transition),
   so the release springs back out on `--spring`. Press must feel crisp, release springy.
6. **Focus ring:** a visible `:focus-visible` outline — and **no** bare `outline: none`
   left anywhere.
7. **Reduced-motion guard:** wrap it all in
   `@media (prefers-reduced-motion: reduce)` — kill the entrance keyframes but force the
   button to its final visible state (`opacity: 1; transform: none`), and reduce the
   hover/press transitions to near-instant so feedback survives without the overshoot.

## Acceptance checklist

- [ ] Reloading the page plays a springy, elastic entrance (never a flash at scale 0).
- [ ] Hover **and** keyboard focus both trigger the lift + grow + bigger shadow, and it
      visibly overshoots before settling.
- [ ] Pressing scales it down crisply; releasing springs it back out past resting size.
- [ ] Tabbing to it shows a focus ring; clicking with the mouse doesn't strand you without
      one.
- [ ] With OS "reduce motion" on: no entrance animation, but the button is fully visible and
      still gives instant hover/press feedback.
- [ ] Exactly one easing custom property drives every overshoot.

## Stretch goals

- **Choreograph the label:** put the icon and text in separate `<span>`s and stagger their
  entrance (icon leads, label follows ~120 ms) with `animation-delay`.
- **Idle attention pulse:** after the entrance finishes, add a subtle, slow, infinite
  "breathing" scale (e.g. `1 → 1.02 → 1`) to draw the eye — and disable it under reduced
  motion too.
- **Success bounce:** add a `.is-success` class that swaps the label to "You're in! ✅" and
  plays a one-shot decaying-overshoot bounce, to imagine the post-click state.
- **Combine transforms:** give the press a tiny `rotate` alongside the scale and make sure
  the function order keeps the spin centered.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
