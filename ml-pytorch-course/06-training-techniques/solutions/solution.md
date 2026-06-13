# Solution 06 — notes

Run: `python 06-training-techniques/solutions/challenge_solution.py` then
`tensorboard --logdir runs`.

## Key points

- **One `train(config)` to rule them all.** Every experiment goes through a single function
  that takes a config dict and returns `(best_state, best_val_acc, best_val_loss, best_epoch)`.
  This is the single most valuable habit in this course: never copy-paste training loops —
  parameterize one and name each run for its config so TensorBoard comparisons are clean.

- **Early stopping = patience + best-state restore.** Track the best val loss; if it doesn't
  improve for `patience` epochs, stop. Crucially, snapshot `copy.deepcopy(model.state_dict())`
  at each new best and **return that**, not the final weights — the final epoch is usually
  worse than the best. In the sample run you can see lines like
  `early stop at epoch 20 (best was epoch 14)`: training continued 6 epochs past the optimum
  before giving up, and the *best* weights were kept.

- **Generalization verdict (Task 2).** On a 4k-sample subset the three configs land close
  together (all ≈ 0.83–0.84 val acc); the regularized/scheduled runs reach their best
  **earlier** and with **lower val loss**, i.e. they're better-behaved even when top-line
  accuracy is similar. Differences grow with a smaller training set or a bigger model —
  regularization matters most exactly when you're prone to overfit.

- **HParams grid (Task 4).** Sorting the HPARAMS table by `val_acc`, the best cell is
  typically `weight_decay=1e-3, dropout=0.3` (≈ 0.84). The grid makes the trend legible:
  some regularization helps; too much (or none) is slightly worse.

- **Save / reload (Task 5).** `torch.save(state_dict)` → fresh model → `load_state_dict` →
  identical val accuracy (the assert checks bit-for-bit agreement). Always save the
  `state_dict` (parameters), not the whole model object, and call `model.eval()` before
  inference so dropout/batchnorm behave.

## Reading it in TensorBoard
- **SCALARS:** overlay `acc/val` and `loss/val` across `chal06_a/b/c`; inspect `lr` to see
  the cosine decay on the scheduled run; eyeball where each `loss/val` bottoms out (the
  early-stop point).
- **HPARAMS:** sort/scatter the `grid_*` runs to pick the winning `weight_decay`/`dropout`.
