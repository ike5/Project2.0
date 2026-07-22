# Module 06 — States: Hover, Focus, Active & Disabled

**Goal:** make a button *respond*. Master every interactive state — `:hover`, `:active`,
`:focus-visible`, `:disabled` — plus the ARIA states (`aria-pressed`, `aria-busy`) that turn
a button into a toggle or a spinner. Do it in the right **source order**, and do it
accessibly on both mouse and touch.
⏱️ ~1.5 h · 🎯 Prereq: Module 05 (Shadows, Depth & Neumorphism).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Hover, click, and — crucially — **tab with your keyboard** to feel every state.

---

## 1. The state matrix, and why source order matters

A button is a little state machine. At any moment it may be in several states *at once* —
you can hover a button that's also focused and pressed. CSS resolves the conflict with two
rules: **specificity**, then **source order** as the tiebreaker. Every pseudo-class below
(`:hover`, `:focus`, `:active`, `:disabled`) has the *same* specificity — one class + one
pseudo-class. So when two of them match at the same time, **whichever is written last wins.**

For links there's the famous **LVHA** mnemonic (`:link`, `:visited`, `:hover`, `:active`).
For buttons the equivalent order that produces correct, predictable results is:

```css
/* Write states in THIS order. Same specificity → later rule wins ties. */
.btn            { /* 1. normal / resting */ }
.btn:hover      { /* 2. pointer is over it */ }
.btn:focus-visible { /* 3. keyboard-focused */ }
.btn:active     { /* 4. being pressed RIGHT NOW — should visually win over hover */ }
.btn:disabled   { /* 5. non-interactive — must override everything above */ }
```

Why this order:

- **`:active` after `:hover`** — while you press, the pointer is *also* hovering. You want
  the pressed look (the "down" feedback) to win, so `:active` must come **after** `:hover`.
- **`:disabled` last** — a disabled button might still receive `:hover`/`:focus` matches in
  some browsers. Putting `:disabled` last guarantees the "dead" look overrides them all,
  instead of relying on `!important`.
- **`:focus-visible` before `:active`** is a matter of taste — the focus ring is an
  `outline`, `:active` usually changes `transform`/`background`, so they don't fight. But
  keep it grouped with the "attention" states, above the press.

> **The mental model:** normal → intent (`:hover`) → keyboard target (`:focus-visible`) →
> commitment (`:active`) → unavailable (`:disabled`). Read top to bottom, that's the
> user's journey through the button.

---

## 2. `:hover` — and the touch problem

`:hover` means "the pointer is over this element." On a mouse, perfect. On a **touchscreen
there is no pointer that hovers** — so the browser fakes it: after a tap, the hover styles
*stick* until you tap somewhere else. The result is a button that looks permanently
hovered, or worse, "highlighted" long after you've moved on. It feels broken.

The fix is to **gate hover styles behind a media query** that only matches devices with a
real, precise, hovering pointer:

```css
/* Only apply :hover where a pointer can actually hover.
   hover: hover  → the primary input CAN hover (mouse, trackpad, stylus-with-hover)
   pointer: fine → the primary input is precise (not a fat fingertip) */
@media (hover: hover) and (pointer: fine) {
  .btn:hover { background: #4338ca; }
}
```

On a phone, that block simply doesn't apply, so hover never sticks. Touch users still get
`:active` feedback on tap (next section), which is what actually matters there.

- **`hover: hover`** vs **`hover: none`** — is the *primary* pointer capable of hovering?
- **`pointer: fine`** vs **`pointer: coarse`** — is it precise (mouse) or coarse (finger)?
- Using **both** is the belt-and-suspenders combo that reliably means "real mouse-like
  input." A hybrid laptop with a touchscreen reports the *primary* input, so a trackpad
  laptop still gets hover; a tablet in tablet mode doesn't.

Keep the resting and pressed styles **outside** the media query — every device needs those.

---

## 3. `:active` — instant pressed feedback

`:active` is true from the moment the user presses down until they release. It's your one
chance to say **"I felt that."** Latency-free tactile feedback is what makes a button feel
physical. The move is tiny — a couple of pixels down, a hair of scale, or an inset shadow
that reads as "pushed in":

```css
.btn:active {
  /* nudge down + shrink a touch = "pressed" */
  transform: translateY(1px) scale(0.98);
  /* optional: an inset shadow deepens the "pushed in" read */
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.25);
  background: #3730a3;
}
```

