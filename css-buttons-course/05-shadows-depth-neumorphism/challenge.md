# Challenge 05 — Depth: an elevation lift button + a neumorphic button

**Task:** in one `index.html`, build **two** buttons that show you own shadows —
(A) an **elevation hover-lift** button on a dark surface, and (B) a **neumorphic** button
(raised at rest, pressed on `:active`) on a matching light panel. No peeking at the solution
until you've tried.

## Requirements

### A — Elevation hover-lift button (dark background)

1. Define an **elevation scale** of at least three custom properties (`--e1`, `--e3`, `--e5`
   or similar), each a **layered** shadow (a tight contact shadow **plus** a soft ambient
   one — comma-separated).
2. At rest, give the button a **low** elevation token.
3. On `:hover`, **raise** it: move it up with `transform: translateY(-Npx)` **and** swap to a
   **higher** elevation token.
4. On `:active`, make it **press in** — reduce or remove the outer shadow and nudge it back
   down.
5. Add a `:focus-visible` ring. Do **not** leave a bare `outline: none`.

### B — Neumorphic button (matching light panel)

6. Create a panel with a **light, non-white** background (e.g. `#e0e5ec`) and give the button
   the **exact same** background color.
7. Raised state: **two** shadows — one **light** offset up-left (`-x -y`) and one **dark**
   offset down-right (`+x +y`).
8. `:active` (pressed) state: the **same two shadows moved `inset`**, so the button caves into
   the surface.
9. Keep the label readable (strong text color) and add a `:focus-visible` ring here too.

### Both

10. Wrap every transition/transform in `@media (prefers-reduced-motion: reduce)` so motion is
    reduced or removed for users who ask for it.

## Acceptance checklist

- [ ] The elevation button visibly **rises** on hover (moves up *and* casts a bigger shadow)
      and **presses in** on click.
- [ ] Its resting and hover shadows are each **two layers** (contact + ambient).
- [ ] The neumorphic button and its panel are the **same color** — it looks extruded from the
      surface, not sitting on top.
- [ ] Pressing the neumorphic button flips both shadows to `inset` and it looks **recessed**.
- [ ] Tabbing to either button shows a visible focus ring; clicking with the mouse does not
      strand keyboard users.
- [ ] With "reduce motion" enabled, neither button animates jarringly.

## Stretch goals

- Add a **glow** variant of the elevation button: a large blurred shadow whose color matches
  the fill, intensifying on hover — driven from a single custom property so fill and glow
  can't drift.
- Give the neumorphic button a **pill** or **circular** icon-only variant (equal padding,
  `border-radius: 50%`) that keeps the same dual-shadow trick.
- Rebuild the elevation lift so the raised shadow lives on a **`::after` pseudo-element** and
  you animate only its `opacity` — the compositor-friendly version from section 8.
- Add a clip-path shape (arrow/hexagon) and shadow it correctly with
  `filter: drop-shadow()`.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
