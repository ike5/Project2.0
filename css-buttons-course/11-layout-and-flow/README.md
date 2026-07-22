# Module 11 — Layout & Flow

**Goal:** stop thinking of a button as a word with padding and start treating it as a
tiny **flex container** — so icons and labels align perfectly, buttons snap together into
groups and split buttons, toolbars wrap gracefully, long labels truncate instead of
exploding, and a count badge sits exactly where you pin it.
⏱️ ~1.5 h · 🎯 Prereq: Module 10 (and the flexbox habits from Module 00).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every layout below is on screen there — resize the window to watch the toolbar
> and button rows wrap.

---

A `<button>` is already a flex container in this course — the baseline `.btn` from Module 00
is `display: inline-flex`. This module cashes that in. Everything here is **Flexbox applied
at two scales**: *inside* one button (aligning an icon next to a label) and *between* buttons
(groups, split buttons, toolbars). Same handful of properties both times.

---

## 1. Icon + label inside a button

The baseline already set this up. An icon and a label are two flex children; `gap` spaces
them and `align-items: center` keeps the icon's optical center on the text baseline-ish
midline. **Leading** vs **trailing** is just source order — put the icon before or after the
text node.

```css
.btn {
  display: inline-flex;      /* the button IS the flex row */
  align-items: center;       /* icon vertically centered on the label */
  justify-content: center;   /* whole group centered in the button */
  gap: .5em;                 /* em-based, so it scales with font-size */
}

/* keep icons from looking oversized — tie them to the text */
.btn svg { width: 1.1em; height: 1.1em; flex: none; }
```

```html
<!-- leading icon -->
<button class="btn" type="button">
  <svg aria-hidden="true" viewBox="0 0 24 24">…</svg>
  Download
</button>

<!-- trailing icon — same markup, icon after the label -->
<button class="btn" type="button">
  Continue
  <svg aria-hidden="true" viewBox="0 0 24 24">…</svg>
</button>
```

Two rules that matter more than they look:

- **`aria-hidden="true"` on every decorative icon.** The label already says "Download." A
  screen reader announcing "image, Download" is noise. Hide the icon; keep the text.
- **`flex: none` on the icon** (shorthand for `flex: 0 0 auto`). Without it, a shrinking
  flex row can squash an SVG. Icons should never shrink — text should (see §3).
- Size icons in **`em`**, not `px`. `1.1em` means the icon tracks the button's font-size, so
  small and large buttons stay proportional with zero extra rules.

An emoji works too and needs no sizing — `<span aria-hidden="true">⬇️</span>` — but SVG
gives you crisp, currentColor-tintable, resolution-independent icons.

---

## 2. Icon-only buttons (and the a11y rule you cannot skip)

Drop the label and you get a compact square or circle — a close button, a toolbar tool, a
"like." The catch: **there is no text left, so you must supply the accessible name yourself
with `aria-label`.** A screen reader on an unlabeled icon button announces literally
nothing useful ("button").

```css
.btn--icon {
  padding: 0;                 /* let width/height define the box, not padding */
  width: 2.5em; height: 2.5em;
  border-radius: 10px;        /* square with soft corners */
}
.btn--icon.round { border-radius: 50%; }   /* perfect circle */
.btn--icon svg { width: 1.25em; height: 1.25em; }  /* icon a bit bigger, no label to share space */
```

```html
<button class="btn btn--icon round" type="button" aria-label="Add to favorites">
  <svg aria-hidden="true" viewBox="0 0 24 24">…</svg>
</button>
```

Why it works and what to watch:

- **Equal `width` and `height`** with `padding: 0` gives a true square; `border-radius: 50%`
  makes it a circle. Because `align-items`/`justify-content: center` are inherited from
  `.btn`, the icon lands dead-center automatically.
- **`aria-label` is mandatory**, and the icon stays `aria-hidden`. Label on the button, icon
  hidden — the name comes from exactly one place.
- Mind the **hit target**: `2.5em` at a 16px base is 40px — right at the 44px comfort line.
  For touch UIs bump to `2.75em`+ or add invisible padding.

---

## 3. Truncating a label inside a flex row

Long labels in a fixed-width button (or a flex column) overflow and shove your layout
around. The fix is a classic three-part incantation — and the non-obvious fourth part that
makes it actually fire inside flexbox.

```css
.btn .label {
  overflow: hidden;
  text-overflow: ellipsis;   /* the … */
  white-space: nowrap;       /* don't wrap — one line only */
  min-width: 0;              /* ← THE one everyone misses */
}
```

