# Module 04 — Backgrounds & Gradients

**Goal:** move past flat fills. Understand that gradients are *images*, master the three
gradient functions (`linear`, `radial`, `conic`), layer several backgrounds into one
button, swap a gradient on `:hover`, and paint text with a gradient using `background-clip`.
⏱️ ~1.5 h · 🎯 Prereq: Module 03 (Borders, Radius & Shapes).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every gradient below is on screen there, live.

---

## 1. `background-color` vs `background-image` — and gradients ARE images

A button's fill can come from two different properties:

```css
.solid {
  background-color: #4f46e5;      /* one flat color */
}
.image {
  background-image: linear-gradient(#4f46e5, #7c3aed);  /* a generated image */
}
```

The key insight that unlocks this whole module: **`linear-gradient()`, `radial-gradient()`,
and `conic-gradient()` are not color functions — they are `<image>` functions.** They
produce an image, exactly like `url(photo.png)` does. That's why they live in
`background-image`, why you can stack several of them, and why each one obeys
`background-size` and `background-position`. Once you think "gradient = image," everything
about layering later makes sense.

`background` is the shorthand that sets both at once (plus size, position, repeat…):

```css
.btn {
  /* image on TOP, color as the fallback UNDERNEATH */
  background: linear-gradient(#6366f1, #4338ca) #4338ca;
}
```

The trailing color is a smart fallback: if the gradient ever fails to paint (or is
translucent), the solid color shows through. A good habit for buttons.

---

## 2. `linear-gradient()` — angles, stops, and hard stops

A linear gradient blends colors along a straight line. You control the **direction**, then
list two or more **color stops**.

```css
/* direction first, then the colors */
.a { background: linear-gradient(to right, #f43f5e, #f59e0b); }   /* keyword */
.b { background: linear-gradient(135deg, #6366f1, #ec4899); }     /* angle   */
```

**Reading the angle.** `0deg` points **up**, and it goes **clockwise**: `90deg` = to the
right, `180deg` = down, `270deg` = left. `to right` is just a friendlier way to say `90deg`.
For buttons, `135deg` (top-left → bottom-right) is the classic, flattering diagonal.

**More than two stops** — just keep listing colors; they spread out evenly:

```css
.rainbow { background: linear-gradient(90deg, #f43f5e, #f59e0b, #22c55e, #3b82f6); }
```

**Positioned stops** — pin a color to a percentage (or length) to control *where* the blend
happens:

```css
/* purple holds until 30%, then blends to pink by 100% */
.weighted { background: linear-gradient(90deg, #7c3aed 30%, #ec4899); }
```

### Hard stops — two-tone fills and stripes

Here's the trick that surprises people. If two adjacent stops sit at the **same position**,
the blend has zero distance — you get a **crisp edge** instead of a fade. This turns the
gradient tool into a *shape* tool.

```css
/* a clean 50/50 split — no blend at the seam */
.two-tone {
  background: linear-gradient(90deg, #6366f1 0 50%, #ec4899 50% 100%);
}

/* repeating diagonal stripes */
.stripes {
  background: repeating-linear-gradient(
    45deg,
    #6366f1 0 12px,      /* color runs 0→12px */
    #4f46e5 12px 24px    /* next color 12→24px, then repeats */
  );
}
```

> `#6366f1 0 50%` is shorthand for placing that color at both `0` and `50%` — a *stop range*.
> Two ranges that meet at the same number (`50%`) share a hard edge.

`repeating-linear-gradient()` tiles the stop pattern forever, which is how you get stripes,
gingham, and progress-bar textures with no images at all.

---

## 3. `radial-gradient()` — spotlights and glossy fills

A radial gradient blends **outward from a point**. Its shape can be a `circle` or an
`ellipse`, and you position its center anywhere. This is your tool for a **spotlight** or a
**glossy highlight**.

```css
.spotlight {
  background: radial-gradient(circle at 50% 30%, #a78bfa, #4c1d95);
}
```

Anatomy of the syntax: `radial-gradient( [shape] [size] at [position], stops )`.

- **shape** — `circle` or `ellipse` (the default).
- **size** — how far the gradient reaches. Keywords: `closest-side`, `closest-corner`,
  `farthest-side`, `farthest-corner` (the default). Or give an explicit radius.
- **position** — `at 50% 30%`, `at top left`, etc. Same coordinate system as
  `background-position`.

The **glossy button** move: put a soft, semi-transparent white highlight near the top,
fading to transparent, over a colored base. It reads as a curved, lit surface:

```css
.glossy {
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%,
                    rgba(255,255,255,.55), rgba(255,255,255,0) 70%),
    #4f46e5;                       /* base color underneath */
}
```

Notice the fade to `rgba(255,255,255,0)` — a **transparent white**, not `transparent`
(which some browsers treat as transparent *black* and can muddy the blend). Always fade to
a zero-alpha version of the *same* color.

---

## 4. `conic-gradient()` — color wheels and pie fills

A conic gradient sweeps colors **around** a center point like a clock hand, instead of
outward. It's how you make color wheels, pie charts, and segment fills.

