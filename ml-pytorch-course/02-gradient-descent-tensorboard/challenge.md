# Challenge 02 — Descend & Visualize

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Your own surface.** Define a different 2-parameter loss — e.g. the Rosenbrock-ish
   `L(w) = (1 - w1)**2 + 10*(w2 - w1**2)**2` (a curved valley). Run gradient descent on it
   from `(-1.5, 2.0)`, logging `loss`, `param/w1`, `param/w2`, and `grad/norm`, plus a
   `descent/path` figure (contour + trajectory). Find a learning rate that converges
   without diverging (this surface punishes large steps).

2. **lr is everything.** For your surface, run three learning rates (one too small, one
   good, one too large) as separate runs. In TensorBoard, overlay their `loss` curves and
   write one sentence describing each behavior.

3. **Gradient-norm story.** Add a chart of `grad/norm` over steps for the good run. Explain
   what its shape tells you about *where* on the surface the optimizer is (steep early,
   flattening near the minimum).

4. **Optimizer showdown.** Run SGD, SGD+momentum, and Adam on your surface (reuse the
   pattern from `optimizer_compare.py`). Report final loss and step count to reach
   `loss < 0.1` for each. Which wins on a curved valley, and why?

5. **Stretch — manual vs optimizer.** Implement the *same* step two ways for one run:
   (a) by hand with `w -= lr * w.grad` under `no_grad`, and (b) with `torch.optim.SGD`.
   Confirm the parameter trajectories are identical (they should be — `optim.SGD` *is*
   that update).

## Success criteria
- [ ] A `descent/path` figure for your own loss surface shows a sensible trajectory to the
      minimum.
- [ ] Three lr runs overlaid, each behavior described in one sentence.
- [ ] You can read the `grad/norm` curve as a proxy for steepness/closeness to the minimum.
- [ ] Optimizer comparison with final loss + steps-to-threshold for SGD/momentum/Adam.
- [ ] (Stretch) Hand-update and `optim.SGD` produce identical paths.
