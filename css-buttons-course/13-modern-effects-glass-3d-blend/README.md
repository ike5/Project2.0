# Module 13 — Modern Effects: Glass, 3D & Blend Modes

**Goal:** wield the modern CSS surface toolkit — `backdrop-filter` glassmorphism, real 3D
transforms with perspective and tilt, a *physical* push button that depresses like a key,
`mix-blend-mode` labels that invert against what's behind them, gradient masks that fade a
button's edge, and `filter` for a one-line hover punch. Know exactly where each one is
supported and how to keep it accessible.
⏱️ ~2 h · 🎯 Prereq: Module 12 (Animated Gradients, Glow & Gradient Borders).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every effect below is on screen there, live — hover, press, and tab through them.

---

## 1. Glassmorphism — `backdrop-filter` frosted glass

"Glass" is a translucent panel that **blurs and brightens whatever sits behind it**. The
star property is `backdrop-filter`: unlike `filter` (which blurs the *element*),
`backdrop-filter` blurs the **backdrop** — the pixels showing through the element's own
translucent background.

```css
.glass {
  /* the translucent fill — MUST be semi-transparent or there's nothing to see through */
  background: rgba(255, 255, 255, 0.12);

  /* the magic: blur + saturate the pixels BEHIND the button */
  -webkit-backdrop-filter: blur(12px) saturate(160%);  /* Safari needs the prefix */
  backdrop-filter: blur(12px) saturate(160%);

  /* the glass edge: a 1px light border reads as a beveled rim */
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 14px;

  /* a top-inner highlight sells the "pane of glass" look */
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35),
              0 8px 24px rgba(0, 0, 0, 0.25);

  color: #fff;
  padding: .7em 1.4em;
}
```

**The one rule people miss: glass needs a busy backdrop.** Over a flat color, blur has
nothing to reveal and the effect vanishes — you just get a faint translucent box. Place
glass buttons over a **gradient, photo, or colorful panel** and the frosted blur suddenly
pops. That's why the demo sits these on a vivid gradient panel.

**The saturate boost matters.** Blurring alone looks muddy; `saturate(160%)` (or `180%`)
re-energizes the colors bleeding through, which is what makes real frosted glass look
*alive* rather than gray.

**Support & fallback.** `backdrop-filter` needs the `-webkit-` prefix for Safari, and older
browsers ignore it entirely. Provide a graceful fallback with `@supports` — bump the
background opacity so the button is still legible without the blur:

```css
/* Fallback FIRST: a more opaque fill, readable with no blur at all */
.glass { background: rgba(30, 30, 40, 0.55); }

/* Then upgrade ONLY where backdrop-filter actually works */
@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .glass {
    background: rgba(255, 255, 255, 0.12);
    -webkit-backdrop-filter: blur(12px) saturate(160%);
    backdrop-filter: blur(12px) saturate(160%);
  }
}
```

> **Performance note:** `backdrop-filter` is expensive — the browser re-blurs live pixels
> every frame. Use it on a handful of elements, not fifty. Big blur radii on large areas can
> jank on low-end hardware.

---

## 2. 3D transforms — `perspective`, `rotateX/Y`, `preserve-3d`

CSS transforms are 3D-capable. Three properties unlock the third dimension:

- **`perspective`** — how much foreshortening you get. Think of it as the distance from your
  eye to the screen. **Smaller = more dramatic** (extreme wide-angle); larger = subtle.
- **`rotateX()` / `rotateY()`** — tilt around the horizontal / vertical axis.
- **`transform-style: preserve-3d`** — tells children to live in the *same* 3D space as the
  parent, instead of being flattened. Essential when a button has layered pseudo-elements
  you want to stay in 3D.

Set `perspective` on the **parent** so the child tilts in a shared, consistent 3D scene:

```css
/* the "stage": establishes the 3D viewpoint for its children */
.stage {
  perspective: 600px;                 /* smaller = punchier tilt */
}

.tilt {
  transform-style: preserve-3d;
  transition: transform .25s ease;
  will-change: transform;             /* hint: this will animate */
}

/* tilt toward the viewer + lift the label off the surface on hover */
.stage:hover .tilt {
  transform: rotateX(12deg) rotateY(-14deg);
}
```

