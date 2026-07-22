# Property Reference — CSS for Buttons 🔘

Every CSS property you'll actually reach for when designing a button, grouped by the
**layer** it affects (box → shape → surface → depth → text → motion → states). Each entry
is a one-line *what it does* plus a tiny *value example*. Keep this open while you build.

> Convention: examples use a `.btn` selector. `em`-based values scale with the button's own
> `font-size`; `rem` values are page-root-relative. See the [glossary](../GLOSSARY.md) for
> any term.

---

## Sensible defaults for a `.btn`

Start here, then override per variant. This is the accessible, resettable baseline.

```css
.btn {
  /* reset the OS chrome */
  appearance: none;
  -webkit-appearance: none;
  border: none;
  background: none;
  font: inherit;              /* buttons don't inherit font — fix it */
  color: inherit;

  /* box */
  display: inline-flex;       /* center label + drop in icons for free */
  align-items: center;
  justify-content: center;
  gap: .5em;                  /* icon ↔ label spacing */
  padding: .65em 1.25em;      /* em-based → scales with font-size */
  min-height: 44px;           /* real touch target */
  border-radius: 8px;

  /* look */
  background: var(--accent, #4f46e5);
  color: #fff;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;        /* label never wraps mid-word */

  /* interaction */
  cursor: pointer;
  touch-action: manipulation; /* kill 300ms tap delay + double-tap zoom */
  user-select: none;
  transition: background-color .15s ease, transform .12s ease;
}

.btn:hover           { background: #4338ca; }
.btn:active          { transform: translateY(1px); }
.btn:focus-visible   { outline: 2px solid #818cf8; outline-offset: 2px; }
.btn:disabled        { opacity: .5; cursor: not-allowed; }

@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
}
```

---

## Box — size & internal layout

| Property | What it does | Example |
|---|---|---|
| `display` | Puts the button in flex context so label/icon center cleanly. | `display: inline-flex;` |
| `box-sizing` | Makes `width`/`height` *include* padding + border (set globally). | `box-sizing: border-box;` |
| `padding` | Space inside the box around the label — the clickable comfort. | `padding: .65em 1.25em;` |
| `gap` | Space between children (icon and label) in a flex button. | `gap: .5em;` |
| `min-height` | Guarantees a real hit target regardless of text size. | `min-height: 44px;` |
| `width` | Fixed or `100%` (full-bleed / stretched-to-container buttons). | `width: 100%;` |
| `aspect-ratio` | Forces a shape ratio — perfect for square/circular icon buttons. | `aspect-ratio: 1;` |

---

## Shape — edges, corners, silhouette

| Property | What it does | Example |
|---|---|---|
| `border` | The visible edge (width, style, color). Often `none` or `1px solid`. | `border: 1px solid #30363d;` |
| `border-radius` | Rounds corners; a huge value makes a **pill**; `50%` makes a circle. | `border-radius: 999px;` |
| `outline` | Draws *outside* the box, doesn't affect layout — used for focus rings. | `outline: 2px solid #818cf8;` |
| `outline-offset` | Pushes the outline away from (or into) the edge. | `outline-offset: 2px;` |
| `clip-path` | Cuts the button into a custom polygon (chevron, cut corner, tag). | `clip-path: polygon(0 0,100% 0,90% 100%,0 100%);` |

---

## Surface — the fill

| Property | What it does | Example |
|---|---|---|
| `background` | Shorthand for the fill: color, image, position, size, repeat. | `background: #4f46e5;` |
| `background-image` / gradients | Layered images or gradients as the surface (see [gradients ref](./gradients-reference.md)). | `background-image: linear-gradient(90deg,#6366f1,#a855f7);` |
| `background-size` | Sizes the background; `200%` sets up scrolling-gradient animation. | `background-size: 200% 100%;` |
| `background-clip` | Limits the background to the padding box or the **text** glyphs. | `background-clip: text;` |
| `backdrop-filter` | Blurs/saturates what's *behind* the button — the glass effect. | `backdrop-filter: blur(12px) saturate(160%);` |

---

## Depth — shadow, glow, light

| Property | What it does | Example |
|---|---|---|
| `box-shadow` | Drop shadows, glows, insets — layer several for elevation/neumorphism. | `box-shadow: 0 4px 12px rgba(0,0,0,.3);` |
| `box-shadow` (inset) | Shadow *inside* the box — pressed look and neumorphic dents. | `box-shadow: inset 0 2px 4px rgba(0,0,0,.4);` |
| `filter: drop-shadow()` | Shadow that follows the button's *alpha shape* (respects `clip-path`). | `filter: drop-shadow(0 4px 8px rgba(0,0,0,.4));` |
| `mix-blend-mode` | Blends the button (or a layer) with what's under it. | `mix-blend-mode: screen;` |

