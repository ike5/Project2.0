# Module 01 — Box Model, Sizing & Spacing

**Goal:** learn to *size* a button correctly — with `box-sizing`, padding, real hit
targets, a proper size scale, full-width CTAs, and clean spacing *between* buttons — so
every button you ship is comfortable to read and easy to tap.
⏱️ ~1 h · 🎯 Prereq: Module 00.

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every rule below is on screen there, live.

---

## 1. `box-sizing: border-box` — set it once, forever

By default, `width` and `height` describe the **content box** only. Padding and border are
then *added on top*, so a button you told to be `200px` wide with `16px` of horizontal
padding and a `2px` border actually renders at **236px**. That math is a bug factory.

`border-box` changes the meaning of `width`/`height` to "the whole box, padding and border
included." Now `width: 200px` means 200px, period — padding eats *into* it instead of
growing it.

```css
/* Put this at the very top of every stylesheet. Non-negotiable. */
*, *::before, *::after {
  box-sizing: border-box;
}
```

Why the universal selector? Because you want *every* element — including pseudo-elements
you'll add later for glows and gradient borders — to obey the same, predictable rule. Once
this is set, **every button rule in this course assumes it.** When you write
`min-width: 44px` or `width: 100%`, you mean the button's real footprint, not a number the
browser will silently inflate.

```
  content-box (default)              border-box (what you want)
  ┌─ width: 200px ─┐                 ┌──── width: 200px ────┐
  │ pad │ text │pad│ + border        │ pad │  text  │ pad │  border inside
  └─────┴──────┴───┘                 └─────┴────────┴──────┘
   actual: 236px                      actual: 200px  ✓
```

---

## 2. Padding is the real sizer — `em` vs `rem` vs `px`

Amateurs reach for `height` to size a button. Don't. **Padding is what sizes a button** —
it sets the breathing room around the label and, crucially, the clickable area. A button
sized by padding grows and shrinks gracefully with its content; a button pinned to a fixed
`height` clips or overflows the moment the label gets longer or the font scales up.

The unit you choose for padding decides *how* the button scales:

```css
/* px — absolute. Padding never changes, no matter the font size.
   A 20px-text button and a 12px-text button get the SAME padding →
   the small one looks bloated, the big one looks cramped. */
.btn-px { padding: 10px 20px; }

/* rem — relative to the ROOT font size. Great for consistent global
   spacing, but it ignores THIS button's font-size. */
.btn-rem { padding: 0.65rem 1.25rem; }

/* em — relative to THIS element's own font-size. This is the winner
   for buttons: padding scales WITH the label. */
.btn-em { padding: 0.65em 1.25em; }
```

**Why `em` wins for buttons.** `1em` equals the element's own `font-size`. So `0.65em 1.25em`
is "0.65× the text tall, 1.25× the text wide" — a *ratio*, not a fixed gap. Bump the
`font-size` and the padding, the gap between icon and label, and the whole button scale up
in perfect proportion. One rule, infinite sizes. That's the trick that makes §4a work.

