# Module 15 — Capstone: Build a Button Design System

**Goal:** assemble everything you've learned into one real, reusable, themeable button
library — design tokens, a base `.btn`, BEM variant/size/shape/state modifiers, dark mode,
and full accessibility — a stylesheet you could drop into a production project today.
⏱️ ~3+ h · 🎯 Prereq: Module 14 (and, honestly, all of 00–14).

> **Do this now:** open [`demo.html`](./demo.html) — a gallery of every variant, size,
> shape, and state, plus mini real-world UI built entirely from the system. Then open
> [`solutions/buttons.css`](./solutions/buttons.css); that file *is* the deliverable, and
> the sections below are its guided tour.

Until now each module taught **one layer**. A design system is the discipline of turning
those layers into **decisions you make once and reuse everywhere**. Two ideas carry the
whole thing:

1. **Tokens** — every color, radius, size, shadow, and easing is a named CSS custom
   property in `:root`. Rules never hard-code raw values; they *reference* tokens. Retheme
   the entire library by editing the token block.
2. **A base + modifiers** — one `.btn` owns the reset and layout; small BEM classes
   (`.btn--primary`, `.btn--lg`, `.btn--pill`, …) override only what differs. Composable,
   predictable, tiny.

---

## 1. Design tokens — the single source of truth

A token is a named value. Instead of scattering `#4f46e5` across forty rules, you name it
once by its **role** and point everything at the name. Color tokens are named by *job*
("primary", "on-primary") not by hue, so a theme can repaint them without renaming anything.

```css
:root {
  /* Color roles (Module 02) — named by job, so themes can swap them */
  --btn-primary:        #4f46e5;   /* brand action        */
  --btn-primary-hover:  #4338ca;
  --btn-primary-active: #3730a3;
  --btn-on-primary:     #fff;      /* text/icon ON primary */
  --btn-danger:         #dc2626;
  --btn-success:        #16a34a;
  --btn-accent-ink:     #4f46e5;   /* accent text on the page bg */

  /* Radius scale (Module 03) */
  --btn-radius:      10px;
  --btn-radius-sm:   8px;
  --btn-radius-lg:   12px;
  --btn-radius-pill: 999px;        /* pill at any width — beats 50% */

  /* Spacing / size scale (Module 01) — em-based, so it scales with font-size */
  --btn-pad-y: 0.65em;
  --btn-pad-x: 1.25em;
  --btn-gap:   0.5em;              /* icon ↔ label (Module 11) */
  --btn-font:  1rem;              /* --sm / --lg change ONLY this */
  --btn-min-hit: 2.75rem;         /* ~44px touch target (Module 14) */

  /* Elevation scale (Module 05) */
  --btn-shadow-1: 0 1px 2px rgba(16,24,40,.08), 0 1px 3px rgba(16,24,40,.10);
  --btn-shadow-2: 0 4px 10px rgba(16,24,40,.12), 0 2px 4px rgba(16,24,40,.08);

  /* Easing tokens (Module 07 / 08) */
  --btn-ease:      cubic-bezier(.2,.7,.3,1);
  --btn-ease-out:  cubic-bezier(.16,1,.3,1);
  --btn-dur:       .16s;

  /* Focus ring (Module 06) */
  --btn-focus-ring:   #818cf8;
  --btn-focus-width:  2px;
  --btn-focus-offset: 2px;
}
```

**Why this pays off:** a token is a promise that "primary" means one thing everywhere.
Theming, dark mode, and a client's brand-color swap all become *edits to this block* — the
two hundred lines below never change. That is the entire point of a system.

---

## 2. The base `.btn` — reset + layout, shared by all

Every button — regardless of variant — needs the same reset (Module 00) and the same
flex layout (Module 11). Put it in one class so nothing repeats it.

```css
.btn {
  /* reset the OS chrome (Module 00) */
  appearance: none; -webkit-appearance: none;
  border: 1px solid transparent;   /* reserved so outline variants don't reflow */
  font: inherit; text-decoration: none;  /* so <a class="btn"> matches */

  /* layout — centers content, hosts an optional icon (Module 11) */
  display: inline-flex; align-items: center; justify-content: center;
  gap: var(--btn-gap); vertical-align: middle;

  /* box (Module 01) */
  padding: var(--btn-pad-y) var(--btn-pad-x);
  min-height: var(--btn-min-hit);
  border-radius: var(--btn-radius);

  /* type (Module 02) */
  font-size: var(--btn-font); font-weight: 600; line-height: 1.2;
  white-space: nowrap;

  /* default paint = primary; each variant re-paints these */
  background: var(--btn-primary); color: var(--btn-on-primary);

  /* interaction (Module 00 / 06) */
  cursor: pointer; touch-action: manipulation; user-select: none;

  /* motion — only cheap, compositor-friendly props animate (Module 07 / 14) */
  transition:
    background-color var(--btn-dur) var(--btn-ease),
    border-color     var(--btn-dur) var(--btn-ease),
    box-shadow       var(--btn-dur) var(--btn-ease),
    transform        .05s var(--btn-ease-out);
}
```

