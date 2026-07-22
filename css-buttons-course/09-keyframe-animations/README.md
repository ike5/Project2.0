# Module 09 — Keyframe Animations

**Goal:** move beyond one-shot transitions into *multi-step, self-running* motion with
`@keyframes` — and build the five animations every real app needs: **pulse, shimmer,
spinner, shake, and a drawn success check**.
⏱️ ~2 h · 🎯 Prereq: 08 (Bézier Curves & Custom Easing).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every animation below is running live on that page — nothing needs JavaScript.

---

## 0. Transition vs. animation — pick the right tool

A **transition** (Module 07) interpolates *one* property from state A to state B when
something changes — a hover, a class toggle. It needs a trigger and it goes one direction.

An **animation** runs a **timeline you author** with `@keyframes`: as many steps as you
like, it can **loop**, **reverse**, **delay**, **hold its end state**, and — crucially —
it can **start on its own with no trigger**. A spinner has no "from state" to hover away
from; it just spins forever. That's the job of `@keyframes`.

Rule of thumb: *state change → transition; standalone timeline or loop → animation.*

---

## 1. `@keyframes`: the timeline

You define a named timeline once, then attach it to elements. There are two syntaxes.

**`from` / `to`** — a simple two-stop animation (identical to `0%` / `100%`):

```css
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
```

**Percentage keyframes** — as many stops as you want along the 0%→100% timeline:

```css
@keyframes pulse {
  0%   { transform: scale(1);    opacity: 1;   }
  50%  { transform: scale(1.08); opacity: .85; }  /* the mid-point */
  100% { transform: scale(1);    opacity: 1;   }  /* back to start → seamless loop */
}
```

Three things worth knowing:

- **Any property not listed at a keyframe** keeps its base value (or interpolates between
  the nearest stops that *do* mention it). You only write what changes.
- **You can group stops:** `0%, 100% { … }` applies one block to both ends — perfect for a
  loop that must return home.
- **The percentages are of the `animation-duration`,** not of time in seconds. Change the
  duration and every stop rescales automatically.

---

## 2. The `animation` shorthand and its longhands

You *could* write eight longhand properties. In practice you write the shorthand and reach
for a longhand only when you need to override one piece. Here is every longhand, annotated:

```css
.thing {
  animation-name: pulse;                 /* which @keyframes to run */
  animation-duration: 1.5s;              /* one cycle's length (REQUIRED to see anything) */
  animation-timing-function: ease-in-out;/* the easing WITHIN each cycle (Module 08 curves work here) */
  animation-delay: 0s;                   /* wait before the first cycle */
  animation-iteration-count: infinite;   /* a number, or `infinite` */
  animation-direction: alternate;        /* normal | reverse | alternate | alternate-reverse */
  animation-fill-mode: none;             /* none | forwards | backwards | both (see §4) */
  animation-play-state: running;         /* running | paused (see §4) */
}
```

The **shorthand** packs them in this canonical order — *name, duration, timing, delay,
iteration-count, direction, fill-mode, play-state*:

```css
/* animation: name duration timing delay iteration direction fill play; */
.thing { animation: pulse 1.5s ease-in-out 0s infinite alternate both running; }

/* Realistically you write just what you need: */
.pulse   { animation: pulse 1.5s ease-in-out infinite; }
.spinner { animation: spin 0.7s linear infinite; }
.shake   { animation: shake 0.4s ease-in-out both; }   /* runs once */
```

