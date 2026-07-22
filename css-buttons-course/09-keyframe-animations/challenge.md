# Challenge 09 — A loading button + an attention CTA

**Task:** using only HTML and CSS, build **two** self-running button animations on one page:
(1) a **loading button** with a CSS spinner, and (2) a separate **attention "pulse" CTA** —
both fully respecting `prefers-reduced-motion`. No JavaScript.

## Requirements

1. Start a new `index.html` (dark background, `system-ui` font) with a real
   `<button type="button">` for each of the two buttons.
2. **Loading button:** show it in a "loading" state that contains a **CSS-only spinner** —
   a circle built from a `border` with **one side a different/brighter color**, rotated
   `360deg` with `linear infinite` timing via `@keyframes`. Put a label like "Saving…" next
   to it, dim the button, and set `cursor: progress`. Mark it `disabled` and
   `aria-label` it appropriately.
3. **Pulse CTA:** a separate primary button that loops a gentle **`scale` and/or `opacity`
   pulse** (`@keyframes`, `infinite`) to draw the eye. Keep it subtle — no jarring jumps.
4. Give **both** interactive buttons a visible **`:focus-visible`** ring, and make sure you
   left **no bare `outline: none`** anywhere.
5. **Accessibility:** wrap a `@media (prefers-reduced-motion: reduce)` block that **stops
   the pulse entirely** and **freezes the spinner** — but leave the spinner *visible* (e.g.
   keep its bright arc) so it still reads as a busy indicator when motion is off.

## Acceptance checklist

- [ ] The spinner rotates smoothly and evenly (you used `linear`, not an ease).
- [ ] The pulse CTA loops forever and looks inviting, not annoying.
- [ ] Tabbing to either button shows a focus ring; a mouse click does not.
- [ ] With "reduce motion" on, the pulse stops **and** the spinner stops — yet the loading
      button still clearly communicates "busy."
- [ ] No JavaScript anywhere; the page works from `file://`.

## Stretch goals

- Add a **shimmer/skeleton** placeholder button (a gradient wider than the box, animated via
  `background-position`).
- Add a **success** state: an inline SVG check that draws itself with
  `stroke-dasharray` / `stroke-dashoffset` and holds via `animation-fill-mode: forwards`.
- **Layer** two animations on the CTA (e.g. a `scale` pulse plus an expanding `box-shadow`
  ring) using a comma-separated `animation` list.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
