# Module 02 — Typography, Color & Contrast

**Goal:** make button *labels* read cleanly, build a semantic color system driven by CSS
custom properties, derive hover/active states from a single base color, and guarantee your
white-on-color text actually passes accessibility contrast.
⏱️ ~1 h · 🎯 Prereq: 01 (Box Model, Sizing & Spacing).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every technique below is on screen there, live.

---

## 1. Label typography: small text, big rules

A button label is short, so every glyph carries weight. Four levers do almost all the work:

```css
.btn {
  font: inherit;            /* recap from Module 00 — buttons DON'T inherit font by default */
  font-weight: 600;         /* labels want a little more weight than body text */
  letter-spacing: 0.01em;   /* a hair of tracking sharpens medium-weight UI text */
  line-height: 1.2;         /* tight; a label is one line, not a paragraph */
}
```

Why these defaults:

- **`font: inherit;`** — the single most important line. An un-reset `<button>` renders in
  the OS's font, not your page's. `font` is shorthand, so it re-inherits family, size,
  weight, and line-height in one go. Set it, then override the pieces you want.
- **`font-weight: 600`** (semibold) reads as "interactive" without shouting like `700`.
  Body text is usually `400`; a button that matches body weight looks unclickable.
- **`letter-spacing`** — normal (`0`) tracking is tuned for running prose. UI labels,
  especially semibold, tighten up visually; `0.01em`–`0.02em` opens them back up. It's a
  small effect you *feel* more than see.

### Uppercase labels: tracking is mandatory

Uppercase letters have no ascenders/descenders to separate them, so they read as a wall
unless you add tracking. **Never uppercase without letter-spacing.**

```css
.btn--caps {
  text-transform: uppercase;
  letter-spacing: 0.08em;   /* REQUIRED for caps — 0.06em–0.12em is the sweet spot */
  font-weight: 700;
  font-size: 0.8em;         /* caps read "bigger" than lowercase; scale down to compensate */
}
```

- **`text-transform: uppercase`** changes the *rendering*, not the DOM text — screen
  readers still read the real casing, and you can style one label two ways. Prefer it over
  typing `SAVE` in your HTML.
- The **optical adjustments** — bumping tracking up and size down for caps — are what
  separate a designed label from a `text-transform` slapped on as an afterthought.

---

## 2. Keep the label on one line

A button that wraps to two lines looks broken. Pin the label to a single line:

```css
.btn {
  white-space: nowrap;      /* never wrap the label, even in a narrow container */
}
```

When the label *can* be arbitrarily long (user data, a filename, a long product name),
`nowrap` alone would overflow. Cap the width and truncate with an ellipsis:

```css
.btn--truncate {
  display: inline-flex;     /* our baseline; flex children need min-width:0 to shrink */
  max-width: 16ch;          /* ch = width of a "0"; a natural unit for text width */
}
.btn--truncate .label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;  /* the … that signals "there's more" */
  min-width: 0;             /* CRITICAL: flex items refuse to shrink past content without this */
}
```

The three-property combo — **`nowrap` + `overflow: hidden` + `text-overflow: ellipsis`** —
is the canonical single-line truncation recipe. Inside a flex button you *must* also set
`min-width: 0` on the truncating child, or it will blow past `max-width`. Always pair a
truncated visible label with a full accessible name (e.g. a `title` attribute) so nothing
is lost.

---

## 3. A semantic color system, not a pile of hex codes

Amateur buttons hard-code `#4f46e5` in twelve places. Professionals name colors by **role**
and store them as CSS custom properties. A button then references the *role*, and re-theming
is a one-line change.

**Solid vs. semantic:** a *solid* color is a value (`#2563eb`). A *semantic role* is what it
*means* — **primary** (the main action), **secondary** (a softer alternative), **success**
(confirm/save), **danger** (delete/destroy), **warning** (proceed with caution). Same
machinery, but roles let design and code talk about intent, not pixels.

```css
:root {
  /* one base color token per semantic role */
  --c-primary:   #2563eb;   /* blue  — the main action */
  --c-secondary: #475569;   /* slate — a quieter alternative */
  --c-success:   #16a34a;   /* green — confirm / save */
  --c-danger:    #dc2626;   /* red   — delete / destroy */
  --c-warning:   #d97706;   /* amber — caution */
}

.btn { background: var(--c-primary); color: #fff; }   /* reference the ROLE */

.btn--secondary { background: var(--c-secondary); }
.btn--success   { background: var(--c-success); }
.btn--danger    { background: var(--c-danger); }
.btn--warning   { background: var(--c-warning); }
```

Now a variant is one class, and rebranding is editing five tokens in `:root`. This tokenized
approach is the seed of the design system you'll ship in the capstone.

---

## 4. Derive states from a base color (don't hand-pick them)

The naive way is to eyeball a second and third hex for hover and active on *every* variant —
that's fifteen colors to maintain for five variants. The professional way: store **one** base
per role and *compute* hover (a touch darker) and active (darker still). Two techniques:

### Technique A — `color-mix()` (modern, works in any color space)

`color-mix()` blends two colors by percentage. Mix the base toward **black** to darken,
toward **white** to lighten, toward **transparent** for a translucent tint:

