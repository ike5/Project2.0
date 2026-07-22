# Module 05 — Shadows, Depth & Neumorphism

**Goal:** use `box-shadow` (and its cousin `drop-shadow()`) to give flat buttons a
believable sense of *depth* — soft elevation, a pressed-in feel, colored glow, and the
matte "soft UI" of neumorphism — while knowing exactly why each shadow reads the way it does.
⏱️ ~1.5 h · 🎯 Prereq: 04 (Backgrounds & Gradients).

> **Do this now:** open [`demo.html`](./demo.html) in your browser and keep it next to this
> README. Every shadow described below is on screen there, live.

---

## 1. `box-shadow` anatomy — the mental model

One shadow is up to five values, in this order:

```css
/*            offset-x  offset-y  blur  spread  color              */
box-shadow:    0px       4px      12px   0px    rgba(0,0,0,.35);
```

- **offset-x** — horizontal shift. Positive = right. This is the light coming from the *left*.
- **offset-y** — vertical shift. Positive = **down**. This is the light coming from *above*
  — the default assumption of almost every UI on earth, so real shadows fall downward.
- **blur** — how soft the edge is. `0` = a hard, crisp shadow; bigger = softer and more
  diffuse. Higher objects cast blurrier shadows.
- **spread** — grow (`+`) or shrink (`−`) the shadow *before* blurring. A small **negative**
  spread pulls the shadow in so it peeks out only at the bottom — the single most useful
  trick for realism.
- **color** — use `rgba()`/`hsla()` with **alpha**, never a solid gray. Shadows are absence
  of light, not paint; they must be semi-transparent so the background shows through.

```css
.card-btn {
  background: #4f46e5;
  color: #fff;
  padding: .7em 1.4em;
  border-radius: 10px;
  /* light from top: no x-shift, positive y, soft blur, slight negative spread */
  box-shadow: 0 6px 16px -4px rgba(0, 0, 0, .45);
}
```

**Mental model:** picture a light bulb above and slightly in front of the button. `offset-y`
places the shadow beneath it, `blur` says how high off the page it floats, `spread` and
`alpha` control how heavy it looks. Keep the light direction consistent across your whole
UI or the interface feels physically "wrong."

---

## 2. Layer multiple shadows for *realistic* softness

Real objects don't cast one shadow — they cast a **tight, dark contact shadow** right at the
base and a **large, soft ambient shadow** spreading out. `box-shadow` takes a
comma-separated list, painted first-on-top, so you can stack both:

```css
.elevated {
  box-shadow:
    0 1px 2px  rgba(0, 0, 0, .30),   /* contact: tight, close, defines the edge   */
    0 8px 24px rgba(0, 0, 0, .22);   /* ambient: big, soft, sells the "floating"   */
}
```

