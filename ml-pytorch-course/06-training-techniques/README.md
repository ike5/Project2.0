# Module 06 — Training Techniques: Overfitting, Regularization, Schedules, HParams

**Goal:** make training *good*, not just working. Diagnose **overfitting** in TensorBoard,
fight it with **regularization**, shape learning with **LR schedules**, and find good configs
with the **HParams** dashboard. ⏱️ ~3 h · 🎯 Prereq: 05.

---

## 1. The central tension: fit vs generalize

You don't care about training accuracy — you care about performance on **unseen** data.
Two failure modes:

- **Underfitting** — model too weak / undertrained. *Both* train and val loss stay high.
  Fix: more capacity, more epochs, better features.
- **Overfitting** — model memorizes the training set. Train loss keeps dropping while
  **val loss turns around and rises**. Fix: regularization (below).

```
 loss                          the tell-tale overfitting signature:
   │\                          train keeps falling,
   │ \____ train               val bottoms out then climbs.
   │  \      \___              the gap = generalization error.
   │   \____      \__         ↑ best model is at the val minimum
   │   val  \____/   \___
   └──────────────────────── epochs
            ↑ early stop here
```

You'll produce exactly this chart and learn to read it.

## 2. Regularization: closing the gap

Techniques that trade a little training fit for better generalization:

- **Weight decay (L2)** — penalizes large weights; in PyTorch it's a one-liner:
  `optim.Adam(params, lr=1e-3, weight_decay=1e-4)`.
- **Dropout** — `nn.Dropout(p)` randomly zeros activations during training, forcing
  redundancy. Active in `model.train()`, off in `model.eval()` (another reason the
  train/eval switch matters).
- **Early stopping** — stop at the val-loss minimum; keep the best checkpoint.
- **Data augmentation** — expand the effective dataset with label-preserving transforms
  (Module 05's flips/crops). More data is the best regularizer.
- **Smaller model** — sometimes the right answer is less capacity.

## 3. Learning-rate schedules: anneal the step

A fixed lr is a compromise: big enough to move fast early, small enough to settle later. A
**schedule** gives you both by *decreasing* lr over training:

```python
import torch.optim as optim
opt = optim.SGD(model.parameters(), lr=0.1, momentum=0.9)
sched = optim.lr_scheduler.StepLR(opt, step_size=10, gamma=0.5)   # halve every 10 epochs
# or: optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)     # smooth decay to ~0

for epoch in range(epochs):
    train_one_epoch(...)
    sched.step()                              # advance the schedule (once per epoch)
    writer.add_scalar("lr", sched.get_last_lr()[0], epoch)
```

Log `lr` alongside `loss` and you'll *see* the loss take a fresh step down each time the lr
drops (the classic staircase). Common schedules: **step decay**, **cosine annealing**, and
**warmup** (ramp up first, then decay) for big models.

## 4. The HParams dashboard: search configs systematically 🎛️

Tuning by eyeballing one run at a time doesn't scale. `add_hparams` logs a run's **config**
and its **final metrics** together so TensorBoard's **HPARAMS** tab can compare them:

```python
writer.add_hparams(
    {"lr": lr, "dropout": p, "weight_decay": wd},        # the knobs
    {"hparam/val_acc": best_acc, "hparam/val_loss": best_loss},  # the results
)
```

Run a small grid (e.g. 3 lrs × 3 dropouts), then in the HPARAMS tab:
- **Table view** — sort runs by `val_acc`.
- **Parallel coordinates** — see which settings the good runs share.
- **Scatter** — plot `lr` vs `val_acc` to spot trends.

This is real hyperparameter search, visualized.

## 5. A reusable, well-instrumented training loop

The lab's loop brings it together: train/val loss + accuracy, current `lr`, early-stopping on
val loss with best-checkpoint saving, and an `add_hparams` summary at the end. It's the
template you'll copy into the capstone.

## 6. Mindset: change one thing at a time

When tuning, vary **one** knob per run and name the run for it (`runs/lr0.01_do0.3`). Overlay
in TensorBoard. If you change three things and val acc jumps, you won't know *which* helped.
Disciplined, logged experiments are the whole job.

---

## Do the lab
Induce overfitting and watch the gap, then knock it down with weight decay + dropout; ride an
LR schedule; and run a small HParams sweep. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/overfit_demo.py`](./code/overfit_demo.py) — overfit a tiny dataset, then regularize
- [`code/lr_schedule.py`](./code/lr_schedule.py) — StepLR vs Cosine, logging lr + loss
- [`code/hparam_search.py`](./code/hparam_search.py) — a small grid logged to the HParams tab

## Key terms
overfitting/underfitting · generalization gap · weight decay (L2) · dropout · early stopping ·
data augmentation · LR schedule (step/cosine/warmup) · `lr_scheduler` · `add_hparams` ·
HPARAMS tab (table/parallel-coords/scatter) · best-checkpoint

**Next →** [Module 07: Capstone](../07-capstone/)
