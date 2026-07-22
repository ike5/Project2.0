# Module 03 — Borders, Radius & Shapes

**Goal:** control the *edge* of a button — draw and remove borders, round corners into
pills and circles, build ghost/outline buttons, and cut buttons into custom shapes with
`clip-path`. This is the "shape" layer of the button.
⏱️ ~1.5 h · 🎯 Prereq: 02.

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every shape below is on screen there — poke at the per-corner playground last.

---

## 1. Border vs. outline — they are not the same thing

A **border** is part of the box. It has width, style, and color, and — this is the key —
it **takes up layout space**. Add a `4px` border and the box grows `4px` on every side
(unless `box-sizing: border-box` eats it out of the content, from Module 01).

```css
.btn {
  /* longhand — three independent properties */
  border-width: 2px;
  border-style: solid;   /* solid | dashed | dotted | none — no style = invisible */
  border-color: #4f46e5;

  /* shorthand — width style color, in that order. Use this. */
  border: 2px solid #4f46e5;
}
```

> **Gotcha:** `border-style` defaults to `none`. If you set only `border-width` and
> `border-color`, you'll see *nothing* — the style must be present for a border to render.

An **outline** is drawn *on top of* the box, **outside** the border, and it does **not**
affect layout. Nothing reflows when you add or remove one. That's exactly why it's the
right tool for focus rings:

```css
/* outline sits outside the box and reserves NO space —
   adding it on :focus-visible never shifts the layout */
.btn:focus-visible {
  outline: 2px solid #818cf8;
  outline-offset: 2px;   /* push the ring away from the edge — outlines only */
}
```

| | `border` | `outline` |
|---|---|---|
| Affects layout / reflows | **Yes** | No |
| Follows `border-radius` | Yes | Mostly yes (modern browsers) |
| Has an `-offset` | No | **Yes** (`outline-offset`) |
| Can differ per side | **Yes** (`border-top`, …) | No (one ring) |
| Best for | the visible edge | focus rings, debugging |

**Rule of thumb:** style the *look* with `border`; signal *focus* with `outline`. Because
an outline reserves no space, a keyboard ring never nudges neighboring buttons.

---

## 2. `border-radius` fundamentals

`border-radius` rounds the corners. One value rounds all four equally:

```css
.btn { border-radius: 12px; }   /* all four corners, 12px */
```

You can set corners independently. The one-value-per-corner shorthand goes **clockwise
from top-left**: top-left, top-right, bottom-right, bottom-left.

```css
/* TL   TR   BR   BL  */
.btn { border-radius: 20px 4px 20px 4px; }   /* a leaf / diagonal shape */

/* or name a single corner explicitly */
.btn { border-top-left-radius: 20px; }
```

Two values are a shorthand pair — `border-radius: A B` means A for TL & BR, B for TR & BL
(the diagonal pairs). Percentages work too, resolved against the box's own width/height.

### Elliptical corners — the slash syntax

Each corner is really an **ellipse**, so it has a *horizontal* and a *vertical* radius. The
slash separates them: **everything before `/` is the horizontal radii, everything after is
the vertical radii.**

```css
/* every corner: 40px wide, 20px tall — squashed, elliptical rounding */
.btn { border-radius: 40px / 20px; }

/* full 8-value form: 4 horizontal / 4 vertical */
.btn { border-radius: 40px 40px 40px 40px / 20px 20px 20px 20px; }
```

This is how you get soft, non-circular corners that most buttons never bother with — a
subtle way to make a shape feel hand-drawn rather than mechanically round.

---

## 3. The pill button — and why a huge radius clamps

The pill is the most-loved button shape: fully rounded ends, flat top and bottom. The trick
is to ask for a radius far larger than the button could ever need:

```css
.btn--pill { border-radius: 999px; }   /* or 9999px — any absurdly large value */
```

**Why does `999px` not make a 999px-wide bulge?** The spec **clamps** every radius so the
sum of two adjacent radii can never exceed the side they share. On a `44px`-tall button the
vertical radius can't exceed `22px` (half the height), so the browser reduces your `999px`
down to `22px` per corner — a perfect half-circle on each end. The result is a pill *no
matter the button's width*, and it stays a pill as the label grows. That's why `999px`
is more robust than `border-radius: 50%` for a pill: `50%` on a wide box gives an ellipse,
whereas the clamped huge value always yields true semicircular caps.

```css
.btn--pill {
  padding: .7em 1.4em;      /* a bit more inline padding suits the rounded ends */
  border-radius: 999px;
}
```

---

## 4. Circular icon buttons

A circle is just a square with `border-radius: 50%`. The job is making the box **square**.
Two ways:

```css
/* A. fixed equal width & height */
.btn--icon {
  width: 44px; height: 44px;   /* 44px = a comfortable minimum touch target */
  padding: 0;                  /* let flex centering do the work */
  border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
}

/* B. modern: let content size it, but force a 1:1 ratio */
.btn--icon-auto {
  aspect-ratio: 1;             /* height tracks width automatically */
  padding: .6em;               /* square because top/bottom = left/right won't hold —
                                  use aspect-ratio, not padding, to guarantee 1:1 */
  border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
}
```

`aspect-ratio: 1` is the cleaner modern approach: size the button however you like and the
browser keeps it square, so `50%` is always a true circle. Always give an icon-only button
an **`aria-label`** — there's no visible text for a screen reader to announce:

