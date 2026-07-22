# Challenge 14 — Refactor a bad button into a good one

**Task:** you've been handed a button that *works* but fails almost every rule in this
module. Refactor it — same visual intent (a pill that lifts and glows on hover), but
accessible and performant. Keep a copy of the "before" so you can see what you fixed.

## The starting point (the "bad" button)

Paste this into an `index.html` and see the problems for yourself. Every commented line is a
crime this module names.

```html
<button class="bad" onmouseover="">Buy now</button>
```
```css
.bad {
  font: 11px sans-serif;          /* tiny text */
  padding: 3px 8px;               /* ~18px tall — far below a 44px target */
  color: #9ca3af;                 /* gray on red → fails 4.5:1 contrast */
  background: #dc2626;
  border: none;                   /* no edge → invisible in High Contrast Mode */
  border-radius: 999px;
  outline: none;                  /* ❌ strands keyboard users, no replacement */
  box-shadow: 0 0 0 rgba(0,0,0,0);
  transition: width .3s ease,     /* ❌ animating width → reflow every frame */
              box-shadow .3s ease;/* ❌ animating a big blur → repaint every frame */
  width: 90px;
  will-change: width, box-shadow; /* ❌ wrong properties, always on → wasted memory */
}
.bad:hover {
  width: 120px;                                   /* reflow */
  box-shadow: 0 8px 30px rgba(220,38,38,.7);      /* repaint */
}
/* No reduced-motion guard. Hover "sticks" on touch. Meaning is color-only. */
```

## Requirements

Produce a `.good` button (and matching HTML) that fixes **all** of these:

1. **Motion is compositor-only.** Replace the width animation with a `transform` (e.g. a
   lift and/or `scale`). Replace the animated `box-shadow` with a pre-painted glow on a
   `::after` pseudo-element whose **`opacity`** you fade. Animate only `transform`/`opacity`.
2. **`will-change` is scoped and correct.** Remove the global `will-change`. If you use it at
   all, put `will-change: transform` on `:hover` only (or omit it — the transition is cheap).
3. **Focus is visible.** No bare `outline: none`. Add a `:focus-visible` ring with
   `outline-offset` that stays visible against the red fill *and* a white page — use a double
   ring (light outline + dark halo) or `currentColor`.
4. **Hit target ≥ 44×44px.** Use `min-height`/`min-width` (and/or padding) so the button is
   at least 44px tall and wide. Bump the font to a readable size.
5. **Reduced-motion guard.** Wrap a `@media (prefers-reduced-motion: reduce)` block that
   neutralizes the transition/animation (and removes the hover lift), while keeping any
   color feedback.
6. **Survives High Contrast.** Keep a `border` (even a transparent one normally), and add a
   `@media (forced-colors: active)` block using system colors so the button and its focus
   ring stay visible.
7. **Contrast + non-color signal.** Raise the label to **≥ 4.5:1** (white on `#dc2626`
   passes). Add a second, non-color cue to the meaning — an icon or explicit word (this is a
   destructive/commerce action, so make the intent unmistakable).
8. **Touch-clean.** Keep `touch-action: manipulation`, and gate the hover lift behind
   `@media (hover: hover)` so it never sticks after a tap.

## Acceptance checklist

- [ ] Recording a hover in DevTools → Performance shows **no Layout (reflow) bars** — only
      compositing.
- [ ] Tabbing to the button shows a ring that's clearly visible on the red fill; clicking
      with the mouse does **not** show it.
- [ ] The button measures **≥ 44px** in both dimensions.
- [ ] With OS "reduce motion" on, the button no longer lifts and nothing loops; it still
      gives feedback.
- [ ] In forced-colors/High Contrast, the button keeps a visible border and an obvious focus
      ring.
- [ ] The label reads at ≥ 4.5:1 and the meaning is conveyed by more than color.

## Stretch goals

- Add a `no-preference` opt-in pulse (Section 1's inverse pattern) so the button gently
  breathes *only* for users who haven't asked for less motion.
- Make an icon-only variant (e.g. a heart) that stays visually 28–30px but projects a 44×44
  tap area via a pseudo-element.
- Write a one-paragraph "diff" listing each rule you changed and *why* — narrate the fix.

Reference answer: [`solutions/index.html`](./solutions/index.html) — it ships **both** the
bad and the fixed button side by side. Try first!
