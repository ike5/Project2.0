# Challenge 11 — A segmented control and a split button

**Task:** from a blank HTML file, build **two** shared-edge components — a three-option
segmented control and a split button — with clean seams, rounded ends, and correct
accessibility on every icon-only part. No peeking at the solution until you've tried.

## Requirements

### Part A — Segmented control (pick one of three)

1. A flex row (`display: inline-flex`, **no gap**) of three `<button type="button">`
   options: **List**, **Board**, **Timeline**.
2. Kill each button's own `border-radius`, then **round only the outer corners** with
   `:first-child` (left) and `:last-child` (right).
3. Collapse the doubled shared border into a single seam with
   `margin-left: -1px` on `.btn + .btn`.
4. Mark the selected option with `aria-pressed="true"` and give it a distinct look; make the
   active segment sit **on top** (`position: relative; z-index: 1`) so its border wins.
5. Wrap the group in a container with `role="group"` and an `aria-label`.

### Part B — Split button

6. A two-segment `inline-flex` component: a wide **"Add item"** main action and a narrow
   **caret** segment.
7. Round only the *outer* corners — left end of the main, right end of the caret; inner
   corners stay square.
8. The caret is **icon-only**: it must have an `aria-label` (e.g. "More add options"), its
   icon must be `aria-hidden`, and it should carry `aria-haspopup="menu"`.
9. Add a hairline divider between the two segments using an **`inset box-shadow`** (not a
   border — a border would break the shared-edge width).

### Both

10. Reuse a single base `.btn` class for every button. Include `:focus-visible` on all
    interactive buttons and do **not** leave a bare `outline: none` anywhere.

## Acceptance checklist

- [ ] The segmented control reads as one pill: rounded ends, square middles, single seams.
- [ ] Exactly one segment shows the pressed state, and its border isn't clipped by its neighbor.
- [ ] The split button's inner corners are square and its outer corners are rounded.
- [ ] The caret announces a real name to a screen reader (aria-label), not "button."
- [ ] Every decorative icon is `aria-hidden`; the divider adds no extra width.
- [ ] Tabbing shows a focus ring on every button; mouse clicks don't strand focus.

## Stretch goals

- Add a fourth segment and confirm the corner and seam rules **still hold with no new CSS** —
  proof your `:first-child`/`:last-child`/`+` selectors are structural, not hard-coded.
- Give the segmented control an icon **before** each label using `gap`, keeping icons
  `flex: none` so they never shrink.
- Add a **count badge** to the split button's main action — an inline `.count` pill or a
  floating corner badge (remember `position: relative` on the anchor and an `aria-label` on
  the number).
- Make the whole split button **full-width** on narrow screens: let the main action
  `flex: 1 1 auto` and keep the caret `flex: none`.

Reference answer: [`solutions/index.html`](./solutions/index.html) — try first!
</content>