```html
<button class="btn btn--icon" type="button" aria-label="Add to favorites">
  <span aria-hidden="true">♥</span>
</button>
```

The emoji/glyph is decorative (`aria-hidden="true"`); the `aria-label` is the real name.

---

## 5. Ghost / outline buttons

A **ghost** (or outline) button has a transparent fill, a colored border, and matching
text. It reads as secondary — present but quiet — and it's the classic partner to a solid
primary button.

```css
.btn--ghost {
  background: transparent;
  color: #818cf8;
  border: 2px solid currentColor;   /* border inherits the text color — one source of truth */
}
```

`border: 2px solid currentColor` is the pro move: the border always matches the text, so
you restyle both by changing one `color`.

### How the border interacts with a hover fill

On hover you usually fill the ghost. The subtlety: **reserve the border's space from the
start** so the fill doesn't cause a `2px` layout jump.

```css
.btn--ghost {
  background: transparent;
  color: #818cf8;
  border: 2px solid currentColor;   /* the border exists even at rest */
  transition: background-color .15s ease, color .15s ease;
}
.btn--ghost:hover {
  background: #818cf8;   /* fill in */
  color: #0e1116;        /* flip text to a dark ink for contrast */
}
```

Because the `2px` border was there the whole time, hover only changes *colors*, never the
box size — no reflow, no wobble. (If you instead added the border only on hover, the button
would grow `2px` and shove its neighbors. Don't.)

A softer variant fills with a translucent tint instead of a solid flood — gentler, and it
keeps the outline visible:

```css
.btn--ghost:hover { background: rgba(129, 140, 248, .14); }
```

---

## 6. Cut / beveled corners with `clip-path: polygon()`

`border-radius` only rounds. To *cut* a corner off — a straight diagonal bevel — you clip
the box to a polygon. `polygon()` takes a list of `x y` points (each `0%`–`100%` of the
box) traced clockwise; the browser fills inside and discards everything outside.

```css
.btn--cut {
  /* start below the top-left, up-and-over the corner, across, down the right… */
  clip-path: polygon(
    12px 0,               /* top edge starts 12px in — clips the TL corner */
    100% 0,               /* top-right */
    100% calc(100% - 12px),
    calc(100% - 12px) 100%,  /* bottom edge ends 12px early — clips the BR corner */
    0 100%,
    0 12px                /* left edge — completes the TL bevel */
  );
}
```

Mixing `px` and `%` with `calc()` keeps the bevel a **constant size** no matter how wide
the button gets. Two things to know:

- **`clip-path` clips the border too.** A `border` on a clipped box gets sliced along the
  diagonal and often looks broken — for cut-corner *outlines*, draw the edge with a
  `::before` layer or a gradient background instead (real gradient borders: Module 12).
- **The focus ring still needs to be visible.** `outline` is drawn outside the clip, so
  `:focus-visible { outline: … }` keeps working even on a clipped shape.

---

## 7. Custom shapes — arrows, tickets, notches

Once you think in polygons, buttons can be any shape.

### An arrow / chevron "next" button

Add a point on the trailing edge by pushing a mid-right vertex outward:

```css
.btn--arrow {
  padding-right: 1.9em;     /* make room for the point so the label doesn't touch it */
  clip-path: polygon(
    0 0,
    calc(100% - 14px) 0,    /* top edge stops short of the tip */
    100% 50%,               /* the point — dead center on the right */
    calc(100% - 14px) 100%, /* bottom edge stops short */
    0 100%
  );
}
```

### A ticket / tag shape

A tag is a rectangle with one pointed end (like a luggage tag or price tag); a **ticket**
is a rectangle with a notch bitten out of each side. Here's a left-pointing tag:

```css
.btn--tag {
  padding-left: 1.9em;
  clip-path: polygon(
    14px 0, 100% 0, 100% 100%, 14px 100%,
    0 50%                   /* the point on the left */
  );
}
```

For a **notch** (a bite out of an edge), route the polygon *inward* and back out at the
notch location — same idea, extra vertices.

### Decorative add-ons with `::before` / `::after`

The pseudo-elements `::before` and `::after` give you two extra layers per button with zero
extra HTML — perfect for a little punched hole in a ticket, a corner ribbon, or a shine:

```css
.btn--ticket { position: relative; }
.btn--ticket::before {   /* a punched hole on the left edge */
  content: "";
  position: absolute; left: -6px; top: 50%; transform: translateY(-50%);
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--bg);   /* same color as the page = looks punched-through */
}
```

You can also layer a thin gradient *outline* look with a pseudo-element behind the button —
but a true, robust **gradient border** (the kind that follows `border-radius` cleanly) has
its own techniques we cover in **Module 12**. For now, just know the hook exists.

---

## ✅ Check yourself

- [ ] Why does adding a `border` reflow the layout but adding an `outline` does not?
- [ ] What are the four corners of `border-radius: 20px 4px 20px 4px`, in order?
- [ ] What does the slash in `border-radius: 40px / 20px` mean?
- [ ] Why does `border-radius: 999px` reliably produce a pill at *any* width?
- [ ] What makes an icon button a true circle — and what `aria-*` does it need?
- [ ] Why must a ghost button carry its border *at rest*, not only on `:hover`?
- [ ] Why can a `border` look broken on a `clip-path` shape, and what still works for focus?

**Next:** [Module 04 — Backgrounds & Gradients →](../04-backgrounds-and-gradients/)
Then try the [challenge](./challenge.md).