**`translateZ()` pushes a layer toward you.** Give an inner label `transform:
translateZ(30px)` inside a `preserve-3d` parent and it visibly floats above the card as it
tilts — a cheap, convincing depth cue. (This is a pure-CSS *fixed* tilt on hover; a button
that follows the cursor's exact position needs JS, which this course avoids.)

```css
.tilt .label {
  transform: translateZ(30px);        /* floats above the card face */
}
```

**`backface-visibility: hidden`** hides the mirror-image back of a rotated element — useful
if you ever flip a button 180°.

---

## 3. The *physical* push button — a solid bottom edge that depresses

This is the most satisfying button in the module: it has a **thick colored edge** below the
face, like a real keyboard key or an arcade button, and on `:active` the face **drops down
into** that edge — the key gets pressed. The trick is a **stacked `box-shadow`** acting as
the side wall:

```css
.push {
  background: #6366f1;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: .8em 1.6em;

  /* the "side wall": a hard (0-blur) shadow = a solid 3D edge below the face.
     the soft second shadow is the ambient contact shadow on the ground. */
  box-shadow: 0 6px 0 #3730a3,           /* the edge — no blur, offset down */
              0 8px 16px rgba(0,0,0,.35); /* soft ground shadow */

  transform: translateY(0);
  transition: transform .06s ease, box-shadow .06s ease;
}

/* hover: raise it a hair — taller edge, floatier shadow */
.push:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 0 #3730a3, 0 12px 20px rgba(0,0,0,.4);
}

/* PRESS: slam the face down into the edge. move down ~the edge height,
   and shrink the edge shadow to match. reads as a real key press. */
.push:active {
  transform: translateY(6px);
  box-shadow: 0 1px 0 #3730a3, 0 2px 6px rgba(0,0,0,.4);
}
```

**Why it feels real:** the face travels down by *exactly* the height of the edge (6px), and
the edge shadow shrinks from `6px` to `1px` in lockstep — so the button appears to collapse
onto the ground plane, then spring back. The `.06s` transition keeps the press instant and
tactile; anything slower feels mushy.

**Alternative: a stacked pseudo-element.** Instead of a hard shadow you can build the edge as
a `::before` sitting behind the face — handy when you want the edge to be a gradient or have
its own radius. The shadow approach is simpler and animates cheaply, so prefer it unless you
need a textured edge.

---

## 4. `mix-blend-mode` — labels that invert against the backdrop

Blend modes composite an element with whatever is *behind* it using Photoshop-style math.
The killer one for buttons is **`difference`**: it subtracts colors, so the element renders
as the **inverse** of its backdrop — white text over a light photo goes dark, over a dark
area goes light. It stays legible over *anything* without you picking a color.

```css
/* the label blends against the vivid panel behind the button */
.blend-label {
  mix-blend-mode: difference;
  color: #fff;        /* difference(white, X) = inverse of X — always contrasty */
}
```

`mix-blend-mode` blends an element against its **siblings/background**;
`background-blend-mode` blends an element's own *background layers* against each other (say a
photo blended with a gradient tint). Use `mix-blend-mode` for a label or overlay that reacts
to the page; use `background-blend-mode` to tint a button's own multi-layer background.

```css
/* background-blend-mode: tint a button's own gradient into its texture */
.tinted {
  background-image: linear-gradient(135deg, #f43f5e, #f59e0b),
                    radial-gradient(circle, #fff, #0000);
  background-blend-mode: overlay;
}
```

> **Gotcha:** an element with a blend mode needs an **isolation boundary** or it blends
> against the whole page. Wrap the group in `isolation: isolate` (or any element that
> creates a stacking context) to contain the blend to just that button and its panel.

---

## 5. Masking & reveal — `mask-image` gradient fades and `clip-path`

A **mask** uses an image's alpha (or luminance) to decide which parts of an element are
visible. A gradient mask fades an element to transparent — perfect for a soft edge or a
"scanning light" reveal. Like `backdrop-filter`, it wants the `-webkit-` prefix.