The single-shadow look is flat and cheap; the two-layer look is what every polished design
system (Material, iOS, Tailwind's `shadow-*`) actually ships. Rule of thumb: **one shadow
you can barely see + one you can, together.** You can stack three or four for extra realism —
each larger and lighter than the last.

---

## 3. An elevation scale as custom properties

Depth should be a **system**, not a guess per button. Define a Material-style ladder of
elevations once as custom properties, then apply a level by name. Notice how both the
offset/blur **and** the total darkness grow with each level — higher things are farther from
the surface *and* cast more light-blocking bulk:

```css
:root {
  --e1: 0 1px 2px rgba(0,0,0,.28), 0 1px 1px rgba(0,0,0,.22);
  --e2: 0 2px 4px rgba(0,0,0,.28), 0 3px 6px rgba(0,0,0,.20);
  --e3: 0 3px 6px rgba(0,0,0,.28), 0 6px 14px rgba(0,0,0,.22);
  --e4: 0 5px 10px rgba(0,0,0,.28), 0 12px 24px rgba(0,0,0,.22);
  --e5: 0 8px 16px rgba(0,0,0,.28), 0 20px 40px rgba(0,0,0,.24);
}

.btn.level-1 { box-shadow: var(--e1); }
.btn.level-2 { box-shadow: var(--e2); }
.btn.level-3 { box-shadow: var(--e3); }
.btn.level-4 { box-shadow: var(--e4); }
.btn.level-5 { box-shadow: var(--e5); }
```

Now "raise a button on hover" is just *swap one token for a higher one* — consistent across
the entire app, tunable in one place. This is exactly how you'll tokenize the capstone
design system in Module 15.

---

## 4. `inset` shadows and the pressed look

Prefix a shadow with `inset` and it's painted **inside** the box — light and dark now live on
the *interior* edges. This is how you carve a well, an input field, or a **pressed** button.
The trick for `:active`: on press, drop the outer elevation and add an inset shadow so the
button appears to *sink into the page*. Nudge it down a hair with `transform` to complete the
illusion:

```css
.push {
  background: #4f46e5;
  box-shadow: 0 4px 10px rgba(0,0,0,.4);   /* raised at rest */
  transition: box-shadow .12s ease, transform .12s ease;
}
.push:active {
  transform: translateY(2px);              /* physically move down */
  box-shadow:
    inset 0 3px 6px rgba(0,0,0,.55),        /* dark well from the top edge */
    0 1px 2px rgba(0,0,0,.3);               /* tiny remaining contact shadow */
}
```

The eye reads "it went down and light no longer reaches under it" as a genuine press. Pair it
with `:focus-visible` so keyboard users still get a ring.

---

## 5. Glow — a large, blurred, *colored* shadow

A glow is just a `box-shadow` whose color **matches the button** instead of being black, with
a big blur and no offset so it radiates evenly. Intensify it on hover for a button that
"charges up":

```css
.glow {
  --hue: #e11d48;                 /* one source of truth for fill + glow */
  background: var(--hue);
  color: #fff;
  box-shadow: 0 0 18px -2px var(--hue);          /* resting glow */
  transition: box-shadow .25s ease, transform .25s ease;
}
.glow:hover {
  box-shadow:
    0 0 8px  -1px var(--hue),                     /* tight inner core */
    0 0 30px  4px var(--hue);                     /* wide halo on hover */
  transform: translateY(-1px);
}
```

Two glow tips: (1) drive the fill and the glow from **one** custom property so they can never
drift out of sync; (2) glow reads best on a **dark background** — on white it just looks like
a fuzzy smudge, because there's no darkness for the light to push against.

---

## 6. Neumorphism (soft UI)

Neumorphism makes a control look **extruded from the surface itself** — as if the background
swelled up into a button. The whole illusion rests on one rule: **the button and its
background must be (nearly) the same color.** There's no fill contrast; shape comes *entirely*
from light and shadow.

You place **two** shadows in opposite corners:

- one **light** shadow up-and-left (`-x -y`) — where the imagined top-left light hits;
- one **dark** shadow down-and-right (`+x +y`) — the side turned away from the light.

```css
.neu-panel { background: #e0e5ec; }          /* button lives ON this exact color */

.neu {
  background: #e0e5ec;                        /* SAME as the panel — required */
  color: #4a5568;
  border: none;
  border-radius: 16px;
  padding: .9em 1.6em;
  box-shadow:
    -6px -6px 12px rgba(255, 255, 255, .9),    /* light: top-left highlight   */
     6px  6px 12px rgba(163, 177, 198, .6);    /* dark:  bottom-right shadow  */
  transition: box-shadow .15s ease;
}

/* Pressed = the same two shadows, moved INSIDE. The button caves in. */
.neu:active {
  box-shadow:
    inset -4px -4px  8px rgba(255, 255, 255, .9),
    inset  4px  4px  8px rgba(163, 177, 198, .6);
}
```

Why it must match: if the button were a different color, the eye would read a *separate object
sitting on top*, not a bump *in* the surface — and the effect collapses. Flipping both shadows
to `inset` for `:active` is the whole trick: raised becomes recessed, and it feels physically
pressable. (Caveat worth knowing: low fill-vs-text contrast makes neumorphism a known
accessibility hazard — use it deliberately, and keep label contrast strong. More in Module 14.)

---

## 7. `filter: drop-shadow()` vs `box-shadow`

They look similar but shadow **different things**:

- **`box-shadow`** traces the element's **border box** — the rectangle (rounded if you have
  radius). It does not know about transparency or odd shapes.
- **`filter: drop-shadow()`** traces the element's **actual painted, opaque pixels** — so it
  follows a `clip-path`, a transparent PNG, or an inline SVG's real silhouette.

```css
/* A hexagon/arrow button clipped to a non-rectangular shape */
.badge {
  clip-path: polygon(0 0, 85% 0, 100% 50%, 85% 100%, 0 100%);
  background: #0ea5e9;
  /* box-shadow here would draw a RECTANGLE behind the arrow — wrong.
     drop-shadow hugs the arrow's real outline — right. */
  filter: drop-shadow(0 6px 10px rgba(0, 0, 0, .5));
}
```

Rule: **rectangular/rounded button → `box-shadow`** (cheaper, supports `inset` and spread);
**clipped or transparent shape → `filter: drop-shadow()`**. Note `drop-shadow()` has *no*
`inset` and no `spread`, and stacks with other `filter`s on the same element.

---

## 8. A performance tease (full story in Module 14)

Animating `box-shadow` directly — e.g. transitioning a small shadow to a big one on hover —
forces the browser to **repaint** the shadow every frame, which can stutter on weaker devices.
The compositor-friendly trick is to paint the "raised" shadow on a **pseudo-element** and
animate only its **`opacity`** (opacity and transform are the two cheap, GPU-composited
properties):

```css
.lift { position: relative; box-shadow: var(--e1); }   /* resting shadow */
.lift::after {
  content: "";
  position: absolute; inset: 0; border-radius: inherit;
  box-shadow: var(--e4);           /* the big "lifted" shadow, pre-baked */
  opacity: 0;                      /* hidden until hover */
  transition: opacity .2s ease;
  pointer-events: none;
}
.lift:hover::after { opacity: 1; } /* cross-fade to the bigger shadow — cheaply */
```

You get the same visual lift, but you're animating `opacity` (cheap) instead of repainting a
shadow (costly). We'll unpack *why* — the render pipeline, `will-change`, compositor layers —
in Module 14.

---

## ✅ Check yourself

- [ ] Name all five `box-shadow` values in order. Which one, made slightly negative, adds the
      most realism?
- [ ] Why layer a tight shadow *and* a diffuse one instead of using a single shadow?
- [ ] What does `inset` change about where a shadow is painted, and how does that create a
      pressed look?
- [ ] Why must a neumorphic button share its background's exact color — what breaks if it
      doesn't?
- [ ] When do you reach for `filter: drop-shadow()` instead of `box-shadow`?
- [ ] Why is animating a pseudo-element's `opacity` cheaper than animating `box-shadow`?

**Next:** [Module 06 — States: Hover, Focus, Active & Disabled →](../06-states-hover-focus-active/)
Then try the [challenge](./challenge.md).
