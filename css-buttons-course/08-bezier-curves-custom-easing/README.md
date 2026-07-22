# Module 08 — Bézier Curves & Custom Easing

**Goal:** stop *picking* easings and start *designing* them. Learn to read a cubic Bézier
curve, author `cubic-bezier()` by hand, use out-of-range Y values to get overshoot and
anticipation from a single curve, keep a gallery of great curves as tokens, and reach for
`steps()` and `linear()` when the job calls for them.
⏱️ ~2 h · 🎯 Prereq: 07 (Transitions & Timing — you know `transition` and the built-in easings).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. The curves below are abstract until you *see* the buttons move — hover the
> comparison grid and watch one button overshoot while the others just arrive.

---

## 1. What a cubic Bézier easing curve *is*

An easing function answers one question, continuously: **"at this fraction of the elapsed
time, how far along is the animation?"** Feed it time, it returns progress.

A CSS cubic Bézier is that function drawn as a curve in a unit square:

- **X axis = time**, normalized 0 → 1 (start of the transition → end).
- **Y axis = progress**, normalized 0 → 1 (start value → end value).
- **P0 = (0, 0)** and **P3 = (1, 1)** are **fixed** — every animation starts at 0% done at
  time 0 and ends at 100% done at time 1. You do **not** control these.
- **P1 and P2** are the two **control handles** you *do* control. Each is an (x, y) point.
  They pull the curve toward themselves like magnets, bending its shape.

```
  progress
   1.0 ┤                                   ● P3 (1,1)  ← fixed end
       │                            ,·—''''
       │                       ,·''
       │                    ,·'        ○ P2 (x2, y2)  ← you set this
       │                 ,·'         /
   0.5 ┤              ,·'          /
       │            ,'          /
       │          ,'         /
       │        ,'      ○ P1 (x1, y1)  ← you set this
       │      ,'      /
       │    ,'     /
   0.0 ●·——'————————————————————————————————→ time
     P0 (0,0)                              1.0
     ↑ fixed start
```

The four numbers in `cubic-bezier(x1, y1, x2, y2)` are exactly **P1** then **P2**. That's
the whole syntax — four numbers describe every easing you'll ever ship.

**The one hard rule:** the **X** values `x1` and `x2` must stay in **0–1**. Time can't run
backwards or overshoot its own duration, so the browser rejects `x` outside that range. The
**Y** values are free to go anywhere — negative, or above 1 — and that freedom is where all
the magic lives (section 4).

---

## 2. Reading a curve: shape → felt motion

The curve is a *position-over-time* graph, so its **slope is speed**. Read it like a
speedometer:

- **Steep segment → fast.** Progress is changing a lot per unit of time.
- **Flat segment → slow.** Little progress per unit of time.
- **A curve that starts flat and ends steep** → slow start, fast finish → *ease-in*
  (accelerates). Feels like something heavy getting moving.
- **A curve that starts steep and ends flat** → fast start, gentle finish → *ease-out*
  (decelerates). Feels like something gliding to a stop. **This is the workhorse for UI**
  because things that *arrive* should settle, not slam.
- **Steep–flat–steep is impossible** with one Bézier, but **flat–steep–flat** gives you
  *ease-in-out*: ramp up, cruise, ramp down. Reads as "smooth and deliberate."

```
 ease-in (slow→fast)     ease-out (fast→slow)     ease-in-out (slow→fast→slow)
   1 ┤            ,●        1 ┤      ,·—''●          1 ┤          ,·—●
     │          ,'           │   ,·'                  │        ,'
     │         /             │  /                     │       /
     │       ,'              │ /                      │      /
     │     ,'                │/                       │   ,·'
   0 ●——'                  0 ●                       0 ●—'
     └─────────→ t            └─────────→ t            └─────────→ t
```

Two practical habits:

- Match the curve to the physics you want the eye to believe. Entrances and things coming
  *toward* the user read best with **ease-out**. Exits often read well with **ease-in**
  (they pick up speed as they leave).