```css
.wheel {
  background: conic-gradient(
    from 0deg,
    #f43f5e, #f59e0b, #22c55e, #3b82f6, #a855f7, #f43f5e
  );
}
```

- **`from <angle>`** rotates the starting edge (where `0%` begins). `from 90deg` starts the
  sweep pointing right.
- **`at <position>`** moves the center, just like radial.

Add **hard stops** here too and the smooth sweep becomes crisp **pie segments** — perfect
for a segmented ring or a faux progress dial:

```css
.pie {
  background: conic-gradient(
    #6366f1 0 25%,       /* quarter one */
    #ec4899 25% 50%,     /* quarter two */
    #f59e0b 50% 75%,     /* quarter three */
    #22c55e 75% 100%     /* quarter four */
  );
}
```

Wrap that in a circle (`border-radius: 50%`) and you have a pie chart, no SVG required.

---

## 5. Layering multiple backgrounds

Because gradients are images, you can list **several, comma-separated**, and they stack.
**The first one listed sits on top**; later ones sit underneath. Each layer can have its own
`background-size` and `background-position` (given in the same comma order).

The everyday button use: a **subtle sheen** — a faint light gradient across just the top
half — painted over a solid base color.

```css
.sheen {
  background:
    /* LAYER 1 (top): a soft sheen, only the upper portion */
    linear-gradient(180deg, rgba(255,255,255,.25), rgba(255,255,255,0)),
    /* LAYER 2 (bottom): the base fill */
    linear-gradient(#4f46e5, #4338ca);
}
```

Per-layer sizing and positioning — here a small highlight glued to the top edge over a base:

```css
.layered {
  background-color: #1e293b;                 /* the true fallback base */
  background-image:
    radial-gradient(120% 80% at 50% -20%, rgba(56,189,248,.5), transparent 60%),
    linear-gradient(180deg, rgba(255,255,255,.08), transparent);
  background-repeat: no-repeat;
}
```

**Order matters, always.** Reversing the comma list changes which layer occludes which.
Think of them as sheets of acetate stacked front-to-back.

---

## 6. Swapping a gradient on `:hover`

You want the fill to change when the user hovers. There's one gotcha to know up front:

> **Gradients don't transition.** `background-image` is not an animatable property, so a
> `transition` on a gradient produces an instant swap, not a smooth crossfade. (The trick to
> *actually animate* a gradient — animating `background-position` on an oversized image —
> is Module 12.) Here, we simply **swap** the gradient on hover, and transition something
> that *does* animate, like `transform` or `box-shadow`, so the interaction still feels alive.

```css
.swap {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  transition: transform .18s ease, box-shadow .18s ease;
  /* background-image change is instant — that's expected */
}
.swap:hover {
  background: linear-gradient(135deg, #ec4899, #f59e0b);   /* new gradient */
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(236,72,153,.35);
}
.swap:active { transform: translateY(0); }
```

A rotating-angle variant reads as a "shift of light" and is a lovely, cheap effect:

```css
.tilt         { background: linear-gradient(120deg, #0ea5e9, #6366f1); }
.tilt:hover   { background: linear-gradient(300deg, #0ea5e9, #6366f1); }
```

Always guard motion for people who ask for less of it:

```css
@media (prefers-reduced-motion: reduce) {
  .swap { transition: none; }
  .swap:hover { transform: none; }
}
```

---

## 7. `background-clip: text` — gradient-filled text

You can clip a background image to the **shape of the text** itself, so a gradient fills the
letters. It needs three things working together:

```css
.gradient-text {
  background: linear-gradient(90deg, #f43f5e, #f59e0b, #a855f7);
  -webkit-background-clip: text;   /* clip the bg to the glyphs (prefix still needed) */
          background-clip: text;
  -webkit-text-fill-color: transparent;  /* let the bg show through */
          color: transparent;            /* fallback for the same effect */
}
```

Why each line:

- **`background-clip: text`** trims the background image to the outline of the text. The
  `-webkit-` prefix is still required for broad support — always ship both.
- **`color: transparent`** (and `-webkit-text-fill-color: transparent`) makes the actual
  glyph fill see-through, so the clipped gradient shows instead of a solid color.

**Accessibility caveat:** transparent text can fail contrast checks and vanishes if the
gradient is too light. Keep the gradient dark/saturated enough against your button, and for
a real *button label* consider a solid, high-contrast fallback color first, then layer the
effect — never rely on it for critical, low-contrast text.

---

## ✅ Check yourself

- [ ] Why does `linear-gradient()` go in `background-image` and not `background-color`?
- [ ] How do you turn a smooth blend into a crisp two-tone edge? (What's a "hard stop"?)
- [ ] In a comma-separated background list, which layer is on top — first or last?
- [ ] Why doesn't a `transition` smoothly animate a change of `background-image`?
- [ ] Which three declarations make `background-clip: text` actually show a gradient?

**Next:** [Module 05 — Shadows, Depth & Neumorphism →](../05-shadows-depth-neumorphism/)
Then try the [challenge](./challenge.md).
