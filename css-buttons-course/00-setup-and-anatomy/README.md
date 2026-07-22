# Module 00 — Setup & Anatomy of a Button

**Goal:** understand what a button *is* in HTML, tame the browser's default styling, and
build a clean, accessible baseline you'll style in every later module.
⏱️ ~45 min · 🎯 Prereq: basic CSS.

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Everything below is on screen there.

---

## 1. Your tools (there is no setup)

You need a **text editor** and a **browser**. No Node, no build step. To see any example:

```bash
open demo.html      # macOS
xdg-open demo.html  # Linux
start demo.html     # Windows
```

…or just drag the file onto a browser tab. Edit, save, refresh. That's the whole loop.

---

## 2. Use the right element

A button should almost always be a real `<button>`:

```html
<button type="button">Click me</button>
```

**Why not a `<div>` or `<a>`?** The `<button>` element is *free accessibility*: it's
focusable with the keyboard, it fires on **Enter** and **Space**, screen readers announce
it as "button," and it participates in forms. A styled `<div>` gives you none of that
unless you reimplement it all by hand (and you'll get it wrong).

- Use **`<button>`** for an action (submit, open a menu, toggle).
- Use **`<a>`** for navigation (going to a URL). Style it *like* a button if you want, but
  it's semantically a link.
- Set **`type`** explicitly. Inside a `<form>`, a `<button>` defaults to `type="submit"`
  and will submit the form — often a surprise. Use `type="button"` unless you mean submit.

---

## 3. The anatomy

A button is just a **box with a label**, but naming the parts helps you talk about design:

```
        ┌───────────────────────────────────┐  ← border (border)
        │        ↑ padding-block             │
        │  ⭢  [icon]  Label text   ⭠         │  ← content (label, optional icon)
        │        ↓ padding-block             │
        └───────────────────────────────────┘
         └─ padding-inline ─┘
   the whole box sits in the page's flow and has a background
```

- **Content** — the label (text), sometimes an icon. This is what the user reads.
- **Padding** — space *inside* the button around the content. This is what gives a button
  its comfortable size and its clickable area. (Module 01.)
- **Border** — the edge. May be visible, invisible, or a gradient. (Module 03.)
- **Background** — the fill behind the content. (Modules 04–05.)
- **Radius** — how rounded the corners are. (Module 03.)

Every later module styles one of these parts.

---

## 4. The browser's defaults are fighting you

Un-styled `<button>` elements inherit an ugly, inconsistent, OS-dependent look (the classic
gray bevel). Before designing, **reset** those defaults so you start from a blank surface:

```css
button {
  /* kill the OS chrome */
  appearance: none;
  -webkit-appearance: none;
  background: none;
  border: none;

  /* buttons don't inherit font by default — fix that */
  font: inherit;
  color: inherit;

  /* sane interaction defaults */
  cursor: pointer;
  /* remove the 300ms tap delay & double-tap zoom on touch */
  touch-action: manipulation;
  /* no text selection flicker on double-click */
  user-select: none;
}
```

Two lines people forget and always regret:

- **`font: inherit;`** — buttons do *not* inherit `font-family`/`font-size` from the page.
  Without this, your button text is a different font than everything around it.
- **`cursor: pointer;`** — signals "this is clickable." (Some teams reserve the pointer
  cursor for links; either way, be deliberate.)

---

## 5. The accessible baseline button

Here's the starting point we'll build on. It's plain on purpose — but it's *correct*:

```css
.btn {
  /* reset */
  appearance: none;
  border: none;
  font: inherit;

  /* box */
  display: inline-flex;          /* lets us center content & add icons later */
  align-items: center;
  justify-content: center;
  gap: 0.5em;                    /* space between icon and label */
  padding: 0.65em 1.25em;        /* comfortable, em-based so it scales with text */
  border-radius: 8px;

  /* look */
  background: #4f46e5;
  color: #fff;
  font-weight: 600;
  line-height: 1.2;

  /* interaction */
  cursor: pointer;
  touch-action: manipulation;
  user-select: none;
  transition: background-color 0.15s ease;
}

.btn:hover  { background: #4338ca; }
.btn:active { background: #3730a3; }

/* NEVER remove focus without replacing it. This shows a ring only for
   keyboard users, not on mouse click — the modern, correct approach. */
.btn:focus-visible {
  outline: 2px solid #4f46e5;
  outline-offset: 2px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

Notes on the choices — these are habits worth forming early:

- **`display: inline-flex`** with `align-items/justify-content: center` means the label is
  perfectly centered and you can drop in an icon later with zero rework.
- **`em`-based padding** (`0.65em 1.25em`) makes the button scale with its font size, so one
  rule gives you proportional small/large buttons just by changing `font-size`.
- **`:focus-visible`, not `:focus`** — never do `outline: none` and stop there. That
  strands keyboard users. `:focus-visible` shows a ring for keyboard navigation but not on
  mouse clicks, which is what everyone actually wants.
- **`:disabled`** communicates non-interactivity. Prefer the real `disabled` attribute so
  the button is also removed from the tab order.

---

## 6. The mental model for the rest of the course

Think of a button as **layers you compose**:

```
  motion         ← transitions, easing, keyframes   (Modules 07–10)
  ─────────────────────────────────────────────────
  depth          ← shadows, glow                     (Module 05)
  surface        ← background / gradient             (Module 04, 12)
  shape          ← radius, border, clip-path         (Module 03)
  content        ← label, icon, layout               (Modules 01–02, 11)
  semantics      ← the real <button>, states, a11y   (Modules 00, 06, 14)
```

You'll add one layer at a time. By the capstone you'll stack them into a full design system.

---

## ✅ Check yourself

- [ ] Why is a real `<button>` better than a styled `<div>` for an action?
- [ ] What does `font: inherit` fix on a button?
- [ ] Why `:focus-visible` instead of `:focus` — and why never a bare `outline: none`?
- [ ] What does `em`-based padding buy you?

**Next:** [Module 01 — Box Model, Sizing & Spacing →](../01-box-model-sizing-spacing/)
Then try the [challenge](./challenge.md).
