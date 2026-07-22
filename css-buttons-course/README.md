# The Art of the Button: CSS Button Design from Basics to Mastery 🔘

A hands-on course that turns you into a **button design expert** — from the box model to
Bézier-driven springs — using nothing but **HTML and CSS**. Every module ships a
self-contained `demo.html` you open in a browser and *see working*, plus a challenge and
a reference solution.

> **Who this is for:** You know a little CSS (selectors, a few properties) and want to
> get genuinely *great* at designing buttons — the styling, the shapes, the shadows, the
> motion, the polish. No build tools, no frameworks, no JavaScript required. Just a text
> editor and a browser.
>
> **What you'll be able to do by the end:** design production-quality buttons and a full
> button design system — pill buttons, gradient buttons, glassmorphic buttons, neumorphic
> buttons, buttons that bounce and spring on a custom Bézier curve, animated-gradient
> glow buttons — all accessible, performant, and responsive.

---

## The arc

```
  Foundations                 Surface & Depth              Motion                    Advanced
 ┌──────────────┐            ┌──────────────────┐        ┌───────────────────┐      ┌──────────────────┐
 │ anatomy, box │            │ gradients,       │        │ transitions,      │      │ flow, animated   │
 │ model, type, │ ────────▶  │ shadows, depth,  │ ─────▶ │ Bézier easing,    │ ───▶ │ gradients, glass,│
 │ color, shapes│            │ interactive      │        │ keyframes,        │      │ 3D, a11y & perf  │
 │              │            │ states           │        │ bounces & springs │      │                  │
 └──────────────┘            └──────────────────┘        └───────────────────┘      └──────────────────┘
                                                                                          ▼
                                                                             Capstone: ship a full
                                                                             button design system
```

---

## What makes it effective

- **Learn by seeing.** Every module = concise concepts + a live `demo.html` you open in a
  browser + an unguided challenge + a reference solution. You never wonder "what does this
  actually look like" — you look at it.
- **Copy-paste-able.** Every example is a complete, self-contained snippet. Steal them.
- **Depth where it matters.** Full modules on **Bézier curves & custom easing** and on
  **bounces, springs & advanced motion** — the stuff that separates amateur buttons from
  buttons that feel *alive*.
- **Correct, not just pretty.** Accessibility (`:focus-visible`, contrast, reduced motion,
  real hit targets) and performance (compositor-only animation, `will-change`) are woven
  in, then given their own module.
- **A capstone.** Assemble everything into a coherent, themeable **button design system**
  with variants, sizes, states, and dark mode — a real deliverable for your portfolio.

---

## Prerequisites

- A **text editor** and a **modern browser** (Chrome, Firefox, Safari, or Edge). That's it.
- Basic CSS: you can write a selector and set a property. If `.btn { color: red; }` makes
  sense, you're ready.
- **No** Node, npm, build step, or framework. Open the HTML files directly (`file://`).

---

## The learning path

### Phase 1 — Foundations
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 00 | [Setup & Anatomy of a Button](./00-setup-and-anatomy/) | Reset a `<button>`; understand its parts; build an accessible baseline | 45 min |
| 01 | [Box Model, Sizing & Spacing](./01-box-model-sizing-spacing/) | Padding vs. fixed size; hit targets; `box-sizing`; consistent spacing | 1 h |
| 02 | [Typography, Color & Contrast](./02-typography-color-contrast/) | Labels that read well; color systems; accessible contrast | 1 h |
| 03 | [Borders, Radius & Shapes](./03-borders-radius-shapes/) | Pills, circles, cut corners, and custom shapes with `clip-path` | 1.5 h |

### Phase 2 — Surface & Depth
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 04 | [Backgrounds & Gradients](./04-backgrounds-and-gradients/) | Linear, radial & conic gradients; multi-layer backgrounds | 1.5 h |
| 05 | [Shadows, Depth & Neumorphism](./05-shadows-depth-neumorphism/) | Layered `box-shadow`, elevation, inset, glow, neumorphic surfaces | 1.5 h |
| 06 | [States: Hover, Focus, Active & Disabled](./06-states-hover-focus-active/) | Every interactive state, done right — including `:focus-visible` | 1.5 h |

### Phase 3 — Motion
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 07 | [Transitions & Timing Functions](./07-transitions-and-timing/) | `transition`, properties, duration, delay, the built-in easings | 1.5 h |
| 08 | [Bézier Curves & Custom Easing](./08-bezier-curves-custom-easing/) | Read and author `cubic-bezier()`; design the *feel* of motion | 2 h |
| 09 | [Keyframe Animations](./09-keyframe-animations/) | `@keyframes`, pulse, shimmer, spin, loading & success states | 2 h |
| 10 | [Bounces, Springs & Advanced Motion](./10-bounces-springs-advanced-motion/) | Bouncy, elastic, spring-like motion; multi-step & staggered effects | 2 h |

### Phase 4 — Advanced
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 11 | [Layout & Flow](./11-layout-and-flow/) | Flexbox inside buttons: icons + labels, button groups, alignment | 1.5 h |
| 12 | [Animated Gradients, Glow & Gradient Borders](./12-animated-gradients-glow-borders/) | Moving gradients, glowing edges, true gradient borders | 1.5 h |
| 13 | [Modern Effects: Glass, 3D & Blend Modes](./13-modern-effects-glass-3d-blend/) | `backdrop-filter` glass, `mix-blend-mode`, masks, 3D transforms | 2 h |
| 14 | [Accessibility, Performance & Best Practices](./14-accessibility-performance/) | `prefers-reduced-motion`, compositor animation, contrast, do's & don'ts | 1.5 h |

### Capstone
| # | Module | You'll… | Est. |
|---|--------|---------|------|
| 15 | [Capstone: Build a Button Design System](./15-capstone-button-design-system/) | Combine everything into a themeable, tokenized button library with variants, sizes, states & dark mode | 3+ h |

**Total: a realistic ~28 hours.** Take it in phases — each phase stands on its own.

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts + annotated code. Read first.
├── demo.html      ← Open in a browser. Every technique, live. Study second.
├── challenge.md   ← An unguided build task. Do third.
└── solutions/     ← Reference answer (HTML/CSS). Peek only after trying.
```

Every `demo.html` is **fully self-contained** (HTML + CSS in one file) so you can
double-click it or drag it into a browser — no server, no build.

---

## Reference material (keep open)

- **[cheatsheets/property-reference.md](./cheatsheets/property-reference.md)** — the CSS properties you'll use daily, at a glance
- **[cheatsheets/easing-reference.md](./cheatsheets/easing-reference.md)** — every easing curve, when to use it, with `cubic-bezier()` values
- **[cheatsheets/gradients-reference.md](./cheatsheets/gradients-reference.md)** — gradient syntax recipes you can paste
- **[GLOSSARY.md](./GLOSSARY.md)** — every term in plain English
- **[playground/index.html](./playground/index.html)** — a live sandbox to remix any button you build

---

## Quick start

```bash
cd css-buttons-course/00-setup-and-anatomy
# read the concepts
cat README.md
# then SEE it — open the demo in your browser:
#   macOS:   open demo.html
#   Linux:   xdg-open demo.html
#   Windows: start demo.html
# or just drag demo.html onto a browser window.
```

Ready? **→ [Start with Module 00: Setup & Anatomy of a Button](./00-setup-and-anatomy/)**

---

## A note on philosophy

A great button is a tiny interface with an outsized job: it invites a click, confirms the
click happened, and communicates state — all in a few dozen pixels. That means a button is
where **visual design, motion design, and accessibility meet**. Master the button and
you've mastered a microcosm of the whole craft. Let's go. 🚀