> `box-shadow` syntax: `x-offset  y-offset  blur  spread  color` (+ optional `inset`).

---

## Text — the label

| Property | What it does | Example |
|---|---|---|
| `font` / `font-family` / `font-size` | The label's typeface and scale (set `font: inherit` first). | `font-size: 1rem;` |
| `font-weight` | Weight; buttons usually read best at 600. | `font-weight: 600;` |
| `letter-spacing` | Tracking; a touch of positive spacing suits uppercase labels. | `letter-spacing: .02em;` |
| `text-transform` | Cases the label without changing the HTML. | `text-transform: uppercase;` |
| `white-space` | `nowrap` stops the label wrapping to two lines. | `white-space: nowrap;` |
| `text-overflow` | With `overflow:hidden`, adds an ellipsis to clipped labels. | `text-overflow: ellipsis;` |

---

## Motion — transitions, animation, transforms

| Property | What it does | Example |
|---|---|---|
| `transition` | Shorthand: animates property changes (hover, focus) smoothly. | `transition: transform .15s ease, background-color .15s ease;` |
| `transition-property` | *Which* properties animate. | `transition-property: transform, box-shadow;` |
| `transition-duration` | *How long* the transition takes. | `transition-duration: .15s;` |
| `transition-timing-function` | The **easing** curve (the feel). See [easing ref](./easing-reference.md). | `transition-timing-function: cubic-bezier(.34,1.56,.64,1);` |
| `transition-delay` | Waits before starting — good for staggered groups. | `transition-delay: 60ms;` |
| `animation` | Shorthand to run a `@keyframes` sequence (pulse, shimmer, spin). | `animation: pulse 1.4s ease-in-out infinite;` |
| `animation-name` | Which `@keyframes` to play. | `animation-name: pulse;` |
| `animation-duration` | Length of one cycle. | `animation-duration: 1.4s;` |
| `animation-timing-function` | Easing across (or between) keyframes. | `animation-timing-function: linear;` |
| `animation-iteration-count` | How many times (or `infinite`). | `animation-iteration-count: infinite;` |
| `animation-direction` | `normal`, `reverse`, `alternate` (ping-pong). | `animation-direction: alternate;` |
| `animation-delay` | Wait before the animation starts. | `animation-delay: .2s;` |
| `animation-fill-mode` | Keep the first/last frame's styles before/after running. | `animation-fill-mode: both;` |
| `@keyframes` | Defines the animation's frames by percentage. | `@keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.06)} }` |
| `will-change` | Hints the compositor to promote a layer — use sparingly. | `will-change: transform;` |
| `transform` | Move/scale/rotate — **compositor-cheap**, the go-to for motion. | `transform: translateY(-2px) scale(1.03);` |
| `opacity` | Fade in/out — also compositor-cheap, safe to animate. | `opacity: .5;` |

> **Animate `transform` and `opacity`** — they run on the compositor (no reflow/repaint).
> Avoid animating `width`, `height`, `top`, `margin`, `box-shadow` in hot paths.

---

## States & pseudo — when styles apply

| Selector | What it targets | Example |
|---|---|---|
| `:hover` | Pointer is over the button (keep changes subtle & fast). | `.btn:hover { background: #4338ca; }` |
| `:active` | Button is being pressed — give tactile feedback. | `.btn:active { transform: translateY(1px); }` |
| `:focus-visible` | Keyboard focus only (not mouse) — draw the focus ring here. | `.btn:focus-visible { outline: 2px solid #818cf8; outline-offset: 2px; }` |
| `:disabled` | The `disabled` attribute is set — dim and block interaction. | `.btn:disabled { opacity: .5; cursor: not-allowed; }` |
| `[aria-*]` | ARIA state attributes — style toggles/loading from markup. | `.btn[aria-pressed="true"] { background: #22c55e; }` |
| `@media (hover: hover)` | Only apply hover styles on devices with a real pointer. | `@media (hover: hover) { .btn:hover { … } }` |
| `@media (prefers-reduced-motion: reduce)` | User asked for less motion — cut transitions/animations. | `@media (prefers-reduced-motion: reduce) { .btn { transition: none; animation: none; } }` |
| `@media (forced-colors: active)` | High-contrast / forced-colors mode — don't fight the OS palette. | `@media (forced-colors: active) { .btn { border: 1px solid ButtonText; } }` |

---

### Quick reminders

- **Never** `outline: none` without a replacement — use `:focus-visible` for the ring.
- Prefer the real `disabled` attribute (removes the button from tab order) over a class.
- `em` padding + `min-height` = buttons that scale with text *and* stay tappable.
- One `transition` on `.btn` covers hover **and** the return — you don't need a `:hover`
  transition too.

**See also:** [easing-reference.md](./easing-reference.md) ·
[gradients-reference.md](./gradients-reference.md) · [GLOSSARY.md](../GLOSSARY.md)
