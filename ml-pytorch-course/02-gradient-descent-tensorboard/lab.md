# Lab 02 — Watch Gradient Descent in TensorBoard

**You'll:** run descent with full logging, sweep the learning rate, and compare optimizer
trajectories on a loss surface — all in TensorBoard. ⏱️ ~70 min.

Keep one terminal running `tensorboard --logdir runs` the whole time and refresh the
browser as new runs appear.

---

## Part A — One parameter, three signals

```bash
python 02-gradient-descent-tensorboard/code/gd_1d.py --lr 0.1
tensorboard --logdir runs
```
Open <http://localhost:6006> → **SCALARS**.
✅ Three curves tell the whole story: `loss` → 0, `param/w` → 3, `grad/w` → 0. When the
gradient flattens to ≈ 0, you've **converged**.

Now feel the learning rate:
```bash
python 02-gradient-descent-tensorboard/code/gd_1d.py --lr 0.01    # crawls
python 02-gradient-descent-tensorboard/code/gd_1d.py --lr 0.9     # oscillates
python 02-gradient-descent-tensorboard/code/gd_1d.py --lr 1.05    # DIVERGES
```
✅ In TensorBoard each `lr` is its own run (toggle them in the left panel). Overlay the
`loss` curves: 0.01 barely moves, 0.9 zig-zags down, 1.05 shoots to infinity.

## Part B — A learning-rate sweep in one shot

```bash
python 02-gradient-descent-tensorboard/code/lr_sweep.py
```
✅ The console prints a behavior table. In TensorBoard, select the `sweep_lr*` runs and
overlay `loss` — a single chart showing the speed/stability trade-off. **There's a sweet
spot**: fast enough to descend quickly, small enough not to diverge.

## Part C — The descent path on a loss surface 🗺️

```bash
python 02-gradient-descent-tensorboard/code/gd_surface.py --lr 0.08
```
In TensorBoard open the **IMAGES** tab → `descent/path`. Drag the **step slider**.
✅ You watch the red path roll from the blue start into the gold minimum. Because the bowl
is **ill-conditioned** (steep in `w1`, shallow in `w2`), plain GD **zig-zags** across the
narrow axis while crawling down the long one — see it bounce side to side.

Try a tiny step (smooth but slow) and a too-big step (diverges):
```bash
python 02-gradient-descent-tensorboard/code/gd_surface.py --lr 0.03    # smooth, slow crawl
python 02-gradient-descent-tensorboard/code/gd_surface.py --lr 0.11    # diverges, path flies off
```
✅ Compare the three `surface_lr*` runs' paths and `grad/norm` curves: the zig-zag at 0.09,
the timid crawl at 0.03, and the blow-up at 0.11.

## Part D — SGD vs Momentum vs Adam

```bash
python 02-gradient-descent-tensorboard/code/optimizer_compare.py
```
✅ **SCALARS:** overlay the three `loss` curves — momentum and Adam reach the bottom in far
fewer steps. **IMAGES:** scrub each `descent/path`:
- `optim_sgd` — zig-zags down the valley.
- `optim_momentum` — the zig-zag is damped; it powers along the valley floor.
- `optim_adam` — adapts its step per parameter; a different, often quicker route.

This is *why* nobody hand-tunes plain SGD when momentum/Adam exist.

## Part E — Reflect (write 3 sentences)

1. What does the gradient's **magnitude** do as you approach the minimum, and why?
2. What single symptom in the `loss` curve says "lr too high"?
3. On the elongated bowl, why does momentum beat plain SGD?

---

✅ **Done when:** you've scrubbed a descent path in the IMAGES tab and can point to the
sweet-spot learning rate in your sweep.

**Next →** [challenge.md](./challenge.md) then [Module 03](../03-linear-regression/)
