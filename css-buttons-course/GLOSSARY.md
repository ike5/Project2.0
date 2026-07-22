# Glossary 📖

Plain-English, button-focused definitions of every term you'll meet in this course. One or
two sentences each. Alphabetical.

> Cross-references: [property-reference](./cheatsheets/property-reference.md) ·
> [easing-reference](./cheatsheets/easing-reference.md) ·
> [gradients-reference](./cheatsheets/gradients-reference.md)

---

**appearance** — The CSS property that turns off (or on) a control's native OS styling.
`appearance: none` strips the browser's default button chrome so you can style from a blank
surface.

**aspect-ratio** — Locks an element's width-to-height ratio. `aspect-ratio: 1` makes a
perfectly square icon button that stays square as it scales.

**backdrop-filter** — Applies a filter (usually `blur`) to whatever is *behind* the element,
not the element itself. It's the core of the frosted-glass button look (glassmorphism).

**background-clip** — Controls how far a background extends: to the border box, the padding
box, or — with `text` — only the shape of the glyphs, which is how you make gradient text.

**Bézier curve / cubic-bezier** — A curve defined by control points that maps animation time
to progress. `cubic-bezier(x1,y1,x2,y2)` lets you author custom easing — the "feel" of a
button's motion.

**box model** — The nested boxes every element is made of: content → padding → border →
margin. Understanding it is how you reason about a button's real clickable size.

**box-shadow** — Draws shadows around (or inside) the box. Its parts are **offset-x**,
**offset-y**, **blur** (softness), **spread** (grow/shrink), and color; add **inset** to
put the shadow *inside* for a pressed or neumorphic dent.

**box-sizing** — Chooses whether `width`/`height` include padding and border. `border-box`
(the sane default) means a stated size is the *actual* rendered size.

**clip-path** — Cuts an element to a shape (polygon, circle, inset). Use it for chevron
buttons, cut corners, tags, and other non-rectangular silhouettes.

**compositor** — The stage of the browser's rendering pipeline that assembles pre-painted
layers on the GPU. Animations that only touch `transform`/`opacity` run here — smooth and
cheap, no reflow.

**conic-gradient** — A gradient whose colors sweep *around* a center point like a clock.
Used for color wheels, pie segments, and circular loader buttons.

**custom property (CSS variable)** — A reusable value you define (e.g. `--accent: #4f46e5`)
and reference with `var(--accent)`. The backbone of a themeable, tokenized button system.

**easing / timing function** — The rule that shapes how an animation progresses over time
(fast-then-slow, overshoot, etc.). Set via `transition-timing-function`; it's what makes
motion feel snappy, smooth, or springy.

**elevation** — The perceived height of a button above the page, communicated with shadow.
Bigger, softer, more-offset shadows read as "higher / floating."

**em vs rem** — Both are relative length units. `em` is relative to the element's *own*
font-size (so `em` padding scales the whole button with its text); `rem` is relative to the
*root* font-size (consistent regardless of local text size).

**filter** — Applies graphic effects to an element (`blur`, `brightness`, `drop-shadow`,
etc.). `filter: drop-shadow()` gives a shadow that follows the button's actual shape,
including `clip-path` cuts.

**:focus-visible** — A pseudo-class that matches focus **only when a focus ring should
show** — i.e. keyboard navigation, not a mouse click. The correct place to draw a button's
focus outline.

**forced-colors** — A mode (e.g. Windows High Contrast) where the OS overrides colors for
accessibility. Detect it with `@media (forced-colors: active)` and defer to system color
keywords instead of fighting it.

**gap** — The spacing between flex/grid children. Inside a button it's the clean way to set
the space between an icon and its label.

**glassmorphism** — A frosted-glass aesthetic: a translucent background plus `backdrop-filter:
blur()`, often with a thin light border, so the page blurs through the button.

**gradient** — A smoothly (or sharply) blended range of colors used as a `background-image`.
Comes in linear, radial, and conic flavors.

**hit target** — The area a user can actually click or tap. Aim for at least ~44×44px
(often via padding + `min-height`) so buttons are comfortable on touch screens.

**@keyframes** — A named, multi-step animation definition where you set styles at percentage
points (`0%`, `50%`, `100%`). Referenced by the `animation` property for pulses, shimmers,
spins, etc.

**linear() easing** — A timing function that approximates *any* curve — even bouncy springs —
by listing progress stops. Lets you paste a tool-generated spring into a single `transition`.

**mask** — Hides or reveals parts of an element using an image or gradient's alpha, the
inverse of `clip-path`'s hard cut. Used for shine wipes and soft-edged reveals.

**mix-blend-mode** — Defines how an element's colors blend with what's underneath (`multiply`,
`screen`, `overlay`…). Used for glowing or color-reactive button layers.

**neumorphism** — A soft-UI style where the button looks *extruded from* or *pressed into* the
background, created with paired light and dark shadows (one normal, one inset) on a matching
surface.

**opacity** — How transparent an element is, from `0` (invisible) to `1` (solid). Cheap to
animate (compositor-friendly); common for fades and disabled states.

**outline vs border** — A **border** is part of the box and affects layout; an **outline** is
drawn outside the box and doesn't shift anything, which is why focus rings use `outline`.

**overshoot / anticipation** — Motion flavors from easing. **Overshoot** (curve `y > 1`) sails
*past* the target then settles — the springy "pop." **Anticipation** (curve `y < 0`) winds
*backward* first, like a crouch before a jump.

**padding** — Space *inside* the button between its edge and the label. It's what gives a
button its comfortable size and most of its clickable area.

**paint vs layout vs composite** — The three costs of a visual change. **Layout** (reflow)
recomputes geometry — expensive; **paint** re-colors pixels — medium; **composite** just
reshuffles GPU layers — cheap. Animate composite-only props (`transform`, `opacity`).

**pill** — A button with fully rounded ends, made by setting a very large `border-radius`
(e.g. `999px`) so the corners become semicircles.

**prefers-reduced-motion** — A user setting requesting minimal animation. Honor it with
`@media (prefers-reduced-motion: reduce)` by cutting or shortening transitions and
animations.

**pseudo-element (::before / ::after)** — Extra "fake" elements you generate purely in CSS,
attached to a button. Perfect for shine overlays, glow layers, and gradient-border tricks
without adding markup.

**radial-gradient** — A gradient that radiates outward from a center point in a circle or
ellipse. Used for glossy highlights and spotlight glows.

**reflow** — The browser recalculating element geometry after a layout-affecting change
(size, position, `width`). Costly, so avoid animating properties that trigger it.

**spring / elastic** — Motion that behaves like a physical spring — overshooting the target
and oscillating before settling. Approximated with back easings or `linear()` curves for
lively buttons.

**steps()** — A timing function that advances in discrete jumps instead of smoothly.
`steps(4, end)` snaps through 4 frames — good for ticking/sprite-style button states.

**transform** — Moves, scales, rotates, or skews an element without disturbing layout.
`translate`/`scale` are the compositor-cheap workhorses of button hover/press motion.

**transition** — Automatically animates a property from its old value to its new one when it
changes (e.g. on `:hover`). You give it which properties, how long, and the easing.

**will-change** — A hint that a property is about to animate, letting the browser promote the
element to its own GPU layer ahead of time. Powerful but use sparingly — overuse wastes
memory.