Rules of thumb:

- **Keep it small and fast.** 1–2px of travel, ~0.98 scale. Big movement feels mushy.
- **Transition `transform`, not layout.** `translate`/`scale` are compositor-only — they
  don't reflow the page and stay smooth. (Module 07 goes deep on this.)
- **`:active` fires on touch too** — this is the feedback phones actually get, and why
  gating `:hover` (§2) but *not* `:active` gives the best cross-device feel.

---

## 4. `:focus` vs `:focus-visible` — the accessibility linchpin

When you tab to a button, the browser draws a **focus indicator** so keyboard users know
where they are. Designers hate the default ring and reach for the single most damaging line
in CSS:

```css
/* ❌ NEVER do this alone. It strands every keyboard user. */
.btn:focus { outline: none; }
```

That removes the *only* signal a keyboard user has for "where am I?" It's a genuine WCAG
failure (2.4.7 Focus Visible). The reason people do it is legitimate, though: `:focus` also
fires on **mouse click**, leaving a ring after every click, which looks unpolished.

The modern answer resolves the tension completely — **`:focus-visible`**:

```css
/* Show a ring ONLY when the browser thinks a focus indicator is helpful —
   i.e. keyboard/programmatic focus, NOT a mouse click. */
.btn:focus-visible {
  outline: 2px solid #818cf8;
  outline-offset: 3px;   /* push the ring off the button so it's clearly visible */
}

/* Belt-and-suspenders: if you must kill the default ring, only kill it for the
   mouse case — and you've already replaced it above for the keyboard case. */
.btn:focus:not(:focus-visible) { outline: none; }
```

Key details:

