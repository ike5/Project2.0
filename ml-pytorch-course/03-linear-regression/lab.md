# Lab 03 — Linear Regression & TensorBoard

**You'll:** train a real model with the standard loop and *watch the line fit*, then see why
feature scaling matters. ⏱️ ~60 min. Keep `tensorboard --logdir runs` running.

---

## Part A — Train the regressor

```bash
python 03-linear-regression/code/linreg.py
tensorboard --logdir runs
```
Console shows `w` and `b` marching toward the true `2.5` / `-1.0`.
✅ **SCALARS:** `loss/train` and `loss/val` fall together; `params/w` → 2.5, `params/b` → −1.

## Part B — Watch the line rotate into place 🎞️

In TensorBoard open **IMAGES** → `fit/line` and drag the **step slider**.
✅ The red model line starts wrong and swings onto the green "true" line as epochs pass —
gradient descent, made visible on real data.

## Part C — Inspect the model graph

Open the **GRAPHS** tab. Double-click the `LinReg` node to expand it.
✅ You see input → `Linear` → output. (Small now; invaluable when models get deep.)

## Part D — The training-loop ritual

Open [`code/linreg.py`](./code/linreg.py) and find the loop. Identify the three lines that
appear in *every* PyTorch training loop:
```python
opt.zero_grad()     # 1. clear old gradients
loss.backward()     # 2. compute new gradients
opt.step()          # 3. update parameters
```
✅ You can recite "zero, backward, step" and say what each does. Try **deleting**
`opt.zero_grad()` and re-running — watch training destabilize (gradients accumulate!), then
put it back.

## Part E — Feature scaling

```bash
python 03-linear-regression/code/feature_scaling.py
```
✅ Console: the **raw** run (lr `1e-8`) barely moves; the **standardized** run (lr `0.1`)
converges to a tiny loss. In TensorBoard overlay the two `loss` curves — the standardized
one plummets while the raw one crawls.

**Why:** raw `x` ≈ thousands makes the loss surface a narrow ravine (the ill-conditioning
from Module 02). Standardizing to mean 0 / std 1 turns it into a round bowl any reasonable
lr can descend.

## Part F — Experiment (pick one)

- Swap `optim.SGD` for `optim.Adam(model.parameters(), lr=0.1)` in `linreg.py`. Re-run and
  compare `loss/train` to the SGD run. Faster?
- Change `batch_size` to `8` then `256`. How does the `loss/train` curve's **noisiness**
  change? (Smaller batch = noisier gradient = jumpier curve.)
- Increase the data noise (the `* 1.5` in `make_data`) and watch the floor that `val` loss
  settles at rise — you can't beat the noise.

---

✅ **Done when:** you've scrubbed the `fit/line` animation and can explain why the
standardized features train so much faster.

**Next →** [challenge.md](./challenge.md) then [Module 04](../04-neural-networks-classification/)
