# Module 07 — Transitions & Timing Functions

**Goal:** make state changes *feel* good. Learn the `transition` shorthand and longhands,
which properties to animate (and which to never touch), how long a transition should last,
what each built-in easing *feels* like, and the pro moves — asymmetric in/out timing and
simple staggering.
⏱️ ~50 min · 🎯 Prereq: 06 (hover, focus, active states).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every easing, lift, and stagger below is running live on that page — race the
> five easings against each other and *watch* the difference.

In Module 06 you set the *destination* states (`:hover`, `:active`, `:focus-visible`). A
transition is the **journey between them**. Without one, states snap instantly; with one,
they glide. That glide is 90% of what makes a button feel expensive.

---

## 1. The `transition` shorthand (and its longhands)

A transition watches a property and, when its value changes, animates from old to new
instead of jumping. The shorthand takes four values **in this order**:

```css
.btn {
  /* property   duration   timing-function   delay */
  transition:   background-color   150ms   ease   0ms;
}
```

- **property** — *what* animates (`background-color`, `transform`, `opacity`, …).
- **duration** — *how long* it takes (`150ms`, `0.15s`). **Required** — a transition with
  no duration does nothing.
- **timing-function** — the *pacing* curve (`ease`, `linear`, `ease-out`…). Default `ease`.
- **delay** — how long to *wait* before starting. Default `0s`.

The same thing written as **longhands** — identical result, sometimes clearer:

```css
.btn {
  transition-property: background-color;
  transition-duration: 150ms;
  transition-timing-function: ease;
  transition-delay: 0ms;
}
```

