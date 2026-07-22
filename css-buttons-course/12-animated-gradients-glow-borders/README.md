# Module 12 — Animated Gradients, Glow & Gradient Borders

**Goal:** make gradients *move*, make edges *glow*, and give a button a *true* gradient
border — the three effects that read as "premium" on a landing page. You'll learn the
tricks the browser forces on you (you can't tween a gradient directly) and how to spin a
conic gradient with `@property`.
⏱️ ~1.5 h · 🎯 Prereq: 11 (Layout & Flow) — plus Modules 04 (gradients), 05 (glow),
09 (`@keyframes`).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every effect below is on screen there, glowing on the dark shell.

---

## 1. Why you can't transition a gradient (and the trick that fixes it)

Try this and watch nothing happen on hover:

```css
.btn { background: linear-gradient(90deg, #6366f1, #ec4899); }
.btn:hover { background: linear-gradient(90deg, #ec4899, #6366f1); } /* ❌ snaps, no tween */
```

A gradient is a **generated image**, not an animatable value. The browser can't interpolate
between two `linear-gradient(...)` images, so the change **snaps** instead of animating.
There is no `@property` type for a whole gradient either.

**The classic workaround:** don't animate the gradient — animate *where it sits*. Make the
gradient **bigger than the button** with `background-size`, then slide it with
`background-position`. Position **is** animatable.

```css
.flow {
  /* a wide multi-stop gradient… */
  background: linear-gradient(90deg, #6366f1, #ec4899, #f59e0b, #6366f1);
  /* …painted at 3× the button's width so there's room to slide */
  background-size: 300% 100%;
  background-position: 0% 50%;
  transition: background-position .6s ease;
}
.flow:hover { background-position: 100% 50%; }  /* ✅ the colors glide across */
```

Because the gradient is 300% wide, moving `background-position` from `0%` to `100%` walks
the visible window across two extra color stops — a smooth, real transition. Repeat the
first color at the end (`… #6366f1` again) so the loop is **seamless** when you animate it
next.

---

## 2. A moving multi-color gradient CTA

Swap the hover transition for an infinite `@keyframes` loop and you get a CTA whose colors
flow forever. Note `background-size: 200%–400%` gives the runway; the keyframe just shuttles
`background-position` back and forth.

```css
@keyframes gradient-flow {
  0%   { background-position:   0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position:   0% 50%; }
}

.cta-flow {
  color: #fff; font-weight: 700;
  padding: .8em 1.6em; border-radius: 999px; border: 0;
  background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899, #f59e0b, #6366f1);
  background-size: 300% 100%;
  animation: gradient-flow 6s ease infinite;   /* slow = expensive-looking */
}
.cta-flow:hover { animation-duration: 2.5s; }  /* speed up on hover for feedback */

@media (prefers-reduced-motion: reduce) {
  .cta-flow { animation: none; background-position: 50% 50%; }
}
```

Design notes:
- **Slow is luxurious.** 6–8s reads as premium; 1s reads as a broken loading bar.
- **`ease` vs `linear`.** `linear` keeps a constant glide; `ease` gently breathes at the
  turns. Both are fine — pick by feel.
- **Repeat the first stop last** so `0%` and `100%` land on the same color — no visible
  jump when the loop wraps.
- Animating `background-position` is cheap, but it is **not** a compositor-only property, so
  keep the element small (a button is fine). We cover the perf trade-offs in Module 14.

---

## 3. Shine / sweep sheen on hover

A band of light that sweeps diagonally across the button — the "premium product card"
effect. Recipe: a `::before` pseudo-element holding a **skewed translucent-white
gradient**, parked off the left edge, that `translateX`-sweeps across on hover. The button
gets `overflow: hidden` so the band is clipped to the button's shape, and
`position: relative` so the pseudo-element is positioned against it.

```css
.shine {
  position: relative;
  overflow: hidden;                    /* clip the sweeping band to the button */
  background: #4f46e5; color: #fff;
  padding: .8em 1.6em; border-radius: 12px; border: 0;
}

.shine::before {
  content: "";
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  /* a narrow bright stripe: transparent → white → transparent */
  background: linear-gradient(100deg,
    transparent 30%, rgba(255,255,255,.55) 50%, transparent 70%);
  transform: translateX(-120%) skewX(-15deg);   /* park it off-screen left, tilted */
  transition: transform .7s ease;
}

.shine:hover::before { transform: translateX(120%) skewX(-15deg); }  /* sweep across */

@media (prefers-reduced-motion: reduce) {
  .shine::before { transition: none; }
  .shine:hover::before { transform: translateX(-120%) skewX(-15deg); } /* stays hidden */
}
```

Why it works:
- **`translateX(-120%) → 120%`** moves the whole band from just off the left to just off the
  right, so it enters and fully exits — no half-band lingering.
- **`skewX(-15deg)`** tilts the stripe so it reads as a diagonal glint, not a flat wipe.
- **`transform` only** — it's compositor-friendly, so the sweep stays at 60fps.
- **`overflow: hidden`** is doing the real work: it masks the band to the button's rounded
  rectangle so nothing spills past the corners.

---

## 4. Pulsing glow

A colored halo that breathes, then flares brighter on hover. You can animate `box-shadow`
directly, but animating a **pseudo-element's opacity** (with a pre-blurred glow baked in) is
smoother — `opacity` is compositor-only, `box-shadow` is not.

**Simple version — animate the shadow:**

```css
@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 12px rgba(99,102,241,.55); }
  50%      { box-shadow: 0 0 28px rgba(99,102,241,.95); }
}
.glow {
  background: #4f46e5; color: #fff; border: 0;
  padding: .8em 1.6em; border-radius: 12px;
  animation: glow-pulse 2s ease-in-out infinite;
}
.glow:hover { animation-duration: .9s; }   /* pulse faster = more urgent */
```

**Smoother version — animate a blurred `::after`'s opacity** (cheaper for the compositor):

```css
.glow2 { position: relative; background: #4f46e5; color: #fff; border: 0;
         padding: .8em 1.6em; border-radius: 12px; }
.glow2::after {
  content: ""; position: absolute; inset: 0; z-index: -1;
  border-radius: inherit;
  background: #6366f1;
  filter: blur(16px);                       /* a soft colored halo behind the button */
  opacity: .5;
  animation: soft-pulse 2s ease-in-out infinite;
}
@keyframes soft-pulse { 0%,100% { opacity: .35; } 50% { opacity: .9; } }
.glow2:hover::after { opacity: 1; filter: blur(22px); }

@media (prefers-reduced-motion: reduce) {
  .glow, .glow2::after { animation: none; }
}
```

- Put the halo **behind** the button with `z-index: -1` and `inset: 0` + `blur()`.
- Match the halo color to the button; a slightly lighter tint reads as "lit from within."
- Always give the reduced-motion crowd a **static** glow, not a pulsing one.

---

## 5. TRUE gradient borders — 2 techniques

A `border-image` can't have rounded corners, and `border: 2px solid gradient` isn't valid.
So a real gradient border takes a trick. Here are the two that actually ship.

### Technique A — the double-background `background-clip` trick (best, rounded corners work)

Layer **two** backgrounds: your fill clipped to the *padding box*, and the gradient clipped
to the *border box*. A transparent border reveals the gradient underneath it.

```css
.gborder {
  color: #fff; font-weight: 600;
  padding: .8em 1.6em;
  border: 2px solid transparent;            /* the border is see-through… */
  border-radius: 14px;
  /* two layers, comma-separated: */
  background:
    linear-gradient(#0e1116, #0e1116) padding-box,   /* fill, clipped inside the border */
    linear-gradient(120deg, #6366f1, #ec4899, #f59e0b) border-box; /* gradient, under the border */
  background-origin: border-box;
}
.gborder:hover {
  background:
    linear-gradient(#161b22, #161b22) padding-box,
    linear-gradient(120deg, #ec4899, #f59e0b, #6366f1) border-box;
}
```

How it reads: the **padding-box** layer paints your solid fill only *inside* the transparent
border. The **border-box** layer paints the gradient across the whole box, but you only *see*
it in the 2px transparent border ring. `border-radius` clips both — so the corners round
perfectly, which `border-image` can't do. This is the technique to reach for by default.

> Match the padding-box fill to whatever sits *behind* the button (here the dark shell
> `#0e1116`). For a gradient-bordered button on a photo, use a semi-transparent fill or the
> mask technique below.

### Technique B — masked `::before` (works over *any* background, incl. photos)

Draw the gradient on a `::before` that fills the button, then **punch out the middle** with a
mask that's opaque only on the border ring. Nothing behind the button is assumed.

```css
.gborder-mask { position: relative; padding: .8em 1.6em; border-radius: 14px;
                color: #fff; background: transparent; }
.gborder-mask::before {
  content: ""; position: absolute; inset: 0; border-radius: inherit;
  padding: 2px;                             /* = border thickness */
  background: linear-gradient(120deg, #6366f1, #ec4899, #f59e0b);
  /* keep only a 2px ring: fill minus content-box, composited "out" */
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;              /* Safari/old syntax */
          mask-composite: exclude;          /* standard syntax */
  pointer-events: none;
}
```

The mask stacks two solid layers: one clipped to the **content box**, one to the full box.
`exclude` (a.k.a. `xor`) keeps only where they *differ* — the 2px padding ring — so the
gradient shows as a border and the center is transparent, letting a photo show through.

---

## 6. Rotating conic-gradient border/glow with `@property`

The showstopper: a gradient border that **spins**. A `conic-gradient` has an angle, and if we
could animate that angle we'd get rotation — but again, you can't tween a gradient. The fix
is a **CSS custom property that's a real `<angle>`**, registered with `@property` so the
browser *can* interpolate it, then fed into the conic gradient.

```css
/* Register a typed custom property so it can animate. */
@property --angle {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: false;
}

@keyframes spin { to { --angle: 360deg; } }

.conic {
  position: relative; z-index: 0;
  padding: .85em 1.7em; border-radius: 14px; border: 0;
  background: #0e1116; color: #fff; font-weight: 600;
}
.conic::before {
  content: ""; position: absolute; inset: -2px;      /* 2px ring outside the button */
  z-index: -1; border-radius: inherit;
  /* the conic gradient reads our animatable --angle */
  background: conic-gradient(from var(--angle),
              #6366f1, #ec4899, #f59e0b, #6366f1);
  animation: spin 4s linear infinite;
}
/* a second, blurred copy = a rotating GLOW instead of a hard ring */
.conic::after {
  content: ""; position: absolute; inset: -2px; z-index: -2;
  border-radius: inherit; filter: blur(14px); opacity: .7;
  background: conic-gradient(from var(--angle),
              #6366f1, #ec4899, #f59e0b, #6366f1);
  animation: spin 4s linear infinite;
}

@media (prefers-reduced-motion: reduce) {
  .conic::before, .conic::after { animation: none; }
}
```

- **`from var(--angle)`** sets the gradient's start angle; animating `--angle` 0→360°
  rotates the whole cone. Without `@property`, `--angle` is just a string and the browser
  snaps at the keyframes — registering it as `<angle>` is what makes it *tween*.
- The button's own solid `background` sits **on top** of the `::before`, so only the 2px
  `inset: -2px` overhang shows as a border. Add the blurred `::after` for a spinning halo.
- **Fallback note:** `@property` ships in all current evergreen browsers (Chrome/Edge 85+,
  Safari 16.4+, Firefox 128+). In an older browser the property simply won't animate —
  `--angle` stays at its `initial-value` and you get a **static** gradient border, which is a
  perfectly acceptable degrade. No polyfill needed.

---

## 7. Guard every loop with `prefers-reduced-motion`

Infinite animations — flowing gradients, pulses, spins — are exactly what motion-sensitive
users have turned off. **Every** `animation` in this module must be answerable by:

```css
@media (prefers-reduced-motion: reduce) {
  .cta-flow, .glow, .conic::before, .conic::after { animation: none; }
  .shine::before { transition: none; }
  /* leave a tasteful STATIC version — a fixed gradient, a steady glow, a solid border */
  .cta-flow { background-position: 50% 50%; }
}
```

The goal isn't to strip the design bare — it's to **stop the looping motion** while keeping
the *look*. A static flowing-gradient still looks great; it just doesn't move. Ship both.

---

## ✅ Check yourself

- [ ] Why does `transition` do nothing when you swap one `linear-gradient` for another?
- [ ] What two properties combine to make a gradient *flow*, and which one actually animates?
- [ ] In the shine sweep, what is `overflow: hidden` on the button responsible for?
- [ ] In the double-background gradient border, what does the `padding-box` layer do vs. the
      `border-box` layer?
- [ ] Why must `--angle` be registered with `@property` before a conic gradient can spin?
- [ ] What's the *static* fallback each of your looping effects degrades to under
      `prefers-reduced-motion: reduce`?

**Next:** [Module 13 — Modern Effects: Glass, 3D & Blend Modes →](../13-modern-effects-glass-3d-blend/)
Then try the [challenge](./challenge.md).