- **Duration and curve are separate knobs.** The curve is the *character* of the motion;
  the duration is *how long*. Same curve at 120 ms vs. 600 ms feels snappy vs. luxurious.

---

## 3. `cubic-bezier()` syntax — and recreating the built-ins

The five CSS keywords are just named cubic Béziers (with one exception). Knowing their
values demystifies them and lets you nudge from a familiar starting point:

```css
.demo {
  /* keyword            ≡  cubic-bezier equivalent            character */
  transition-timing-function: cubic-bezier(0.25, 0.1, 0.25, 1.0);  /* ease  (the default) */
  transition-timing-function: cubic-bezier(0.42, 0.0, 1.0,  1.0);  /* ease-in            */
  transition-timing-function: cubic-bezier(0.0,  0.0, 0.58, 1.0);  /* ease-out           */
  transition-timing-function: cubic-bezier(0.42, 0.0, 0.58, 1.0);  /* ease-in-out        */
  transition-timing-function: cubic-bezier(0.0,  0.0, 1.0,  1.0);  /* linear (a diagonal) */
}
```

Notes worth internalizing:

- **`ease` is not symmetric.** `cubic-bezier(.25,.1,.25,1)` accelerates briefly then spends
  a long time decelerating — that's why the browser default feels gentle-but-a-little-mushy.
  Designers often replace it with a cleaner ease-out.
- **`linear`** is a straight diagonal from (0,0) to (1,1): constant speed. It looks
  mechanical for movement, but it's the *correct* choice for continuous loops (spinners) and
  for things the eye reads as steady (progress bars, marquees). Don't use it for enter/exit
  of UI — real objects have inertia.
- You can write these as `cubic-bezier(...)` anywhere a timing function is expected:
  `transition`, `transition-timing-function`, and `animation-timing-function` (Module 09).

Store them once as **custom properties** so every button speaks the same motion language:

```css
:root {
  --ease-standard:  cubic-bezier(0.25, 0.1, 0.25, 1);   /* ≈ ease */
  --ease-in:        cubic-bezier(0.42, 0,   1,    1);
  --ease-out:       cubic-bezier(0,    0,   0.58, 1);
  --ease-in-out:    cubic-bezier(0.42, 0,   0.58, 1);
}

.btn { transition: transform .25s var(--ease-out); }
```

---

## 4. The magic: Y outside 0–1 → overshoot and anticipation

Here's the idea that separates flat UI from UI that feels *alive*. Because the **Y** (progress)
values are unconstrained, you can tell the animation to go **past** its target and come back,
or to **back up** before launching. One curve, real personality — no keyframes required.

- **Overshoot ("back" / follow-through):** set a control-point **Y > 1**. The curve rises
  above the top of the box, so progress exceeds 100% mid-flight, then settles to 1. The
  element flies slightly *past* its destination and eases back — the little "pop" you feel on
  a great toast or modal. Put the overshoot on **P2** (`y2 > 1`) so it happens near the
  *end*, on arrival.
- **Anticipation (wind-up):** set a control-point **Y < 0**. The curve dips below the
  bottom first, so the element moves slightly *backwards* before going forward — like a
  pitcher winding up. Put it on **P1** (`y1 < 0`) so the wind-up happens at the *start*.

```
  overshoot (y2 = 1.56)            anticipation (y1 = -0.6)
   progress                          progress
   1.5 ┤        ○ P2 (.64,1.56)       1 ┤              ,·—●
       │       / ‾‾●·—''   P3          │           ,·'
   1.0 ┤‑‑‑‑‑‑/‑‑‑‑‑‑‑‑‑‑‑‑‑          │        ,·'
       │     /   ← crosses 1,        0 ●——,‑‑‑‑‑‑‑‑‑‑‑‑‑ ← starts forward…
       │    /       then settles       │    \    ,'
       │  ,'                           │     '‑,'  ← …after dipping below 0
   0.0 ●'                          -0.6┤      ○ P1 (.36,-0.6)
       └────────────→ t                 └────────────→ t
```

