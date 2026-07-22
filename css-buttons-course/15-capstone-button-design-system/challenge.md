# Challenge 15 — Extend the design system

**Task:** you have a working button library ([`solutions/buttons.css`](./solutions/buttons.css)).
Now make it yours. You'll add a new variant, a new size, an icon-only round variant, and
re-theme the whole thing to a brand color — **by changing tokens and adding modifiers only,
never by rewriting the base `.btn`.** That constraint *is* the test: a good system extends
without surgery.

Start from a copy of `buttons.css` and a small HTML page that links or inlines it.

## Requirements

1. **New variant — `.btn--warning`.** Add a fourth semantic color role. Introduce
   `--btn-warning` / `--btn-warning-hover` / `--btn-warning-active` / `--btn-on-warning`
   tokens in `:root`, give them dark-mode values too, then write a `.btn--warning` block
   that mirrors `.btn--danger` — reading only from the new tokens. Pick a readable amber and
   check the label contrast against it (Module 02).
2. **New size — `.btn--xl`.** Add an extra-large size. Change **only** `--btn-font` (and,
   if you like, `--btn-min-hit` and the radius). Prove the em trick: no padding value should
   appear in the rule.
3. **Icon-only round variant.** Build a circular, icon-only button using
   `class="btn btn--primary btn--circle"` with a single inline-SVG or emoji glyph. It **must**
   carry an `aria-label` (there's no visible text to announce). Confirm it stays a perfect
   circle at `.btn--sm` and `.btn--lg`.
4. **Re-theme to your brand.** Change **only the token block** so `--btn-primary` (and its
   hover/active/on- and accent-ink tokens) become *your* brand color. Do not touch any rule
   below `:root`. Every primary, ghost, link, focus ring, and pill should re-color together.
5. **Prove both themes.** Show your buttons once in the default theme and once inside a
   `[data-theme="dark"]` wrapper, side by side, with no JavaScript.

## Acceptance checklist

- [ ] `.btn--warning` reads **only** from new `--btn-warning*` tokens — no raw hex in the rule.
- [ ] `.btn--xl` contains **no** padding value; it changed `--btn-font` and nothing structural.
- [ ] The round icon button has an `aria-label` and is a true circle at `--sm` and `--lg`.
- [ ] Re-theming touched **only** the `:root` token block; the base `.btn` is byte-for-byte
      unchanged.
- [ ] Keyboard-tabbing shows a focus ring on every new button; mouse-clicking does not.
- [ ] Both theme panels render correctly with zero JS, and respect reduced motion.

## Stretch goals

- **Loading spinner state.** Wire up your new variants to the `[aria-busy="true"]` loading
  state and verify the spinner is visible against each fill (dark arc on light variants,
  light arc on dark ones — Module 09). Confirm the button **keeps its width** while busy
  (no reflow) and that the spin stops under `prefers-reduced-motion: reduce`.
- **Gradient primary.** Give `.btn--primary` a token-driven gradient background
  (`--btn-primary-grad`) without breaking the flat variants (Module 04 / 12).
- **Split the tokens into a theme file.** Move the `:root` block into its own `tokens.css`
  so a teammate can drop in a whole new brand by swapping one file.

When you can add a variant, a size, and a brand in minutes without touching the base, you
have internalized what a design system *is*. Reference build:
[`solutions/index.html`](./solutions/index.html) — try first!