> Rule of thumb: **`em` for a component's internal padding** (it should scale with the
> component), **`rem` for layout spacing between components** (it should stay consistent
> regardless of any one component's font size). We'll use exactly that split in §6.

---

## 3. Minimum hit targets — the 44×44 rule

A button can *look* fine and still be a failure: too small to tap. Fingers are blunt. A
label like "OK" with tight padding might render 24px tall — a coin-toss to hit on a phone,
and a real barrier for anyone with a motor impairment.

The guidance to memorize: **make interactive targets at least 44×44 CSS pixels.**
(Apple's HIG says 44pt; WCAG 2.5.5 *Target Size (Enhanced)* says 44×44; WCAG 2.5.8, the
newer AA rule, says 24×24 as a floor. Design for 44 and you clear all three.)

You don't enforce this with `height` — that fights §2. You enforce it with **minimums**:

```css
.btn {
  min-height: 44px;      /* never shorter than a fingertip */
  min-width: 44px;       /* icon-only buttons stay tappable too */
  padding: 0.65em 1.25em;/* still the real sizer for normal buttons */
  display: inline-flex;  /* so the label re-centers when min-height kicks in */
  align-items: center;
  justify-content: center;
}
```

`min-height`/`min-width` are a *floor*: padding sizes the button normally, and the minimum
only takes over when the content would otherwise be too small (think a bare icon or a
one-character label). Because the button is a flex container that centers its content, the
label stays perfectly centered when the floor stretches the box.

> **The clickable area is the whole padding box, not the text.** In the demo, the
> hit-target card overlays a translucent 44×44 patch so you can *see* that a comfortable
> button more than covers a fingertip — and that a stingy one leaves gaps you'll miss.

---

## 4. A size scale — two ways to build sm / md / lg

Real design systems ship three or four sizes. There are two clean ways to get them, and you
should understand both because they behave differently.

### 4a. Scale by `font-size` (the `em` payoff)

Because §2 made padding `em`-based, **changing one property — `font-size` — resizes the
entire button.** Padding, icon gap, and even a `rem`-free radius all move together.

```css
.btn {
  padding: 0.65em 1.25em;   /* em → everything below scales from font-size */
  border-radius: 0.5em;
}
.btn--sm { font-size: 0.8rem; }
.btn--md { font-size: 1rem; }   /* base */
.btn--lg { font-size: 1.25rem; }
```

One base rule, three sizes, zero duplicated padding values. This is the most maintainable
approach and the one to reach for first. The label's *type* scales too, which is usually
what you want (bigger button → bigger words).

### 4b. Scale by padding tokens

Sometimes you want the **text to stay the same size** but the button to get chunkier — a
big CTA with normal-sized words. Then hold `font-size` steady and drive the size with
padding tokens (custom properties):

```css
.btn {
  padding: var(--btn-pad-y) var(--btn-pad-x);
  --btn-pad-y: 0.65em;
  --btn-pad-x: 1.25em;
}
.btn--sm { --btn-pad-y: 0.4em;  --btn-pad-x: 0.9em;  font-size: 0.85rem; }
.btn--md { --btn-pad-y: 0.65em; --btn-pad-x: 1.25em; }
.btn--lg { --btn-pad-y: 1em;    --btn-pad-x: 1.75em; }
```

Tokens make the scale *explicit and tunable* — a designer can hand you three padding pairs
and you drop them straight in. Use **4a** when you want type and box to scale together;
use **4b** when you want independent control. The demo shows both rows side by side.

---

## 5. Inline vs block, and full-width mobile CTAs

A `<button>` is **inline-level** by default: it sits in the text flow and is only as wide as
its content. `display: inline-flex` (from Module 00) keeps that inline behavior while
letting us center content. That's the right default for buttons in a row.

But on mobile, the primary call-to-action usually wants to be **full-width** — a big, easy
thumb target spanning the screen:

```css
/* Opt-in modifier — a block-level, full-width button */
.btn--block {
  display: flex;      /* flex, not inline-flex → becomes block-level */
  width: 100%;        /* fill the container (which border-box makes honest) */
}
```

`width: 100%` fills the *parent's* content width — so constrain it by wrapping the button in
a container, not by hard-coding pixels. A common, responsive pattern: buttons are auto-width
on desktop and go full-width only on narrow screens.

```css
@media (max-width: 30rem) {
  .btn--cta { display: flex; width: 100%; }
}
```

Notice we never set a pixel width. `width: 100%` + `box-sizing: border-box` means the
button fills its container exactly, padding included — no overflow, no horizontal scrollbar.

---

## 6. Spacing *between* buttons — use `gap`, not margins

You have two buttons side by side. How do you space them? The old way was
`margin-right` on all-but-the-last — fiddly, error-prone, and it leaks margin onto the
edges. **The modern way is a flex (or grid) container with `gap`.**

```css
/* A button row: put the space on the CONTAINER, not the buttons. */
.btn-row {
  display: flex;
  flex-wrap: wrap;     /* buttons wrap instead of overflowing on small screens */
  gap: 0.75rem;        /* rem: layout spacing, consistent regardless of button size */
  align-items: center;
}
```

Why `gap` beats margins:

- **No edge leak.** `gap` only inserts space *between* items, never before the first or
  after the last. Margins do, and then you're writing `:not(:last-child)` hacks.
- **It survives wrapping.** With `flex-wrap`, `gap` spaces items both horizontally *and*
  vertically when they wrap to a new line. Margins can't do that cleanly.
- **One number, one place.** Change the container's `gap` and the whole row re-spaces.

A **toolbar** is the same idea, with alignment control — group related actions, push others
to the far end with `margin-left: auto` or a spacer:

```css
.toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 12px;
  background: #161b22;
}
.toolbar .spacer { margin-left: auto; }  /* everything after this hugs the right edge */
```

Note the unit choice, straight from §2's rule of thumb: **`gap` is `rem`** (layout spacing,
stays consistent) while the buttons' internal **padding is `em`** (scales with each button).

---

## 7. `line-height` and vertical centering of the label

The label's *vertical* position inside a button is set by two things working together:

1. **`line-height`** — the height of the text's line box. A large `line-height` (say `1.8`)
   adds space above and below the text *inside the content box*, which quietly inflates the
   button and can throw off your padding math. Keep it tight for buttons:

```css
.btn {
  line-height: 1.2;   /* tight — the label is one line; don't add stray vertical space */
}
```

2. **Flex centering** — with `display: inline-flex; align-items: center`, the label is
   centered in the button's box regardless of `line-height`, ascenders, or descenders. This
   is more robust than the old `line-height: <height>` trick (which only works for a fixed
   single-line height and breaks the instant the text wraps).

```css
.btn {
  display: inline-flex;
  align-items: center;      /* vertical centering — robust, wrap-safe */
  justify-content: center;  /* horizontal centering */
  line-height: 1.2;         /* keep the line box tight so centering is exact */
}
```

Why not just crank `line-height` to center? Because `line-height` centers text only for a
*single* line at a *known* height. The moment a label wraps to two lines, or you add an
icon of a different height, line-height centering falls apart. Flex centering doesn't care —
it centers whatever's inside, however tall. Use flex for position; use `line-height` only to
keep the line box from adding unwanted height.

---

## ✅ Check yourself

- [ ] What does `box-sizing: border-box` change about what `width` means — and why does
      every button rule assume it?
- [ ] Why is `em`-based padding better than `px` for a button that needs multiple sizes?
- [ ] What's the target-size number to design for, and which property (not `height`)
      enforces it?
- [ ] Two ways to build a size scale — when do you pick font-size vs. padding tokens?
- [ ] Why is `gap` on a flex container better than `margin` for spacing a button row?
- [ ] Why centre the label with flexbox instead of a big `line-height`?

**Next:** [Module 02 — Typography, Color & Contrast →](../02-typography-color-contrast/)
Then try the [challenge](./challenge.md).
