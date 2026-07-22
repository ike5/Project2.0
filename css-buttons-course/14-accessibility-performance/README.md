# Module 14 — Accessibility, Performance & Best Practices

**Goal:** take everything you've built — gradients, shadows, springs, glass — and make it
*ship-ready*: motion that respects the user, animation the compositor loves, focus rings
nobody can lose, buttons that survive High Contrast Mode, and hit targets a thumb can hit.
⏱️ ~1.5 h · 🎯 Prereq: Module 13 (you've built expressive, animated buttons — now make them
correct).

> **Do this now:** open [`demo.html`](./demo.html) in your browser. Then flip your OS
> "reduce motion" switch and reload — watch the animations calm down. Tab through with the
> keyboard. If you're on Windows, toggle High Contrast Mode. The whole lesson is on screen.

This module doesn't add a new *look*. It adds the discipline that separates a demo from a
product. Every rule here is cheap to apply and expensive to skip.

---

## 1. Respect motion preferences — `prefers-reduced-motion`

Some people get dizzy, nauseated, or disoriented by movement — vestibular disorders,
migraine, motion sensitivity. The OS lets them ask for less of it (macOS: *Reduce motion*;
Windows: *Show animations off*; iOS/Android similar). Browsers expose that request as a
media query. **Honoring it is not optional.**

The canonical pattern: build your motion normally, then wrap a "calm it down" block that
neutralizes *all* animation and transition site-wide.

```css
/* Your normal, delightful motion */
.btn {
  transition: transform .2s ease, background-color .2s ease;
}
.btn:hover { transform: translateY(-3px); }

/* The global guard — put this ONCE, near the end of your stylesheet.
   It doesn't kill motion outright; it collapses it to ~instant so
   functional transitions (a menu opening) still "complete." */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;   /* stop infinite loops */
    transition-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
}
```

**Why `.01ms` and not `none`?** A hard `transition: none` can cause visible "jumps" and can
break scripts that wait for a `transitionend` event. Near-zero duration keeps the state
change instantaneous *and* still fires the event. It's the community-standard nuke.

**Prefer targeted softening where you can.** The global guard is a safety net. For a
specific button, decide what "reduced" should *mean* — often: keep the color feedback, drop
the movement.

```css
@media (prefers-reduced-motion: reduce) {
  .btn:hover { transform: none; }   /* no lift… */
  .btn { transition: background-color .2s ease; }  /* …but still color-fade */
}
```

### The opt-in (inverse) pattern

Sometimes you want a button that is *still by default* and only animates for people who
haven't asked for less motion. Gate the motion behind `no-preference` instead of stripping
it away:

```css
.pulse { /* no animation by default — safe for everyone */ }

@media (prefers-reduced-motion: no-preference) {
  .pulse { animation: pulse 1.6s ease-in-out infinite; }
}
@keyframes pulse { 50% { transform: scale(1.05); } }
```

Same result for the sensitive user, but the *default* is the calm one — which is the safer
default to ship.

---

## 2. Animate only `transform` and `opacity`

Not all CSS properties are equal to animate. The browser renders a frame in stages:

```
  Style  →  Layout (reflow)  →  Paint  →  Composite
                 │                 │           │
      geometry: where & how    fill pixels:  stitch layers
      big is every box         color, text   on the GPU
```

- Animate a property that changes **geometry** (`width`, `height`, `top`, `left`, `margin`,
  `padding`, `border-width`) and the browser must **re-run Layout every frame** — recompute
  the size/position of that box *and everything affected by it*. That's **reflow**, the most
  expensive thing you can do 60 times a second.
- Animate a property that changes **appearance** (`box-shadow`, `background`, `color`,
  `border-color`, `filter`) and you skip Layout but force a **repaint** every frame —
  re-filling pixels, also costly for large or blurred areas.
