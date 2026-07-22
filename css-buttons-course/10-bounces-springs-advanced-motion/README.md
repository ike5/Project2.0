# Module 10 — Bounces, Springs & Advanced Motion

**Goal:** make a button feel *alive* — bounce, spring, pop, wobble, and choreograph its
parts — by turning the easing (Module 08) and keyframes (Module 09) you already know into
motion that overshoots, settles, and delights.
⏱️ ~2 h · 🎯 Prereq: 09 (keyframes) — and 08 (custom easing) close by.

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every curve below is on screen there — hover, press, and reload to replay the
> entrances.

---

## 0. The one idea behind all of it: **overshoot + settle**

Real objects have mass. When a real thing moves to a new spot, it doesn't glide to a
perfect stop — it goes a little *too far*, then comes back. A dropped ball sinks past its
resting height (well, it can't, but its squash does), springs up past it, and wobbles down
to rest. That overshoot-and-settle is the entire difference between motion that feels
mechanical and motion that feels **physical**.

Every effect in this module is one of two recipes for overshoot:

1. **One move, one overshoot** — a single `transition` on a curve whose Bézier handle pokes
   *past* the endpoint (an "ease-out-back"). Cheap, great for hovers and presses.
2. **Many moves, decaying overshoots** — a `@keyframes` timeline that swings past the target
   and back, each swing smaller than the last, like a real spring ringing down. Richer,
   great for entrances and playful accents.

Learn to reach for the right one and your buttons stop *changing state* and start
*reacting*.

---

## 1. Bounce, method A — one transition on an "ease-out-back"

The fastest bounce is not a keyframe animation at all. It's a plain transition on a curve
whose **second control point sits above 1.0**, so the property flies past its target and
eases back down into it:

```css
.bounce-hover {
  /* the magic: y2 = 1.55 pushes the value PAST the endpoint, then it settles */
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
  transition: transform 0.4s var(--ease-out-back);
  will-change: transform;
}
.bounce-hover:hover,
.bounce-hover:focus-visible {
  transform: translateY(-6px) scale(1.06);   /* it overshoots, then settles into this */
}
```

**Why it bounces:** in `cubic-bezier(x1, y1, x2, y2)`, `y` is *progress toward the final
value*. A `y` greater than 1 means "more than 100% of the way there" — i.e. past the
target — mid-animation. Here `y1 = 1.56` launches it past, `y2 = 1` brings it home. One
line, physical feel. (This is the "back" easing family from Module 08; the bigger `y1`, the
harder the overshoot.)

Use method A when the motion is **a single move that reverses cleanly** (hover in / hover
out, press / release). It's compositor-cheap and interruptible: yank the mouse away
mid-bounce and it gracefully animates back.

---

## 2. Bounce, method B — decaying overshoots in `@keyframes`

For a *settling* bounce — a ball dropping and coming to rest — one overshoot isn't enough.
You want several, each smaller than the last. That's a keyframe timeline:

```css
@keyframes settle {
  0%   { transform: translateY(-40%); }   /* start high */
  30%  { transform: translateY(0);    }   /* first impact */
  45%  { transform: translateY(-18%); }   /* bounce up (biggest) */
  60%  { transform: translateY(0);    }   /* impact 2 */
  75%  { transform: translateY(-7%);  }   /* smaller bounce */
  88%  { transform: translateY(0);    }   /* impact 3 */
  95%  { transform: translateY(-2%);  }   /* tiny hop */
  100% { transform: translateY(0);    }   /* rest */
}
.drop { animation: settle 1s cubic-bezier(0.22, 1, 0.36, 1) both; }
```

The **decay** — 40 → 18 → 7 → 2 — is what sells it. Real bounces lose energy each impact;
if every bounce were the same height it would read as a machine, not a ball. Roughly halving
(or better) each overshoot mimics that energy loss. Bias the impact frames close together
near the end so the button appears to "give up" and rest.

> **Rule of thumb:** method A for *interruptible state changes* (hover/press), method B for
> *fire-and-finish* moments (entrances, a success bounce). A running keyframe animation
> can't gracefully reverse the way a transition can.

---

## 3. Springs & elastic — overshoot *both* ways

A spring doesn't just overshoot once and stop — it oscillates: past the target, back past
the start, past the target again, ringing down. For buttons the most useful spring is an
**elastic pop-in**: an entrance that scales up from nothing, blows *past* full size, dips
under, and settles.

```css
@keyframes pop-in {
  0%   { transform: scale(0);   opacity: 0; }
  60%  { transform: scale(1.1);  opacity: 1; }   /* overshoot past 100% */
  80%  { transform: scale(0.95);            }   /* dip under */
  100% { transform: scale(1);               }   /* settle */
}
.pop {
  animation: pop-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  transform-origin: center;
}
```

`0 → 1.1 → 0.95 → 1` is the canonical elastic entrance — enough overshoot to feel bouncy,
enough dip to feel like it has weight, quick enough not to annoy. For a *stronger* spring,
add more oscillations (`1.15 → 0.9 → 1.03 → 1`); for a subtle one, shrink the overshoot to
`1.04`. Pair it with `opacity` so the element fades in as it grows — pure scale-from-0 can
look like it's punching out of the screen.

**`both`** (shorthand for `animation-fill-mode: both`) makes the button hold frame 0 before
it starts and frame 100% after it ends, so it never flashes at its un-animated size.

---

## 4. Springy press & release on `:active`

A tactile button acknowledges the *press* itself. Scale it **down** on `:active` (finger
pushes it into the page), then let it **spring back** on release using an overshoot curve so
it pops out past its resting size and settles — exactly like a physical key.

```css
.springy {
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
  /* release uses the springy curve (slower); press is quick and linear-ish */
  transition: transform 0.45s var(--ease-out-back);
  will-change: transform;
}
.springy:hover,
.springy:focus-visible { transform: scale(1.05); }
.springy:active {
  transform: scale(0.9);              /* pushed IN */
  transition: transform 0.08s ease;   /* press is FAST — no bounce going down */
}
```

The trick is the **asymmetric transition**: the `:active` rule overrides the transition to
be fast and un-bouncy (you don't want a spring *into* the press — that feels mushy), while
the base rule's slow ease-out-back governs the *release*, giving you the pop. Press is
instant and crisp; release is springy. That contrast is what feels "clicky."

---

## 5. "Juicy" tactile hover — transform + shadow + spring, together

"Juice" is what game designers call the layered feedback that makes an interaction feel
satisfying. For a button it's the **combination**: it rises (`translateY`), grows a touch
(`scale`), and casts a bigger, softer shadow — all on one springy curve so the whole thing
lifts as a single physical object.

```css
.juicy {
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.35);
  transition:
    transform  0.35s var(--ease-out-back),
    box-shadow 0.35s var(--ease-out-back);
  will-change: transform;
}
.juicy:hover,
.juicy:focus-visible {
  transform: translateY(-5px) scale(1.05);
  box-shadow: 0 14px 30px rgba(99, 102, 241, 0.5);   /* lift = bigger, softer shadow */
}
.juicy:active {
  transform: translateY(-1px) scale(1.01);
  box-shadow: 0 6px 14px rgba(99, 102, 241, 0.45);
  transition: transform 0.09s ease, box-shadow 0.09s ease;
}
```

**Why the growing shadow matters:** shadow size reads as *height off the page*. A button
that rises but keeps a flat shadow looks like a sticker sliding; grow the shadow as it lifts
and your eye reads real elevation. Transform and shadow are both compositor-friendly, so
this stays 60fps. This is the single highest-ROI button effect in the whole course — it's
three properties and it makes a button feel *expensive*.

---

## 6. Jelly / wobble — playful skew

For a friendly, informal button, make it **wobble** like jelly. The move is a rapid
`skew` oscillation (with a little scale) that decays to rest — a squash-and-stretch borrowed
straight from classic animation:

```css
@keyframes jelly {
  0%   { transform: scale(1, 1); }
  25%  { transform: scale(1.12, 0.88) skewX(-6deg); }   /* squash wide */
  40%  { transform: scale(0.92, 1.08) skewX(4deg);  }   /* stretch tall */
  55%  { transform: scale(1.04, 0.96) skewX(-2deg); }
  70%  { transform: scale(0.98, 1.02) skewX(1deg);  }
  85%  { transform: scale(1.01, 0.99);              }
  100% { transform: scale(1, 1);                    }
}
.jelly:hover,
.jelly:focus-visible { animation: jelly 0.6s ease both; }
```

The signature of jelly is that **width and height move oppositely** — as it squashes wide
(`scale x > 1, y < 1`) it must get shorter, preserving apparent volume. Adding a small
`skewX` that flips sign each keyframe gives the side-to-side "gummy" wobble. Keep it under
~0.6s or it stops reading as bouncy and starts reading as broken. Trigger it on hover for a
toy-like button, or reuse the same keyframes on click for a "boing" acknowledgment.

---

## 7. Staggered / sequential motion — choreograph the parts

A button is often an **icon + a label**. Animate them with *different delays* and you get
choreography instead of a single blob move. The tool is `animation-delay` (or a staggered
`transition-delay`) per child:

```css
.reveal { overflow: hidden; }             /* clip the parts as they slide in */
.reveal .icon,
.reveal .label { display: inline-block; }

@keyframes rise {
  from { opacity: 0; transform: translateY(120%); }
  to   { opacity: 1; transform: translateY(0);    }
}
.reveal .icon  { animation: rise 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
.reveal .label { animation: rise 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.12s both; }
/*                                            icon leads ↑ label follows 120ms later */
```

The `0.12s` head start on the label is the whole effect: the icon springs up, the label
chases it a beat later, and the eye reads a deliberate little performance. This scales — a
row of buttons can stagger by index (`:nth-child(2) { animation-delay: 0.1s }`,
`:nth-child(3) { 0.2s }`…) to cascade in. **Stagger is the cheapest way to look
expensive.** Keep total spread small (100–150ms between parts) so it feels tight, not slow.

---

## 8. Combining transform functions — and why **order matters**

Keyframes get their richness from stacking transforms: `translate` + `scale` + `rotate` in
one `transform`. Critical rule: **the browser applies them right-to-left, and each acts in
the coordinate space left by the previous one.** They do **not** commute.

```css
/* A: rotate happens in the ALREADY-TRANSLATED space → it orbits the origin */
transform: translateX(50px) rotate(45deg);

/* B: translate happens in the ALREADY-ROTATED space → it moves along the tilted axis */
transform: rotate(45deg) translateX(50px);
```

For button pops the reliable order is **translate → rotate → scale** (position first, then
spin, then size), which keeps the spin centered and the scale uniform:

```css
@keyframes tada {
  0%   { transform: scale(1) rotate(0); }
  15%  { transform: scale(0.95) rotate(-4deg); }   /* wind up: shrink + tilt back */
  35%  { transform: scale(1.1)  rotate(4deg);  }   /* pop: overshoot big, tilt forward */
  60%  { transform: scale(1.03) rotate(-2deg); }
  100% { transform: scale(1)    rotate(0);     }
}
.tada:hover,
.tada:focus-visible { animation: tada 0.6s ease both; }
```

Also set **`transform-origin`** deliberately — a pop from `center` feels balanced; a wobble
pinned to `bottom center` feels hinged, like it's standing on the page. If a combined
transform ever animates "wrong" (orbiting when you wanted a spin), reorder the functions
before you touch anything else.

---

## 9. Guard everything: `prefers-reduced-motion`

Bounces and springs are exactly the motion that triggers vestibular discomfort for some
users. **Every** effect in this module must degrade for people who ask for less motion.
Wrap the motion, keep the meaning:

```css
@media (prefers-reduced-motion: reduce) {
  .bounce-hover, .springy, .juicy, .tada {
    transition-duration: 0.01ms;   /* state still changes — instantly, no bounce */
  }
  .drop, .pop, .jelly, .reveal .icon, .reveal .label {
    animation: none;               /* skip the keyframe show entirely */
  }
  /* keep the *result*: an entrance must still end up visible, not stuck at scale(0) */
  .pop { opacity: 1; transform: none; }
  .reveal .icon, .reveal .label { opacity: 1; transform: none; }
}
```

Two non-negotiables: (1) never leave an entrance animation's element stranded at its `0%`
frame — if you kill `pop-in`, force `opacity:1; transform:none` so it's still *there*; and
(2) prefer *reducing* (near-instant transitions) over deleting hover feedback entirely — the
button should still confirm interaction, just without the springy overshoot. Feel is a
feature; accessibility is a requirement. You can have both.

---

## ✅ Check yourself

- [ ] What makes a `cubic-bezier` overshoot — which number, and why past 1.0?
- [ ] When do you reach for a single ease-out-back transition vs. a decaying-overshoot
      `@keyframes`?
- [ ] Why must a settling bounce's overshoots *decay* instead of staying equal?
- [ ] In a springy press, why is the `:active` (press-down) transition fast while the
      release is slow and bouncy?
- [ ] Why does a *growing* shadow sell a lifting hover better than a static one?
- [ ] `translateX(50px) rotate(45deg)` vs. `rotate(45deg) translateX(50px)` — why aren't
      they the same?
- [ ] What two things must your `prefers-reduced-motion` block guarantee for an *entrance*
      animation?

**Next:** [Module 11 — Layout & Flow →](../11-layout-and-flow/)
Then try the [challenge](./challenge.md).