Notice: the base already reads *only* from tokens. It has no opinion about which variant
it is — that's the modifier's job.

---

## 3. Variants — BEM modifiers that override only the paint

A **variant** answers "how much emphasis?" Each is a `.btn--name` class that reuses the
base and repaints three lines: background, color, and the hover/active steps (Module 06).

```css
.btn--primary  { background: var(--btn-primary);  color: var(--btn-on-primary);
                 box-shadow: var(--btn-shadow-1); }
.btn--primary:hover  { background: var(--btn-primary-hover); }
.btn--primary:active { background: var(--btn-primary-active); }

/* Ghost — transparent fill, outlined; low emphasis */
.btn--ghost { background: transparent; color: var(--btn-accent-ink);
              border-color: currentColor; }
.btn--ghost:hover { background: var(--btn-tint); }        /* faint accent wash */

/* Danger / Success — same shape, different role token */
.btn--danger  { background: var(--btn-danger);  color: #fff; }
.btn--success { background: var(--btn-success); color: #fff; }

/* Link — looks like a hyperlink, behaves like a button */
.btn--link { background: transparent; color: var(--btn-accent-ink);
             min-height: 0; padding-inline: .25em; }
.btn--link:hover { text-decoration: underline; }
```

The BEM naming (`block__element--modifier`) keeps the API flat and self-documenting:
`class="btn btn--danger"` reads exactly as "a button, of the danger kind." No specificity
wars, no cascade surprises.

---

## 4. Sizes & shapes — the em trick doing the work

Because padding is **em-based** (Module 00/01), a size modifier only needs to change
`--btn-font`; the padding, gap, and hit target scale with it automatically.

```css
.btn--sm { --btn-font: .85rem; --btn-min-hit: 2.25rem; border-radius: var(--btn-radius-sm); }
.btn--lg { --btn-font: 1.15rem; --btn-min-hit: 3.25rem; border-radius: var(--btn-radius-lg); }

/* Shapes (Module 03) */
.btn--pill  { border-radius: var(--btn-radius-pill); }   /* 999px = pill at any width */
.btn--icon   { padding: 0; width: var(--btn-min-hit); aspect-ratio: 1; }  /* square */
.btn--circle { padding: 0; width: var(--btn-min-hit); aspect-ratio: 1; border-radius: 50%; }
```

`aspect-ratio: 1` keeps icon buttons perfectly square as the size scales — no magic width
math. And `999px` gives a pill regardless of width, where `border-radius: 50%` would give
an ellipse on a wide button (Module 03).

> **Accessibility rule:** an icon-only button (`.btn--icon` / `.btn--circle`) has no visible
> text, so it **must** carry an `aria-label`. See the API table.

---

## 5. States — driven by real attributes, so they're announced

The trap with states is styling them without telling assistive tech. The fix: key the
**look** off the same attribute that carries the **meaning** (Module 06 / 14).

```css
/* Press — a 1px "give"; tactile, free */
.btn:active { transform: translateY(1px); }

/* Focus — keyboard-only ring; NEVER a bare outline:none (Module 06) */
.btn:focus-visible { outline: var(--btn-focus-width) solid var(--btn-focus-ring);
                     outline-offset: var(--btn-focus-offset); }

/* Disabled — real attribute (out of tab order) OR aria-disabled (announced) */
.btn:disabled, .btn[aria-disabled="true"] { opacity: .55; cursor: not-allowed; }

/* Toggle — style off aria-pressed so "on" is SHOWN and ANNOUNCED (no drift) */
.btn[aria-pressed="true"] { background: var(--btn-primary-active);
                            box-shadow: inset 0 2px 4px rgba(0,0,0,.25); }

/* Loading — aria-busy hides the label and paints a spinner IN PLACE (no reflow) */
.btn[aria-busy="true"] { color: transparent !important; cursor: progress;
                         pointer-events: none; position: relative; }
.btn[aria-busy="true"]::after {
  content: ""; position: absolute; inset: 0; margin: auto;
  width: 1.1em; height: 1.1em; border-radius: 50%;
  border: 2px solid rgba(255,255,255,.4); border-top-color: currentColor;
  animation: btn-spin .7s linear infinite;   /* Module 09 — linear = no stutter */
}
@keyframes btn-spin { to { transform: rotate(360deg); } }
```

Styling off `aria-pressed` and `aria-busy` is the whole lesson of Module 06 made
systematic: **there is no visual state that isn't also a semantic state.** A screen-reader
user and a sighted user get the same information.

---

## 6. Theming & dark mode — retheme by re-pointing tokens

Because every rule reads tokens, "dark mode" is not new CSS — it's the **same rules with
different token values.** Ship two doors and users get both automatic and manual control
(Module 02 / 14):