- Animate **`transform`** or **`opacity`** and the browser can hand the whole thing to the
  **compositor on the GPU**: no Layout, no Paint, just re-stitching an already-painted
  layer. This is the smooth, cheap path — it can run on a separate thread and stay at 60fps
  even while the main thread is busy.

### Cheap vs. expensive — the table to memorize

| You want to animate… | Do it with | Triggers | Cost |
|---|---|---|---|
| Move / nudge | `transform: translate()` | Composite only | ✅ Cheap |
| Grow / shrink | `transform: scale()` | Composite only | ✅ Cheap |
| Rotate / spin | `transform: rotate()` | Composite only | ✅ Cheap |
| Fade in/out | `opacity` | Composite only | ✅ Cheap |
| Resize a box | ~~`width` / `height`~~ | **Layout** → Paint → Composite | ❌ Reflow |
| Reposition | ~~`top`/`left`/`margin`~~ | **Layout** → Paint → Composite | ❌ Reflow |
| Glow / shadow | ~~`box-shadow`~~ | **Paint** → Composite | ⚠️ Repaint |
| Recolor fill | ~~`background`~~ | **Paint** → Composite | ⚠️ Repaint |

Rules of thumb: **to move, use `translate` (not `top`/`left`/`margin`). To resize, use
`scale` (not `width`/`height`). To fade, use `opacity`.**

### Refactor: an animated `box-shadow` → an `opacity` fade

A glowing hover with `transition: box-shadow` repaints a large blurred region every frame —
death on cheaper GPUs. The fix: **paint the shadow once** onto a pseudo-element, then
animate only that layer's **`opacity`**. Same look, compositor-cheap.

```css
/* ❌ Costly: repaints a big blur every frame */
.glow-bad {
  box-shadow: 0 0 0 rgba(99,102,241,0);
  transition: box-shadow .3s ease;
}
.glow-bad:hover { box-shadow: 0 8px 30px rgba(99,102,241,.6); }
```

```css
/* ✅ Cheap: the glow is pre-painted on ::after; we fade its opacity */
.glow-good { position: relative; }
.glow-good::after {
  content: "";
  position: absolute; inset: 0; z-index: -1;
  border-radius: inherit;
  box-shadow: 0 8px 30px rgba(99,102,241,.6);  /* painted ONCE */
  opacity: 0;                                   /* hidden until hover */
  transition: opacity .3s ease;                 /* compositor-friendly */
}
.glow-good:hover::after { opacity: 1; }
```

The blurred shadow is rasterized a single time; hovering just cross-fades an existing layer.
This trick — *pre-paint the expensive thing, animate its opacity* — works for shadows,
gradients, and glows alike.

---

## 3. `will-change` — a scalpel, not a seasoning

`will-change` tells the browser "this property is about to animate, promote it to its own
GPU layer *now*" so the first frame isn't janky.

```css
.btn:hover { will-change: transform; }   /* hint on intent */
.btn       { transform: translateY(0); transition: transform .2s ease; }
```

**Why you must NOT put it on everything.** Each promoted layer costs **GPU memory** and
bookkeeping. Slap `will-change: transform` on every button and you can *exhaust memory and
make the page slower* — the exact opposite of the goal. It's a promise you're asking the
browser to keep; keep the promise list short.

Best practice: **add it on hover-intent, remove it when the animation is done.** Applying it
on `:hover` (as above) is a clean CSS-only way to scope it — the layer is created when the
pointer arrives and released when it leaves. Reserve `will-change` for elements that
*genuinely* animate often. If a transition already feels smooth, you don't need it at all.

---

## 4. Focus visibility — never strand a keyboard user

The single most common accessibility crime in button CSS:

```css
.btn:focus { outline: none; }   /* ❌ NEVER ship this alone */
```

That deletes the *only* signal a keyboard user has for "where am I?" If you remove the
default outline, you **must** provide a replacement. The modern tool is `:focus-visible`,
which shows a ring for keyboard navigation but *not* on mouse click — exactly what everyone
wants.