Reading the shorthand: the **first `<time>` is duration, the second is delay** (order
matters — that's the only way the browser tells them apart). A bare number is the
iteration count. Keywords (`infinite`, `alternate`, `forwards`, `paused`) land in their
own slots. `linear` timing keeps a spinner perfectly even; `ease-in-out` gives a pulse its
soft breathing feel.

**`direction: alternate`** is a favorite trick: instead of jumping from 100% back to 0%,
the animation plays *forward, then backward, then forward…* You often write only the
"forward" half of a loop and let `alternate` handle the return for free.

---

## 3. Five recipes you'll use forever

Each is a complete `@keyframes` block plus the class that uses it. Steal them.

### 3a. Pulse — "look at me"

A gentle scale + fade loop that draws the eye to a primary CTA without shouting.

```css
@keyframes pulse {
  0%, 100% { transform: scale(1);    }
  50%      { transform: scale(1.06); }
}
.cta-pulse { animation: pulse 1.6s ease-in-out infinite; }
```

For an even stronger "ping," animate a **`box-shadow` ring** that expands and fades:

```css
@keyframes ping-ring {
  0%   { box-shadow: 0 0 0 0 rgba(79,70,229,.55); }
  100% { box-shadow: 0 0 0 16px rgba(79,70,229,0); }  /* grows out & fades to 0 */
}
.cta-ping { animation: ping-ring 1.6s ease-out infinite; }
```

### 3b. Shimmer / skeleton loading

The gray "content is loading" placeholder. The trick: a **gradient background wider than
the element**, whose `background-position` slides a bright band across it. Note
`background-size: 200%` — the gradient is twice as wide as the box, so there's room to move.

```css
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }   /* slide the highlight left across the box */
}
.skeleton {
  background: linear-gradient(
    100deg,
    #1b2230 30%,          /* base */
    #2b3446 50%,          /* the moving highlight */
    #1b2230 70%
  );
  background-size: 200% 100%;               /* room for the position to travel */
  animation: shimmer 1.4s linear infinite;
  color: transparent;                       /* hide any placeholder text */
}
```

Animate **`background-position`, not `background-image`** — position is cheap; regenerating
the gradient every frame is not.

### 3c. Spinner — a rotating ring (for loading buttons)

The classic: a circle with a visible border on three sides and **one transparent side**,
rotated forever. The gap is what makes it read as "spinning."

```css
@keyframes spin { to { transform: rotate(360deg); } }   /* `to` only — starts at 0 implicitly */

.spinner {
  width: 1.1em; height: 1.1em; border-radius: 50%;
  border: 2px solid rgba(255,255,255,.35);   /* the faint track */
  border-top-color: #fff;                    /* one bright arc… */
  animation: spin 0.7s linear infinite;      /* …spun round = a loader */
}
```

`linear` is non-negotiable here — any easing makes the spin visibly stutter each cycle.

### 3d. Shake — error feedback (runs once)

A quick left-right jitter to say "that didn't work." It should fire **once**, not loop, or
it becomes an anxious buzz. Keep the travel small (a few px) and fast.

```css
@keyframes shake {
  0%, 100%      { transform: translateX(0); }
  20%, 60%      { transform: translateX(-5px); }
  40%, 80%      { transform: translateX(5px); }
}
.shake { animation: shake 0.4s ease-in-out both; }   /* one shot; `both` holds ends cleanly */
```

In the demo we retrigger it on `:hover` so you can watch it repeatedly without JS; in a
real app you'd add the class in response to a failed action.

### 3e. Success — a checkmark that draws itself

The most satisfying micro-interaction there is. Draw a check as an inline SVG `<path>`,
then animate the **stroke** so the line appears to be *drawn*. The mechanism:
`stroke-dasharray` makes the stroke one long dash the length of the whole path;
`stroke-dashoffset` pushes that dash out of view; animating the offset to `0` reels it in.

```css
@keyframes draw {
  to { stroke-dashoffset: 0; }              /* pull the dash into view = "drawing" */
}
.check-path {
  stroke-dasharray: 32;                     /* ≈ the path's total length */
  stroke-dashoffset: 32;                    /* start fully hidden */
  animation: draw 0.4s ease-out 0.1s forwards;  /* `forwards` = stay drawn at the end */
}
```

`fill-mode: forwards` is essential here — without it the check would snap back to hidden
the instant the animation ends. (More on that next.)

---

## 4. Holding, pausing, and controlling playback

### `animation-fill-mode` — what happens *outside* the run

By default an element reverts to its un-animated look before the delay and after the last
iteration. `fill-mode` changes that:

- **`forwards`** — after finishing, **freeze on the last keyframe.** This is how a
  draw-once check *stays* drawn, or a fade-in stays visible.
- **`backwards`** — during any `delay`, apply the *first* keyframe immediately (so a
  delayed fade-in starts invisible instead of flashing at full opacity first).
- **`both`** — do both. A safe default for one-shot animations.

```css
.draw-once { animation: draw 0.4s ease-out forwards; } /* holds the finished state */
```

### `animation-play-state` — pause on demand, no JS

`paused` freezes an animation mid-flight; `running` resumes it. You can toggle it with pure
CSS — for example, **pause a marquee/shimmer on hover** so users can read it:

```css
.ticker           { animation: shimmer 1.4s linear infinite; }
.ticker:hover     { animation-play-state: paused; }   /* freeze while hovered */
```

The animation keeps its position; it doesn't reset — it just stops the clock.

---

## 5. Layering: multiple animations on one element

`animation` is a **comma-separated list.** You can run several independent timelines on the
same element at once — each with its own duration, easing, and loop count. Perfect for a
button that both floats *and* glows:

```css
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
@keyframes glow  { 0%,100% { box-shadow: 0 0 12px rgba(79,70,229,.4); }
                   50%     { box-shadow: 0 0 24px rgba(79,70,229,.8); } }

.alive {
  animation:
    float 3s   ease-in-out infinite,
    glow  1.8s ease-in-out infinite;   /* two clocks, different tempos, one element */
}
```

Two cautions: **don't animate the same property in two layers** (they fight — last one
wins), and if you set longhands like `animation-duration` alongside a multi-value
`animation`, provide a matching comma-separated list or the extras get defaults.

---

## 6. Respect `prefers-reduced-motion` — always

Looping, pulsing, sliding motion can trigger vestibular disorders and is plainly
distracting for many users. The OS exposes a "reduce motion" setting; honor it. Wrap
**every** attention/loop animation and either kill it or tame it to a non-moving cue:

```css
@media (prefers-reduced-motion: reduce) {
  .cta-pulse, .cta-ping, .skeleton, .spinner, .shake, .alive {
    animation: none !important;        /* stop the motion entirely */
  }
  /* Keep a *functional* substitute where motion carried meaning: */
  .spinner { border-top-color: #fff; opacity: .8; }  /* still reads as a busy indicator */
  .check-path { stroke-dashoffset: 0; }              /* just show the finished check */
}
```

The principle: **decorative motion → remove it. Functional motion (a loader, a drawn
check) → show the end state statically** so the *information* survives even when the
*motion* doesn't. This isn't optional polish; it's a correctness requirement, which is why
every animation in `demo.html` is guarded this way.

---

## ✅ Check yourself

- [ ] When do you reach for `@keyframes` instead of a `transition`?
- [ ] In the `animation` shorthand, how does the browser tell **duration** from **delay**?
- [ ] Why must a spinner use `linear` timing?
- [ ] What does `animation-fill-mode: forwards` do, and why does the success check need it?
- [ ] How do `stroke-dasharray` + `stroke-dashoffset` make an SVG line "draw itself"?
- [ ] How do you pause an animation on hover with **no JavaScript**?
- [ ] What must you do for **every** looping animation to be accessible?

**Next:** [Module 10 — Bounces, Springs & Advanced Motion →](../10-bounces-springs-advanced-motion/)
Then try the [challenge](./challenge.md).
