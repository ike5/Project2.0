# Gradients Reference — paste-ready recipes 🎨

Every gradient trick you'll use on buttons: linear, radial, conic, the animated-gradient
glow, gradient **text**, and true gradient **borders**. Each recipe has a one-line intro,
then code you can drop straight onto a `.btn`.

> Gradients are just `background-image` values — you can **layer** several (comma-separated),
> stack them over a solid color, and animate their position. See
> [property-reference.md](./property-reference.md) for the background properties involved.

---

## `linear-gradient()` — straight bands of color

**Basic** — top-to-bottom fade (the default direction is `to bottom` / `180deg`):

```css
.btn { background-image: linear-gradient(#6366f1, #4338ca); }
```

**Angled** — set an angle; `90deg` = left→right, `135deg` = top-left→bottom-right:

```css
.btn { background-image: linear-gradient(135deg, #6366f1, #a855f7); }
```

**Hard-stop / two-tone** — repeat a stop position to get a crisp split, no blend:

```css
/* left half indigo, right half violet — no gradient blur */
.btn {
  background-image: linear-gradient(90deg, #6366f1 0 50%, #a855f7 50% 100%);
}
```

**Sheen overlay** — a diagonal white streak layered over the base fill for a glossy edge
of light. Layer the sheen *above* the base color:

```css
.btn {
  background-image:
    linear-gradient(120deg, transparent 40%, rgba(255,255,255,.35) 50%, transparent 60%),
    linear-gradient(135deg, #6366f1, #4338ca);
}
```

---

## `radial-gradient()` — color radiating from a point

**Glossy top-light** — a soft highlight near the top, fading into the base, reads as a
rounded, lit surface:

```css
.btn {
  background-color: #4338ca;
  background-image: radial-gradient(120% 80% at 50% 0%, rgba(255,255,255,.45), transparent 60%);
}
```

**Spotlight** — a bright circle centered under the cursor/label for a focal glow:

```css
.btn {
  background-color: #1e1b4b;
  background-image: radial-gradient(circle at 50% 50%, #6366f1, #1e1b4b 70%);
}
```

> Syntax: `radial-gradient(<shape> <size> at <position>, <stops>)`. `circle`/`ellipse`,
> sizes like `closest-side`/`120% 80%`, and `at x y` to move the center.

---

## `conic-gradient()` — color swept around a center

**Color wheel** — hues sweep a full turn; great for a rainbow ring or loader:

```css
.btn {
  background-image: conic-gradient(from 0deg, #ef4444, #f59e0b, #22c55e, #3b82f6, #a855f7, #ef4444);
}
```

**Hard segments** — repeat stops to slice the sweep into flat wedges (pie/segment look):

```css
.btn {
  background-image: conic-gradient(#6366f1 0 25%, #4338ca 25% 50%, #6366f1 50% 75%, #4338ca 75% 100%);
}
```

> `from <angle>` rotates the start; `at x y` moves the center. Pairs beautifully with
> `border-radius: 50%` for circular badge buttons.

---

## Animated gradient (the moving-glow trick)

Gradients can't tween their *colors*, but you can make an **oversized** background and
animate its **position** — the colors appear to flow. Key move: `background-size: 200%`.

```css
.btn {
  background-image: linear-gradient(90deg, #6366f1, #a855f7, #ec4899, #6366f1);
  background-size: 200% 100%;          /* wider than the button */
  animation: slide-gradient 4s linear infinite;
}

@keyframes slide-gradient {
  from { background-position:   0% 50%; }
  to   { background-position: 200% 50%; }   /* scroll one full tile */
}

@media (prefers-reduced-motion: reduce) {
  .btn { animation: none; }
}
```

Repeat the first color at the end of the gradient so the loop is seamless. Add a matching
`box-shadow`/`filter: blur()` glow layer for a neon effect.

---

## Gradient **text** (`background-clip: text`)

Clip a gradient to the shape of the glyphs and make the text itself transparent, so the
gradient shows *through* the letters:

```css
.btn {
  background: linear-gradient(90deg, #a855f7, #ec4899);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;              /* let the gradient show through */
  -webkit-text-fill-color: transparent;
}
```

Keep the `-webkit-` prefixes — they're still required in several browsers. Works on any
text, but ensure the gradient keeps enough contrast to stay legible.

---

## Gradient **border** (border-box / padding-box)

There's no `border-image` shortcut that plays nicely with `border-radius`, so the reliable
trick is **two backgrounds**: a solid fill clipped to the padding box, and the gradient
clipped to the border box underneath.

```css
.btn {
  border: 2px solid transparent;                 /* space for the gradient edge */
  border-radius: 12px;
  background:
    linear-gradient(#161b22, #161b22) padding-box,           /* inner fill */
    linear-gradient(135deg, #6366f1, #ec4899) border-box;    /* the "border" */
  background-clip: padding-box, border-box;
  color: #e6edf3;
}
```

How it reads: the fill (`padding-box`) covers everything inside the border; the gradient
(`border-box`) extends into the transparent border, so only the edge shows. Swap the inner
fill for `transparent` to get a gradient outline over the page background.

> Animate the gradient border by adding `background-size: 200% 200%` to the gradient layer
> and animating `background-position`, exactly like the moving-glow trick above.

---

### Layering cheatsheet

- Backgrounds stack **first-listed on top**. Put highlights/sheens before the base fill.
- Mix gradients with `background-color` as a fallback and base tint.
- `background-clip: text` needs `color: transparent`; `padding-box`/`border-box` need
  `border: … transparent`.

**See also:** [property-reference.md](./property-reference.md) ·
[easing-reference.md](./easing-reference.md) · [GLOSSARY.md](../GLOSSARY.md)