```css
.btn:focus-visible {
  outline: 2px solid #818cf8;   /* a real outline, not box-shadow — see below */
  outline-offset: 2px;          /* push the ring off the button so it's not lost in the fill */
}
```

- **`outline`, not `border`** — `outline` doesn't take up layout space, so adding it never
  shifts the button. And unlike `box-shadow`, an `outline` is preserved in Windows High
  Contrast Mode (Section 5).
- **`outline-offset`** gives the ring breathing room so it reads on top of the button's own
  color and any adjacent element.

### Make the ring survive on ANY background

A single-color ring can vanish against a same-color background. Two robust tricks:

```css
/* A: double ring — a light outline plus a dark box-shadow gap.
   One of the two always contrasts, on light OR dark surfaces. */
.btn:focus-visible {
  outline: 2px solid #fff;
  outline-offset: 2px;
  box-shadow: 0 0 0 4px #000;   /* dark halo behind the white ring */
}
```

```css
/* B: let the ring pick up the current text color, which you've already
   chosen to contrast with the background. */
.btn:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 3px;
}
```

Never rely on the *button's own accent* as the ring color when the button might sit on that
same accent. Test your ring on your lightest and darkest surfaces.

---

## 5. Forced colors / Windows High Contrast Mode

When a user turns on **High Contrast** (or Contrast Themes) on Windows, the browser enters
**forced-colors mode**: it *throws away most of your colors* — backgrounds, box-shadows,
gradients, and images — and substitutes a small palette of user-chosen **system colors**.
This is great for the user and brutal for a button whose "edges" were made of `background`
and `box-shadow` alone: it can render as **invisible text on nothing**.

Detect it and shore up the button's structure:

```css
@media (forced-colors: active) {
  .btn {
    /* Your background may be dropped — a BORDER guarantees a visible edge.
       System color keywords are honored in forced-colors mode. */
    border: 1px solid ButtonText;
    /* Optional: opt back into the fill the system chose for buttons */
    background-color: ButtonFace;
    color: ButtonText;
  }
  /* Make the focus ring use the system highlight so it's always visible */
  .btn:focus-visible {
    outline: 2px solid Highlight;
    outline-offset: 2px;
  }
}
```

Key ideas:

- **Always keep (or add) a `border` on buttons.** It's the one part that reliably survives
  when the background is stripped, so the button keeps a visible shape. A transparent border
  in normal mode can become a visible one here.
- **Use system color keywords**, not hex: `ButtonText`, `ButtonFace`, `Highlight`,
  `HighlightText`, `Canvas`, `CanvasText`, `LinkText`, `GrayText` (for disabled). They map
  to the user's chosen theme.
- **`forced-color-adjust: none`** exists to *opt a specific element out* (e.g., a color
  swatch that must keep its color). Use it sparingly — the whole point is to defer to the
  user.

You don't need to redesign for High Contrast; you need to make sure the button is still
*perceivable and operable* when your palette is gone.

---

## 6. Hit targets & touch

A button the eye can see but the thumb can't hit is a broken button.

- **Minimum size: 44×44 CSS pixels.** That's Apple's HIG number and close to WCAG 2.5.5's
  44px target; WCAG 2.5.8 sets a floor of 24px. Aim for 44.
- A visually small button can still *meet* the target with padding, or by projecting an
  invisible tap area with a pseudo-element:

```css
/* Guarantee the box itself is at least 44×44, regardless of label length */
.btn {
  min-height: 44px;
  min-width: 44px;
  padding: .65em 1.25em;
}

/* Tiny icon button that stays visually small but hits 44×44 for touch */
.icon-btn { position: relative; width: 28px; height: 28px; }
.icon-btn::before {           /* invisible, centered 44×44 tap target */
  content: "";
  position: absolute;
  top: 50%; left: 50%;
  width: 44px; height: 44px;
  transform: translate(-50%, -50%);
}
```

