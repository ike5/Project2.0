# Module 02 — Gradient Descent, Visualized

**Goal:** understand gradient descent deeply by *watching* it — log loss, parameters, and
gradients to **TensorBoard**, and draw the **descent path crawling across a loss surface**.
This is the module that makes "the model learns" stop being magic. ⏱️ ~3 h · 🎯 Prereq: 01.

---

## 1. The idea in one picture

Every model has a **loss surface**: a landscape where the height is the loss and the
horizontal axes are the parameters. Training = a ball rolling downhill. At each step:

```
gradient  = slope of the loss at where we stand   (points UPHILL)
new_params = params - learning_rate * gradient    (step DOWNHILL)
```

```
   loss
    │      ╲                       ╱     each step: stand on the surface,
    │       ╲      • ← start      ╱      measure the slope (gradient),
    │        ╲    •  •           ╱       step downhill by lr × slope.
    │         ╲  •     •  •     ╱
    │          ╲•          •••╱   ← convergence (flat, gradient ≈ 0)
    └───────────────────────────── param
```

Too-small `lr` → the ball barely moves (slow). Too-big `lr` → it leaps past the valley and
**diverges**. You'll *see* both in TensorBoard.

## 2. The algorithm, concretely

For a one-parameter quadratic `L(w) = (w − 3)²`:

```python
import torch
w = torch.tensor(-8.0, requires_grad=True)
lr = 0.1
for step in range(60):
    loss = (w - 3) ** 2
    loss.backward()                 # w.grad = 2*(w-3)
    with torch.no_grad():
        w -= lr * w.grad            # the step
    w.grad.zero_()
```

That's it. Linear regression, neural nets, transformers — all the same loop, just with more
parameters and a fancier `loss`.

## 3. Wiring in TensorBoard

A `SummaryWriter` writes event files; TensorBoard draws them live. The four things worth
logging during descent:

```python
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter("runs/gd_lr0.1")

writer.add_scalar("loss", loss.item(), step)          # is it going down?
writer.add_scalar("param/w", w.item(), step)          # where is the ball?
writer.add_scalar("grad/w", w.grad.item(), step)      # how steep, which way?
writer.add_scalar("lr", lr, step)                     # (constant here; varies later)
```

Launch:

```bash
tensorboard --logdir runs        # http://localhost:6006 -> SCALARS
```

You'll watch **loss** sink toward 0, **param/w** glide to 3, and **grad/w** shrink to ≈ 0 as
the slope flattens. That triad *is* convergence.

## 4. The money shot: the descent path on a contour map

For a **two-parameter** loss we can draw the landscape as a contour map and plot the path
the optimizer takes across it. We render it with matplotlib and log the figure:

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.contour(W1, W2, Z, levels=30)            # the loss surface, top-down
ax.plot(path_w1, path_w2, "o-", color="red")  # every (w1, w2) the optimizer visited
ax.scatter([w1_star], [w2_star], marker="*") # the true minimum
writer.add_figure("descent/path", fig, step)
plt.close(fig)
```

Now the **IMAGES** tab shows the trajectory, and a step slider lets you *scrub the ball
rolling into the valley*. On an **ill-conditioned** bowl (steep one way, shallow the other)
plain GD **zig-zags**: it bounces across the narrow axis while crawling down the long one.
Crank the lr too high and the path flies off the surface (diverges); set it tiny and the
descent barely moves. That zig-zag is exactly the pain momentum and Adam were invented to
fix — which the next script shows.

## 5. Beyond vanilla GD: variants you'll meet

Same loop, smarter step rule. You don't have to implement these — `torch.optim` has them —
but seeing their paths side by side is illuminating:

- **SGD** — plain gradient descent (on mini-batches, later).
- **Momentum** — accumulates a velocity so it powers through shallow spots and damps
  zig-zag. Path looks like a heavier ball.
- **Adam** — adapts a per-parameter step size; often fast and forgiving of lr choice.

The lab logs SGD vs Momentum vs Adam on the *same* surface so you can compare trajectories
in one TensorBoard.

## 6. Reading the gradient signal

The **gradient** is the whole game, so learn to read it:

- **Sign** tells you direction: positive grad → decrease the param; negative → increase it.
- **Magnitude** tells you steepness: big early, shrinking near the minimum.
- A gradient stuck near **0** far from a good loss = a flat region / saddle (problem).
- A gradient **blowing up** = lr too high or an unstable loss (you'll see the curve explode).

In TensorBoard, plot `grad/*` right under `loss` — when the gradient hits ≈ 0 and stays
there, you've converged.

---

## Do the lab
Run vanilla GD with full logging, sweep the learning rate, and watch SGD vs Momentum vs
Adam descend the same surface. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/gd_1d.py`](./code/gd_1d.py) — 1-parameter descent; logs loss/param/grad scalars
- [`code/lr_sweep.py`](./code/lr_sweep.py) — same problem at several learning rates (compare runs)
- [`code/gd_surface.py`](./code/gd_surface.py) — 2-parameter descent; logs the **contour + path** figure
- [`code/optimizer_compare.py`](./code/optimizer_compare.py) — SGD vs Momentum vs Adam on one surface

## Key terms
loss surface · gradient descent · learning rate · step / update · convergence ·
divergence / oscillation · contour map · descent path · momentum · Adam ·
`add_scalar` · `add_figure` · global step

**Next →** [Module 03: Linear Regression](../03-linear-regression/)