```css
.btn {
  --base: var(--c-primary);
  background: var(--base);
}
.btn:hover  { background: color-mix(in srgb, var(--base) 88%, black); }  /* 12% black → darker */
.btn:active { background: color-mix(in srgb, var(--base) 78%, black); }  /* 22% black → darkest */
```

Because every variant reads `--base`, one rule set darkens *all* of them correctly. Change a
variant's base and its hover/active follow automatically — zero extra colors to maintain.

### Technique B — `hsl()` lightness tweak

Store the color as **H S L** channels and just lower the **L** for darker states. HSL makes
"same hue, less light" trivial:

```css
.btn--hsl {
  --h: 217; --s: 91%; --l: 60%;                 /* one base, as channels */
  background: hsl(var(--h) var(--s) var(--l));
}
.btn--hsl:hover  { background: hsl(var(--h) var(--s) 52%); }   /* -8% lightness  */
.btn--hsl:active { background: hsl(var(--h) var(--s) 44%); }   /* -16% lightness */
```

**Which to use?** `color-mix()` is the more powerful, future-proof tool (any color space,
including toward `transparent` for tints) and is the modern default. The `hsl()` channel
trick is dependency-free, dead simple to reason about, and great when you're already thinking
in hue/lightness. Both derive states from *one* source of truth — that's the point.

### Subtle tints for soft/ghost variants

Mixing toward `transparent` gives a translucent wash of the same hue — perfect for a soft
button or a hover fill on an outline button:

```css
.btn--soft {
  color: var(--c-primary);
  background: color-mix(in srgb, var(--c-primary) 15%, transparent);  /* 15% tint */
}
.btn--soft:hover { background: color-mix(in srgb, var(--c-primary) 25%, transparent); }
```

---

## 5. Color notations, alpha & translucent fills

You'll write color four ways; know when each shines:

```css
.a { color: #dc2626; }                 /* hex — compact, universal, hard to eyeball tweaks   */
.b { color: rgb(220 38 38); }          /* rgb — direct channel values                        */
.c { color: hsl(0 72% 51%); }          /* hsl — reason in hue/sat/light; best for shade math */
.d { color: rgb(220 38 38 / 0.5);      /* the /alpha slot: 50% opaque red                     */ }
```

**Alpha vs. `opacity` — a crucial distinction:**

- **`opacity: 0.5`** fades the **entire element** — text, border, everything — and creates a
  new stacking context. Use it for a whole faded state (like `:disabled`).
- **Alpha on a color** (`rgb(... / .5)`, `hsl(... / .5)`, or `color-mix(..., transparent)`)
  makes only *that one color* translucent — a see-through *background* with fully opaque
  text on top. Use it for translucent fills, tints, and glass.

```css
/* translucent fill, crisp label — three equivalent ways */
.fill-1 { background: rgba(37, 99, 235, 0.15); }
.fill-2 { background: hsl(217 91% 60% / 0.15); }
.fill-3 { background: color-mix(in srgb, #2563eb 15%, transparent); }
```

Reach for **alpha** when you want a tint with readable text; reach for **`opacity`** only
when you truly want the whole thing to fade.

---

## 6. Contrast & accessibility — the part that's non-negotiable

Text on a button must be **readable**. The WCAG standard: normal text needs a contrast ratio
of at least **4.5:1** against its background (large/bold text ≥ 18.66px bold or 24px: **3:1**).
This isn't optional polish — low contrast fails real users in real light.

```css
/* ❌ BAD — white on amber is ~1.9:1. Fails badly; the label looks like a smudge. */
.btn--bad  { background: #fbbf24; color: #fff; }

/* ✅ GOOD — near-black on the same amber is ~10:1. Crisp and legible. */
.btn--good { background: #fbbf24; color: #1f2937; }
```

Practical rules that keep you passing:

- **Light, saturated fills (amber, yellow, lime, cyan) want *dark* text**, not white. White
  text only passes on *deep* colors. When you pick a variant color, pick its text color to
  match — don't default everything to `#fff`.
- **Test the pair.** Any browser DevTools color picker shows the live contrast ratio and
  flags AA/AAA. Check every variant, including hover/active (darkening usually *helps*, but
  a light base can dip below 4.5 on a subtle tint).
- **Never rely on color alone.** ~8% of men have some color-vision deficiency, so a red
  "delete" and green "save" can look identical. Back the color with a **word or an icon**
  (🗑 Delete, ✓ Save) so meaning survives without hue.
- **Disabled ≠ invisible.** A disabled button may be exempt from contrast minimums, but if
  users can't read it they can't understand the UI. Keep it dim, not unreadable.

A reliable habit: **deep color → white text; light color → dark text**, then verify the
number. Do that and your buttons are legible for everyone.

---

## ✅ Check yourself

- [ ] Why must uppercase labels get extra `letter-spacing`?
- [ ] What three properties truncate a label with an ellipsis — and what extra property is
      required inside a flex button?
- [ ] Why store one base color per *role* instead of hard-coding hex on each button?
- [ ] How does `color-mix(in srgb, var(--base) 88%, black)` derive a hover color, and what's
      the equivalent move in `hsl()`?
- [ ] What's the difference between `opacity: 0.5` and `rgb(... / 0.5)`?
- [ ] What contrast ratio must normal button text meet, and why shouldn't every button use
      white text?

**Next:** [Module 03 — Borders, Radius & Shapes →](../03-borders-radius-shapes/)
Then try the [challenge](./challenge.md).