**Where does the transition live?** On the **base rule**, not the `:hover`. The element
carries its transition at all times so it animates *both* into the hover state and back
out. (We'll bend this rule deliberately in §7.)

---

## 2. Transitioning multiple properties — and the `all` trap

To transition several properties, give a **comma-separated list**. Each entry is its own
mini-transition with its own timing — so different properties can move at different speeds:

```css
.btn {
  transition:
    background-color 150ms ease,
    transform        250ms ease-out,
    box-shadow       250ms ease-out;
}
```

That's the good way. Now the trap:

```css
/* ⚠️ Tempting, but risky */
.btn { transition: all 250ms ease; }
```

**`transition: all` animates *every* animatable property that ever changes** — including
ones you never intended. Add a `border` on hover, or let layout shift, and suddenly
`width`, `color`, `margin`, and things you didn't think about all animate too. That causes
two problems:

- **Accidental animations** — a property you tweak for an unrelated reason now visibly
  slides, producing motion you didn't design.
- **Jank** — `all` can catch expensive-to-animate properties (see §5) and drag your frame
  rate down.

**Rule: name the properties you mean.** It's a few more characters and it makes the
button's motion intentional and predictable. Reach for `all` only in throwaway prototypes.

---

## 3. How long? Duration guidance

Duration is a feel decision, and the sweet spot is **shorter than beginners expect**:

| Interaction | Duration | Why |
|---|---|---|
| Hover color, small state flips, tiny UI | **~100–200ms** | Feels instant but smooth |
| A visible move — lift, slide, larger element | **~200–350ms** | Long enough to read the motion |
| Anything longer on a *button* | usually too slow | Feels sluggish, blocks the user |

```css
.btn        { transition: background-color 150ms ease; }   /* snappy hover */
.card-lift  { transition: transform 250ms ease-out; }      /* a real move */
```

Two guardrails:

- **Under ~100ms** the eye barely registers the tween — it reads as a snap. Fine for
  micro-feedback, wasted effort for anything you want *seen*.
- **Over ~400ms** on a button feels laggy: the user has decided to move on and the UI is
  still catching up. Save long durations for large, deliberate page-level motion.

---

## 4. The five built-in timing functions

The timing function is the **velocity curve** — it doesn't change *where* the button ends
up, only *how it accelerates* getting there. Open the demo and race them side by side.

```css
.linear      { transition-timing-function: linear;      }
.ease        { transition-timing-function: ease;        } /* the default */
.ease-in     { transition-timing-function: ease-in;     }
.ease-out    { transition-timing-function: ease-out;    }
.ease-in-out { transition-timing-function: ease-in-out; }
```

What each one *feels* like:

- **`linear`** — constant speed, no acceleration. Mechanical. Correct for continuous things
  (a spinner, a marquee); feels robotic for UI state changes.
- **`ease`** — the default. Accelerates fast, coasts, eases out. A safe, natural
  general-purpose curve — slightly front-loaded.
- **`ease-in`** — starts slow, *speeds up* into the finish. It "leaves." Because it ends at
  full speed it can feel like the element yanks away — good for **exits**.
- **`ease-out`** — starts fast, *slows down* to a gentle stop. It "arrives." This is the
  most useful UI easing: elements decelerate into place the way real objects do.
- **`ease-in-out`** — slow at both ends, fast in the middle. Smooth and symmetric; nice for
  a move that goes and comes back, or a toggle.

**The rule that matters:** **`ease-out` for enter, `ease-in` for exit.** Things that appear
or move *toward* the user should decelerate into place (arrive gently); things that leave
should accelerate away. We use exactly this asymmetry in §7.

---

## 5. Transition `transform` and `opacity` — not layout

Not all properties are equal to animate. Some can be handed to the GPU and animated on a
separate compositor thread; others force the browser to recompute layout or repaint on
**every frame**, which is where jank comes from.

- ✅ **Cheap / smooth:** `transform` (translate, scale, rotate) and `opacity`. These are
  *composited* — buttery even under load.
- ⚠️ **Expensive:** `width`, `height`, `top`/`left`, `margin`, `padding` (trigger **layout**);
  `background-color`, `box-shadow`, `color` (trigger **paint** — usually fine in small doses,
  but avoid animating big shadows or huge areas).

So to make a button *lift* on hover, don't animate `top` — animate `transform`:

```css
.lift {
  transition: transform 200ms ease-out, box-shadow 200ms ease-out;
  box-shadow: 0 2px 6px rgba(0, 0, 0, .35);
}
.lift:hover {
  transform: translateY(-4px);              /* rises — composited, smooth */
  box-shadow: 0 12px 24px rgba(0, 0, 0, .45); /* shadow grows → sells the height */
}
.lift:active {
  transform: translateY(-1px);              /* presses back down */
}
```

That `translateY` + growing-shadow combo is the classic hover-lift. It reads as the button
physically rising off the page, and because the movement is a `transform`, it stays smooth.
(We go deep on *why* the compositor makes this fast in **Module 14 — Performance**.)

---

## 6. `delay` and simple staggering

`transition-delay` holds the transition before it starts. Give sibling parts *different*
delays and they animate in sequence — a **stagger** — which reads as choreographed and
deliberate rather than everything firing at once.

Here an icon leads and the label follows a beat later:

```css
.stagger .icon,
.stagger .label {
  display: inline-block;
  transition: transform 200ms ease-out;
}
.stagger:hover .icon  { transform: translateX(4px);  transition-delay: 0ms;  }
.stagger:hover .label { transform: translateX(4px);  transition-delay: 80ms; }
```

The icon moves, then 80ms later the label catches up. It's a tiny detail, but staggering is
what separates "things moved" from "that felt designed." Keep stagger gaps small on buttons
(50–120ms) — big gaps feel slow.

---

## 7. Asymmetric transitions — different in vs. out

Here's the trick that instantly upgrades a hover. Real objects don't enter and leave at the
same speed, and neither should your button. Per §4 you want **`ease-out` on the way in** and
**`ease-in` on the way out** — and often a *snappier* enter than exit (or vice-versa).

The mechanism is beautifully simple, and it's why the transition lives on the base rule:

- The transition declared on the **base rule** is used when going *back to* the resting
  state — that's your **"out"** timing.
- Override `transition` on **`:hover`** and *that* value is used while entering hover —
  your **"in"** timing.

```css
.asym {
  /* OUT: leaving hover — slower, ease-in (accelerates away) */
  transition: transform 260ms ease-in, background-color 260ms ease-in;
}
.asym:hover {
  /* IN: entering hover — quick, ease-out (snaps in, settles) */
  transition: transform 140ms ease-out, background-color 140ms ease-out;
  transform: translateY(-4px);
  background: #6366f1;
}
```

Hover on and it snaps up crisply; move away and it settles back with a slower, softer glide.
That in≠out feel is subtle but unmistakably premium — most polished buttons in the wild do
exactly this. (This asymmetry is *why* the transition belongs on the base rule, not `:hover`.)

---

## 8. Always guard motion

Some users get motion sick or simply prefer stillness, and the OS lets them say so. Honor it
— **reduce or remove** transitions when `prefers-reduced-motion: reduce` is set. The color
change can stay (it's not motion); the *movement* should go:

```css
@media (prefers-reduced-motion: reduce) {
  .lift, .lift:hover, .lift:active { transition: none; transform: none; }
  .asym, .asym:hover { transition-property: background-color; }
}
```

This isn't optional polish — it's an accessibility requirement. Every motion demo on this
page is guarded exactly this way.

---

## ✅ Check yourself

- [ ] What are the four values of the `transition` shorthand, in order — and which one is
      required for the transition to do anything?
- [ ] Why is `transition: all` risky, and what should you write instead?
- [ ] Roughly how long should a hover-color change take vs. a visible lift?
- [ ] Which easing for an element *entering*, and which for one *leaving*?
- [ ] Why prefer transitioning `transform`/`opacity` over `top`/`width`?
- [ ] Where do you put the "out" transition vs. the "in" transition to get asymmetry?

**Next:** [Module 08 — Bézier Curves & Custom Easing →](../08-bezier-curves-custom-easing/)
Then try the [challenge](./challenge.md).