```css
/* (a) Follow the OS automatically */
@media (prefers-color-scheme: dark) {
  :root {
    --btn-primary: #6366f1; --btn-primary-hover: #818cf8; --btn-primary-active: #4f46e5;
    --btn-secondary: #21262d; --btn-on-secondary: #e6edf3;
    --btn-accent-ink: #a5b4fc; --btn-focus-ring: #a5b4fc;
    /* …the rest of the dark palette… */
  }
}

/* (b) Explicit override — wins because it's a real ancestor scope. Put
   data-theme on <html>, <body>, or any wrapper (this is your JS-free toggle hook). */
[data-theme="dark"]  { /* same dark token payload */ }
[data-theme="light"] { /* re-assert the light tokens, to force light in a dark OS */ }
```

The base `.btn` never learns it went dark. That is the payoff of the token discipline: a
whole second theme costs zero rule changes.

---

## 7. Utilities & icons — the last mile

```css
/* Full-width block button — great in forms and on mobile */
.btn--block { display: flex; width: 100%; }

/* Icon support is already built into the base via `gap` (Module 11). */
```
```html
<button class="btn btn--primary">
  <svg viewBox="0 0 24 24" aria-hidden="true"><!-- icon --></svg>
  Save changes
</button>
```

An icon is just a first flex child; `gap` spaces it from the label with no extra CSS.
Mark decorative icons `aria-hidden="true"` so they aren't announced twice (Module 14).

---

## 8. The class API — at a glance

Compose one base class with any modifiers: `class="btn btn--primary btn--lg btn--block"`.

| Class | Kind | Does | From module |
|---|---|---|---|
| `.btn` | base | reset + layout every button shares | 00, 11 |
| `.btn--primary` | variant | high-emphasis brand action | 02, 06 |
| `.btn--secondary` | variant | neutral, medium emphasis | 02, 06 |
| `.btn--ghost` | variant | transparent, outlined, low emphasis | 03, 06 |
| `.btn--danger` | variant | destructive action | 02 |
| `.btn--success` | variant | confirm / save | 02 |
| `.btn--link` | variant | looks like a link, acts like a button | 02 |
| `.btn--sm` / `.btn--lg` | size | smaller / larger via `--btn-font` | 00, 01 |
| `.btn--pill` | shape | fully rounded ends at any width | 03 |
| `.btn--icon` | shape | square, icon-only (needs `aria-label`) | 03, 11 |
| `.btn--circle` | shape | round, icon-only (needs `aria-label`) | 03, 11 |
| `.btn--block` | utility | full-width | 01 |
| `.btn--raised` | utility | deeper elevation | 05 |
| `[disabled]` | state | non-interactive, out of tab order | 06 |
| `[aria-disabled="true"]` | state | non-interactive, still announced/focusable | 06, 14 |
| `[aria-pressed="true"]` | state | toggle "on" — shown *and* announced | 06 |
| `[aria-busy="true"]` | state | loading spinner in place, no reflow | 09, 14 |
| `[data-theme="dark\|light"]` | theme | force a theme on any ancestor | 02, 14 |

Built-in safety nets (Module 14): `prefers-reduced-motion` disables the spin and press,
`:focus-visible` gives a keyboard-only ring, and `forced-colors` mode keeps a real border
and system focus so buttons survive Windows High Contrast.

---

## ✅ Check yourself

- [ ] Why name color tokens by *role* (`--btn-primary`) instead of by *hue* (`--indigo`)?
- [ ] How does em-based padding let a size modifier change only `--btn-font`?
- [ ] Why key the loading and toggle *look* off `aria-busy` / `aria-pressed` rather than a
      plain `.is-loading` / `.is-on` class?
- [ ] Why does `[data-theme="dark"]` override `prefers-color-scheme`, and when do you want
      that?
- [ ] What does the base `.btn` need to *not* know for the token system to work?
- [ ] Why `border-radius: 999px` for a pill instead of `50%`?

---

## 🎓 You did it — you're a button person now

You started at a gray OS-default `<button>` and ended holding a tokenized, themeable,
accessible button **library** — variants, sizes, shapes, states, dark mode, reduced-motion
and forced-colors safety, all self-contained, all without a line of JavaScript. That is a
real portfolio piece and a real tool.

Every layer you stacked here has its own module behind it: [box model](../01-box-model-sizing-spacing/),
[color & contrast](../02-typography-color-contrast/), [shapes](../03-borders-radius-shapes/),
[gradients](../04-backgrounds-and-gradients/), [shadows](../05-shadows-depth-neumorphism/),
[states](../06-states-hover-focus-active/), [transitions](../07-transitions-and-timing/),
[Bézier easing](../08-bezier-curves-custom-easing/), [keyframes](../09-keyframe-animations/),
[springs](../10-bounces-springs-advanced-motion/), [layout](../11-layout-and-flow/),
[animated gradients](../12-animated-gradients-glow-borders/), [glass & 3D](../13-modern-effects-glass-3d-blend/),
and [accessibility & performance](../14-accessibility-performance/). Go back and remix any
of them into your system.

**→ Back to the [course home](../README.md).** Then keep going: drop your variants into the
**[playground](../playground/index.html)** and make the system *yours* — new brand color,
new variant, a gradient primary, a glassmorphic ghost. The [challenge](./challenge.md) walks
you through exactly that.

Now go build something people love to click. 🔘🚀