**Why `min-width: 0`?** A flex item's default `min-width` is `auto`, which means "never
shrink below your content's intrinsic width." That default silently overrides `overflow:
hidden` — the item refuses to get narrow enough to clip, so the text pushes out instead of
truncating. Setting `min-width: 0` tells the item it *may* shrink past its content, and only
then do `overflow`/`text-overflow` get a chance to work.

```html
<button class="btn" style="max-width: 200px" type="button">
  <svg aria-hidden="true" viewBox="0 0 24 24">…</svg>
  <span class="label">This label is far too long to fit</span>
  <span class="count">3</span>
</button>
```

Wrap the truncating text in its own `<span class="label">` so the icon and the badge —
which should *not* truncate — keep their `flex: none` size while only the label clips.

---

## 4. Button groups & segmented controls

A segmented control is a **flex row of buttons that share edges**: no gap between them, only
the outermost corners rounded, and one shared border between neighbors instead of two.

```css
.group { display: inline-flex; }          /* row, no gap — buttons touch */

.group .btn {
  border-radius: 0;                        /* kill individual rounding… */
  border: 1px solid var(--line);
}
/* …then round only the outer corners */
.group .btn:first-child { border-radius: 10px 0 0 10px; }
.group .btn:last-child  { border-radius: 0 10px 10px 0; }

/* collapse the doubled shared border: every button but the first
   pulls left by 1px so its left border overlaps its neighbor's right */
.group .btn + .btn { margin-left: -1px; }

/* the active/hovered segment must sit ON TOP so its border wins */
.group .btn:hover,
.group .btn[aria-pressed="true"] { position: relative; z-index: 1; }
```

The three moves that make it look professional:

1. **`border-radius: 0` then re-round the ends** with `:first-child` / `:last-child`. The
   pill silhouette comes from the group, not the individual buttons.
2. **`margin-left: -1px` on `.btn + .btn`** overlaps adjacent borders so the seam is a
   single 1px line, not a 2px double line. `+` is the adjacent-sibling combinator: "a `.btn`
   immediately after another `.btn`" — i.e. everyone except the first.
3. **`z-index` on the active segment** so its (usually colored) border draws over the
   neighbor it overlaps, instead of being half-hidden under it.

For a *selection* control (pick one of three), use `aria-pressed` on the chosen segment —
it's the honest state for a toggle and it's what you style against.

---

## 5. Split buttons

A split button is one primary action plus a second, narrow segment — a caret that opens more
options. It's a two-child group where the first child is wide (the label) and the second is a
square caret, with a subtle divider between them.

```css
.split { display: inline-flex; }

.split .btn { border-radius: 0; }
.split .main { border-radius: 10px 0 0 10px; }   /* round the action's outer end */
.split .caret {
  border-radius: 0 10px 10px 0;                  /* round the caret's outer end */
  padding-inline: .6em;                          /* narrow — it's just an arrow */
  box-shadow: inset 1px 0 0 rgba(255,255,255,.25); /* the hairline divider */
}
.split .caret svg { width: 1em; height: 1em; }
```

```html
<div class="split">
  <button class="btn main" type="button">Save</button>
  <button class="btn caret" type="button" aria-label="More save options"
          aria-haspopup="menu">
    <svg aria-hidden="true" viewBox="0 0 24 24">…</svg>
  </button>
</div>
```

Notes:

- The caret is effectively an **icon-only button**, so it gets the same treatment: a real
  `aria-label` ("More save options"), icon `aria-hidden`, plus `aria-haspopup` to signal it
  opens a menu.
- The **divider** is an `inset box-shadow`, not a border — a border would add width and fight
  the shared-edge math. An inset shadow paints inside the box and costs no layout.
- Round only the two *outer* corners; the inner corners stay square so the seam is invisible.

---

## 6. Toolbars

A toolbar is a **wrap-friendly flex row**: many buttons, a `gap`, and `flex-wrap: wrap` so a
narrow screen stacks them onto new rows instead of overflowing. Use `justify-content` and an
`auto` margin to push groups apart.

```css
.toolbar {
  display: flex;
  flex-wrap: wrap;          /* never overflow — wrap to a new line */
  gap: .5rem;               /* even spacing, applies across wrapped rows too */
  align-items: center;
  padding: .5rem;
  border-radius: 12px;
  background: var(--panel);
}