```css
/* fade the RIGHT edge of the button to transparent */
.masked {
  -webkit-mask-image: linear-gradient(to right, #000 70%, transparent);
          mask-image: linear-gradient(to right, #000 70%, transparent);
  /* black (opaque) region = shown; transparent region = hidden */
}
```

For a **reveal on hover**, animate a `clip-path` (a polygon/inset that crops the element)
or slide a masked highlight across. A crisp, cheap wipe:

```css
.reveal {
  position: relative;
  overflow: hidden;
}
.reveal::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 30%, rgba(255,255,255,.5), transparent 70%);
  /* park the sheen off to the left, then sweep it across on hover */
  transform: translateX(-120%);
  transition: transform .5s ease;
}
.reveal:hover::after { transform: translateX(120%); }
```

**Mask vs. clip.** `clip-path` cuts with a *hard* edge along a shape; `mask-image` can fade
*softly* via a gradient's alpha. Reach for `clip-path` for geometric crops (Module 03), for
`mask-image` when you need a feathered edge.

---

## 6. `filter` on hover — a one-line punch

`filter` applies graphics effects to the **element itself** (versus `backdrop-filter`, which
hits the backdrop). `brightness()`, `contrast()`, and `saturate()` give you an instant,
universally-supported hover pop with a single declaration — no need to hand-pick a darker
hover color:

```css
.punch {
  transition: filter .15s ease;
}
.punch:hover  { filter: brightness(1.12) saturate(1.15); }  /* brighter, richer */
.punch:active { filter: brightness(0.95); }                  /* dip on press */
```

Chain them: `filter: drop-shadow(0 0 8px #6366f1) brightness(1.1)` adds a **shape-accurate**
glow (`drop-shadow` follows the alpha silhouette, unlike `box-shadow` which follows the box).
Because `filter` is compositor-friendly and supported everywhere, it's the safest "make it
feel responsive" tool in this module.

---

## 7. Support caveats & reduced motion

Modern effects are the *least* uniformly supported CSS. Degrade gracefully:

- **`backdrop-filter`** — needs `-webkit-` for Safari; older browsers ignore it. Always ship
  the `@supports` fallback from §1 so text stays legible without blur.
- **`mask-image`** — still wants `-webkit-mask-*` prefixes for broad coverage. Feature-detect
  with `@supports (mask-image: linear-gradient(#000, #000))` if it's load-bearing.
- **`mix-blend-mode` / `background-blend-mode`** — widely supported now, but remember the
  `isolation: isolate` boundary or they'll blend against the whole page.
- **3D transforms** — well supported, but wrap any perspective work in a container with
  `perspective` so the scene is consistent.

**Reduced motion.** Every transition here (the tilt, the push travel, the sheen sweep) is
motion. Honor the user's OS setting — kill or shorten transforms while keeping the *static*
look (the glass, the edge, the blend) intact:

```css
@media (prefers-reduced-motion: reduce) {
  .tilt, .push, .reveal::after, .punch {
    transition: none;
  }
  .stage:hover .tilt { transform: none; }   /* no tilt */
  .push:active       { transform: translateY(3px); }  /* keep a tiny press cue */
}
```

And never drop `:focus-visible` — these fancy surfaces still need a clear keyboard ring.

---

## ✅ Check yourself

- [ ] Why does a glass button need a colorful backdrop, and what does `saturate()` add?
- [ ] What's the difference between `filter` and `backdrop-filter`?
- [ ] In the physical push button, why must the face travel down by the same distance the
      edge shadow shrinks?
- [ ] What does `mix-blend-mode: difference` do, and why is `isolation: isolate` needed?
- [ ] `clip-path` vs. `mask-image`: which gives a soft, feathered edge?
- [ ] Which effects need the `-webkit-` prefix or an `@supports` fallback?

**Next:** [Module 14 — Accessibility, Performance & Best Practices →](../14-accessibility-performance/)
Then try the [challenge](./challenge.md).