- **`outline`, not `border` or `box-shadow`, for the ring** — `outline` doesn't affect
  layout (it won't shift the button), and critically it's **visible in forced-colors /
  Windows High Contrast mode**, where `box-shadow` is dropped.
- **`outline-offset`** lifts the ring off the edge so it reads clearly even against a busy
  background or a shadow.
- **Forced-colors mode.** If you *do* build a fancy ring with `box-shadow` (for rounded
  corners the outline can't follow on older engines), add a transparent `outline` as a
  fallback so a real ring still appears when the user forces system colors:

```css
.btn:focus-visible {
  box-shadow: 0 0 0 3px #0e1116, 0 0 0 5px #818cf8;  /* custom double ring */
  outline: 2px solid transparent;                    /* invisible normally… */
  outline-offset: 2px;
}
@media (forced-colors: active) {
  /* …but in forced colors, box-shadow is gone — the outline becomes the ring. */
  .btn:focus-visible { outline-color: Highlight; }
}
```

The one-line takeaway: **never `outline: none` without a replacement, and prefer
`:focus-visible` so the ring appears exactly when it helps and never when it annoys.**

---

## 5. `:disabled` vs `aria-disabled="true"`

There are two ways to disable a button, and they are **not** interchangeable.

**The real `disabled` attribute:**

```html
<button type="button" disabled>Save</button>
```

```css
.btn:disabled,
.btn[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
  /* clicks can't land anyway, but this makes intent explicit */
  pointer-events: none;
}
```

The browser does a lot for you here: the button is **removed from the tab order**, it
**can't be focused or clicked**, and screen readers announce "dimmed/unavailable." That's
the correct default for most cases.

**But there's a catch:** because it's unfocusable, a keyboard user **tabbing through can't
land on it** to discover *why* it's disabled — and there's no tooltip on an element you
can't focus. For a form's submit button that's disabled until the form is valid, users can
be left confused.

**`aria-disabled="true"`** is the alternative for exactly that case:

```html
<button type="button" aria-disabled="true">Save</button>
```

```css
.btn[aria-disabled="true"] {
  opacity: 0.5;
  cursor: not-allowed;
}
```

This keeps the button **focusable** (still in the tab order) and announces "dimmed" to
screen readers, so keyboard users *can* reach it and read a helper message. **The tradeoff:
it does *not* block the click.** `aria-disabled` is a promise to assistive tech, not a
behavior — you must prevent the action yourself (in real life, in JS; here, know that the
click still fires). Don't use `pointer-events: none` on it either, or you defeat the whole
point of keeping it reachable.

| | `disabled` attribute | `aria-disabled="true"` |
|---|---|---|
| In tab order? | **No** (unfocusable) | **Yes** (still focusable) |
| Click fires? | No (browser blocks it) | **Yes** (you must block it) |
| Screen reader | "unavailable" | "dimmed" |
| Use when | the action is simply off | you want the user to reach it & learn why |

Rule of thumb: reach for the **real `disabled` attribute** by default; switch to
**`aria-disabled`** only when discoverability matters more than hard-blocking the click.

---

## 6. Toggle (`aria-pressed`) and busy (`aria-busy`) states

A button can *hold* a state, not just fire once. ARIA gives you attributes you can both
style with an attribute selector **and** expose to screen readers — one source of truth.

**Toggle / pressed** — a button that stays "on" (mute, bold, follow):

```html
<button type="button" aria-pressed="false">🔔 Notifications</button>
```

```css
/* The attribute IS the state. Style off vs. on straight from ARIA —
   the screen reader hears "pressed", the eye sees the active look. */
.toggle[aria-pressed="true"] {
  background: #16a34a;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.35);  /* looks "sunken / on" */
}
.toggle[aria-pressed="true"]::before { content: "✓ "; }
```

Because the styling keys off `aria-pressed`, you can't get into the classic bug where the
button *looks* on but is announced as off — the attribute drives both. (Flipping the value
is a one-liner of JS in production; the point here is that the **CSS and semantics share the
attribute**.)

**Busy / loading** — a button working on something, with a CSS-only spinner:

```html
<button type="button" aria-busy="true">
  <span class="spinner" aria-hidden="true"></span>
  <span class="label">Saving…</span>
</button>
```

```css
/* When busy: dim the label, show the spinner, block re-clicks. */
.btn[aria-busy="true"] { cursor: progress; pointer-events: none; }
.btn[aria-busy="true"] .label   { opacity: 0.6; }

.btn .spinner { display: none; }         /* hidden until busy */
.btn[aria-busy="true"] .spinner {
  display: inline-block;
  width: 1em; height: 1em;
  border: 2px solid currentColor;
  border-top-color: transparent;         /* the "gap" that reads as spinning */
  border-radius: 50%;
  animation: btn-spin 0.7s linear infinite;
}
@keyframes btn-spin { to { transform: rotate(360deg); } }

/* Motion is not decoration here, but respect the preference anyway:
   slow the spin way down instead of freezing it dead. */
@media (prefers-reduced-motion: reduce) {
  .btn .spinner { animation-duration: 2.4s; }
}
```

`aria-busy="true"` tells assistive tech "this region is updating, hold on." Pairing it with
`pointer-events: none` stops the double-submit that plagues real forms.

---

## 7. Transitioning smoothly between states

State changes shouldn't *snap*. A short transition on the properties that change makes the
button feel liquid instead of jumpy — while the **press stays instant**:

```css
.btn {
  transition:
    background-color 0.18s ease,
    box-shadow       0.18s ease,
    transform        0.06s ease;   /* press feedback: near-instant on purpose */
}

/* Never animate away someone's motion preference. */
@media (prefers-reduced-motion: reduce) {
  .btn { transition-duration: 0.01ms; }
}
```

Principles:

- **Transition specific properties**, not `all` — `all` accidentally animates things you
  didn't mean to (and can hurt performance).
- **Color/shadow can be leisurely (~150–200ms); the press must be snappy (~50–80ms)** so it
  feels connected to your finger.
- **Guard motion** with `prefers-reduced-motion` — a hard rule for this whole course.

Module 07 is entirely about transitions and timing functions; this is the taste of it that
makes states feel good.

---

## ✅ Check yourself

- [ ] In what source order do you write `:hover`, `:active`, and `:disabled`, and why does
      `:active` come after `:hover`?
- [ ] Why do bare `:hover` styles misbehave on touchscreens, and which media query fixes it?
- [ ] Why is `outline: none` (alone) an accessibility bug, and how does `:focus-visible`
      resolve the mouse-vs-keyboard tension?
- [ ] Why prefer `outline` over `box-shadow` for a focus ring in forced-colors mode?
- [ ] `disabled` attribute vs `aria-disabled="true"`: which stays in the tab order, and
      which one still fires the click?
- [ ] How does keying styles off `aria-pressed` prevent the "looks on, announced off" bug?

**Next:** [Module 07 — Transitions & Timing Functions →](../07-transitions-and-timing/)
Then try the [challenge](./challenge.md).