```css
:root {
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);   /* y2 = 1.56 → overshoot */
  --ease-anticipate: cubic-bezier(0.36, -0.6, 0.66, -0.56); /* y1 < 0 → wind-up   */
}

/* A button that pops slightly past its hover scale, then settles — feels springy */
.btn-pop { transition: transform .4s var(--ease-out-back); }
.btn-pop:hover { transform: scale(1.15); }
```

The **magnitude** of the out-of-range Y controls how bouncy it feels. `y2 = 1.2` is a
whisper of overshoot; `y2 = 1.7` is a cartoonish boing. Tune to taste — and remember a
single Bézier can only cross its target **once**, so you get *one* overshoot, not a
multi-bounce. Real multi-bounce needs `@keyframes` (Module 10) or `linear()` (section 7).

---

## 5. A curated gallery of great curves (as tokens)

These are the curves worth memorizing — the same values used across the good design systems.
Drop them in once as custom properties and reach for them by *feel*, not by digits.

```css
:root {
  /* ---- decelerate: things arriving / entering (default choice for UI) ---- */
  --ease-out-quart: cubic-bezier(0.25, 1,    0.5,  1);    /* strong, clean deceleration    */
  --ease-out-expo:  cubic-bezier(0.16, 1,    0.3,  1);    /* dramatic: fast then long glide */
  --ease-out-circ:  cubic-bezier(0,    0.55, 0.45, 1);    /* rounded, mechanical settle     */

  /* ---- overshoot: playful "pop" on arrival ---- */
  --ease-out-back:    cubic-bezier(0.34, 1.56, 0.64, 1);  /* classic springy overshoot      */
  --ease-out-back-soft: cubic-bezier(0.22, 1.2, 0.36, 1); /* GENTLE overshoot — subtle pop  */

  /* ---- symmetric: deliberate moves, in AND out ---- */
  --ease-in-out-cubic: cubic-bezier(0.65, 0,   0.35, 1);  /* smooth, balanced               */
  --ease-in-out-back:  cubic-bezier(0.68, -0.6, 0.32, 1.6); /* wind-up + overshoot both ends */
}
```

**When to use which:**

| Token | Feel | Reach for it when… |
|-------|------|--------------------|
| `--ease-out-quart` | crisp deceleration | your everyday hover/enter; safe default |
| `--ease-out-expo` | fast, then a long luxurious glide | hero elements, big surfaces sliding in |
| `--ease-out-circ` | rounded, "weighted" stop | drawers, panels — feels physical |
| `--ease-out-back` | springy pop past the target | toasts, badges, "add to cart" confirmations |
| `--ease-out-back-soft` | a *hint* of overshoot | primary buttons — alive but not silly |
| `--ease-in-out-cubic` | smooth both directions | position swaps, reordering, toggles |
| `--ease-in-out-back` | wind-up then overshoot | attention-grabbing, playful transitions |

Rule of thumb: **decelerate (ease-out) for anything the user summons** (it arrives and
settles); **overshoot sparingly** — one confident pop reads as quality, overshoot on
everything reads as noise; **reserve `ease-in` (accelerate)** for things *leaving*.

---

## 6. `steps()` — stepped, mechanical motion

Not all motion should be smooth. `steps()` chops the transition into **N discrete jumps**
with no interpolation between them — perfect for a ticking clock, a sprite/frame flip, or a
typewriter reveal.

```css
/* steps(n, jump-term) — n equal jumps across the duration */
.tick   { transition: transform .8s steps(4, jump-end); }
.wind   { transition: transform .8s steps(4, jump-start); }
```

The **jump term** decides *when* the jumps land relative to the start/end:

- **`jump-end`** (default): hold the start value, jump at the *end* of each interval. The
  animation waits, then ticks. Reaches the final value only at the very end.