/* push everything after this button to the far end */
.toolbar .spacer { margin-left: auto; }
```

```html
<div class="toolbar" role="toolbar" aria-label="Formatting">
  <button class="btn btn--icon" aria-label="Bold">…</button>
  <button class="btn btn--icon" aria-label="Italic">…</button>
  <button class="btn btn--icon" aria-label="Underline">…</button>
  <button class="btn spacer" type="button">Publish</button>
</div>
```

- **`gap` beats margins in a wrapping row.** It spaces items evenly *and* handles the vertical
  gap between wrapped rows — margins can't do the second part cleanly.
- **`margin-left: auto`** on one item eats all the free space to its left, shoving it (and
  everything after) to the right edge. It's the flexbox way to say "align this to the end."
- Give a real toolbar `role="toolbar"` and an `aria-label` so assistive tech announces it as
  one group.

---

## 7. Full-width & responsive buttons

On mobile, primary CTAs usually go **full-width**. And a wide button can push its icon and
label to opposite ends with `justify-content: space-between`.

```css
/* full-width CTA — block-level, fills its container */
.btn--block { display: flex; width: 100%; }

/* a wide button with content pushed to the two ends */
.btn--between { justify-content: space-between; }

/* let a row of buttons wrap on small screens instead of overflowing */
.btn-row { display: flex; flex-wrap: wrap; gap: .75rem; }
.btn-row .btn { flex: 1 1 auto; }    /* grow to share the row, wrap when too tight */
```

```html
<button class="btn btn--block btn--between" type="button">
  <span>Continue to payment</span>
  <svg aria-hidden="true" viewBox="0 0 24 24">…</svg>
</button>
```

- **`width: 100%` + `display: flex`** (not inline-flex) makes the CTA a full-width block.
  Keep `justify-content: center` for a centered label, or switch to `space-between` to send
  the label left and a chevron to the right edge — a common "next step" pattern.
- **`flex: 1 1 auto`** on buttons in a row lets them grow to fill the width and wrap onto new
  lines when the row runs out of room — responsive with no media query.

---

## 8. Badges & counters

A notification count is a small pill pinned to a button. Two ways: as a **flex child** (it
sits in the row, after the label) or **absolutely positioned** (it floats over a corner).
The floating version needs `position: relative` on the button as the anchor.

```css
/* inline pill — a normal flex child */
.count {
  flex: none;                         /* never shrink or truncate */
  min-width: 1.6em; padding: 0 .5em;
  height: 1.6em; border-radius: 999px;
  display: inline-flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,.22); font-size: .8em; font-weight: 700;
}

/* floating badge — pinned to the top-right corner */
.btn.has-badge { position: relative; }   /* ← anchor for the absolute child */
.badge {
  position: absolute; top: -.4em; right: -.4em;
  min-width: 1.4em; height: 1.4em; padding: 0 .35em;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 999px; background: #ef4444; color: #fff;
  font-size: .72em; font-weight: 700; line-height: 1;
  border: 2px solid var(--panel);       /* a ring so it reads as separate */
}
```

```html
<button class="btn has-badge" type="button">
  <svg aria-hidden="true" viewBox="0 0 24 24">…</svg>
  Inbox
  <span class="badge" aria-label="12 unread">12</span>
</button>
```

- **`position: relative` on the button** turns it into the positioning context, so the
  badge's `top`/`right` are measured from the button's own corner. Forget this and the badge
  jumps to the nearest positioned ancestor — often the whole page.
- **Give the badge an `aria-label`** ("12 unread") so the bare number reads as meaningful; the
  raw "12" alone is ambiguous to a screen reader.
- The **`border` ring** in the panel color fakes a cut-out, so the badge visually detaches
  from the button edge it overlaps.

---

## ✅ Check yourself

- [ ] Why must every decorative icon be `aria-hidden`, and every icon-only button carry an `aria-label`?
- [ ] What does `min-width: 0` fix, and why doesn't `overflow: hidden` alone truncate inside flexbox?
- [ ] In a segmented control, why `margin-left: -1px` on `.btn + .btn`, and why the `z-index` on the active segment?
- [ ] Which corners do you round in a group or split button, and with which selectors?
- [ ] What makes `justify-content: space-between` push an icon and label to opposite ends?
- [ ] Why does a floating badge need `position: relative` on the button?

**Next:** [Module 12 — Animated Gradients, Glow & Gradient Borders →](../12-animated-gradients-glow-borders/)
Then try the [challenge](./challenge.md).
</content>
</invoke>