Two more touch essentials:

```css
.btn {
  /* Kill the 300ms tap delay and double-tap-to-zoom on the button */
  touch-action: manipulation;
}

/* Only apply hover effects on devices that actually hover.
   Without this, a hover style can "stick" after a tap on a phone. */
@media (hover: hover) {
  .btn:hover { transform: translateY(-2px); }
}
```

`@media (hover: hover)` is the fix for the classic mobile bug where a tapped button keeps its
hover state until you tap elsewhere. Gate every non-essential hover effect behind it.

---

## 7. Don't rely on color alone

Roughly 1 in 12 men has some form of color-vision deficiency. If the *only* difference
between two button states (or two button meanings) is hue, those users can't tell them apart.
WCAG 1.4.1 requires a **second, non-color signal**.

```css
/* ❌ Only color distinguishes "danger" */
.btn-danger { background: #dc2626; }

/* ✅ Color PLUS an icon and a clear label */
```
```html
<button class="btn btn-danger" type="button">⚠️ Delete account</button>
<button class="btn" type="button">Cancel</button>
```

Add a redundant cue: an **icon**, an explicit **word** ("Error", "Success"), a **shape**, or
an **underline** for a selected/active tab-button. For a toggle, pair the color change with a
checkmark, a filled vs. outline icon, or `aria-pressed` reflected visually.

### Contrast, recapped (from Module 02)

- **Text on the button:** at least **4.5:1** for normal text, **3:1** for large text
  (~24px, or 19px bold). White-on-`#4f46e5` passes; white-on-`#a5b4fc` does not.
- **The button vs. its surroundings:** non-text UI (the button's edge/fill against the page)
  needs **3:1** so the control is discernible (WCAG 1.4.11).
- **Don't drop contrast on hover/focus** below these floors — a state change shouldn't make
  the label *harder* to read.

---

## 8. The ship-it checklist — DO / DON'T

**✅ DO**

- Reuse a real `<button>` with the correct `type`.
- Wrap all motion in a `prefers-reduced-motion: reduce` guard (or opt-in with
  `no-preference`).
- Animate **only `transform` and `opacity`**; pre-paint shadows/glows and fade their opacity.
- Provide a `:focus-visible` ring with `outline-offset` that survives on any background.
- Keep a **border** and honor **system colors** under `forced-colors: active`.
- Make targets **≥ 44×44px**; add `touch-action: manipulation`; gate hover with
  `@media (hover: hover)`.
- Back every color signal with an icon, word, or shape; hold text contrast ≥ **4.5:1**.

**❌ DON'T**

- Don't ship `outline: none` without a replacement.
- Don't animate `width`, `height`, `top`, `left`, `margin`, or (in a loop) `box-shadow` /
  `background`.
- Don't sprinkle `will-change` everywhere — it costs memory; scope it to hover-intent.
- Don't let an infinite animation ignore the reduced-motion request.
- Don't rely on `box-shadow` as your *only* focus indicator (it disappears in High Contrast).
- Don't make the whole button smaller than a thumb to "look tidy."
- Don't encode meaning in color alone.

---

## ✅ Check yourself

- [ ] Why `transition-duration: .01ms !important` instead of `transition: none` in the
      reduced-motion guard?
- [ ] Which render stage does animating `width` trigger, and why is that the expensive one?
- [ ] How do you turn an animated `box-shadow` hover into a compositor-friendly effect?
- [ ] Why is scoping `will-change` to `:hover` better than declaring it globally?
- [ ] What single property should you *always* keep on a button for `forced-colors: active`,
      and why?
- [ ] What's the minimum hit target, and what does `@media (hover: hover)` fix?

**Next:** [Module 15 — Capstone: Build a Button Design System →](../15-capstone-button-design-system/)
Then apply it all in the [challenge](./challenge.md) — refactor a genuinely bad button into a
good one.