- **`jump-start`**: jump *immediately* at the start of each interval, then hold. Moves right
  away, then waits.
- (`jump-none` keeps both endpoints; `jump-both` adds a pause at each end — rarer.)

```
  jump-end (waits, then steps)      jump-start (steps, then waits)
   1 ┤              ┌────●           1 ┤        ┌────┘‾‾‾‾●
     │         ┌────┘                  │   ┌────┘
     │    ┌────┘                       │ ──┘
   0 ●────┘                          0 ●
     └───────────────→ t               └───────────────→ t
```

**Typewriter reveal** — the classic use, done with pure CSS (no JS):

```css
.type {
  width: 9ch;                       /* final width = characters to reveal */
  white-space: nowrap; overflow: hidden;
  border-right: 2px solid;          /* the caret */
  transition: width 1.2s steps(9, jump-end);  /* 9 chars → 9 discrete jumps */
}
.type:hover { width: 0; }           /* or animate 0 → 9ch to type it out */
```

Because there's no interpolation, `steps()` is also how you flip through a sprite sheet
frame-by-frame in an `@keyframes` animation (Module 09).

---

## 7. `linear()` — approximating springs and bounces

A single `cubic-bezier()` can cross its target only once, so it can't do a *multi*-bounce
(down, up, down, settle). The modern **`linear()`** easing function fixes this: you hand it a
list of progress checkpoints and the browser draws straight lines between them. With enough
points you can trace *any* shape — a damped spring, a bouncing ball, a wobble.

```css
:root {
  /* A bounce: overshoots, falls back, smaller bounce, settles. Each stop is a
     progress value; the browser interpolates linearly between them. */
  --bounce: linear(
    0, 0.063, 0.25, 0.563, 1 36%, 0.813, 0.75, 0.813,
    1 72%, 0.938, 0.938, 1
  );
}
.ball { transition: transform .9s var(--bounce); }
.ball:hover { transform: translateY(120px); }
```

Each entry is a Y (progress) value; an optional percentage pins it to a point in *time*
(the X). More stops = smoother the traced curve. You rarely hand-write these — you generate
them (e.g. from a spring simulator) and paste the result.

**Browser support (as of 2024+):** `linear()` shipped in Chrome/Edge 113+, Firefox 112+,
and Safari 17.4+. It's widely available now, but for older browsers **provide a fallback**:

```css
.ball {
  transition: transform .9s cubic-bezier(.34,1.56,.64,1); /* fallback: single overshoot */
  transition: transform .9s var(--bounce);                /* modern: true multi-bounce  */
}
```

A browser that doesn't understand the `linear()` line simply ignores it and keeps the
cubic-bezier above — graceful degradation for free. For the full spring/bounce toolkit
(and `@keyframes`-based bounces that work everywhere), see Modules 09 and 10.

---

## Accessibility: always guard motion

Everything in this module *moves*. Some users get motion sickness or vestibular symptoms from
it. **Wrap every non-essential motion** so it collapses to an instant, honest state change
for anyone who's asked the OS to reduce motion:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
```

Keep the *end state* (the hover color, the final position) — just remove the *journey*. And
never drop `:focus-visible`: a curve is decoration, a focus ring is a necessity.

---

## ✅ Check yourself

- [ ] Which two Bézier points are fixed, and what are their coordinates? Which two do you set?
- [ ] Why must `x1` and `x2` stay in 0–1, while `y1`/`y2` can be negative or above 1?
- [ ] On a position-over-time curve, does a *steep* segment mean fast or slow?
- [ ] Which control point (P1 or P2) gives you overshoot, and what Y value triggers it?
- [ ] What's the difference between `steps(4, jump-start)` and `steps(4, jump-end)`?
- [ ] Why does a single `cubic-bezier()` fail at a multi-bounce, and what solves it?

**Next:** [Module 09 — Keyframe Animations →](../09-keyframe-animations/)
Then try the [challenge](./challenge.md).
