# Lab 06 — Overfitting, Regularization, Schedules & HParams

**You'll:** produce the classic overfitting chart and fix it, ride three LR schedules, and run
a hyperparameter sweep you compare in the HPARAMS tab. ⏱️ ~70 min.

> Reuses FashionMNIST from Module 05 (already in `data/`). All runs are short.

---

## Part A — Make a model overfit (on purpose)

```bash
python 06-training-techniques/code/overfit_demo.py
tensorboard --logdir runs
```
Console: the **plain** model reaches `train_acc ≈ 1.000` / `train_loss ≈ 0` while
`val_loss` balloons (~1.4). The **regularized** model keeps `val_loss` far lower (~0.85).
✅ Open **SCALARS**, select `overfit_plain`, overlay `loss/train` and `loss/val`. You'll see
the signature: train dives to ~0, val bottoms out then **rises**. That rise is overfitting.

## Part B — Close the gap

Now add `overfit_regularized` to the chart.
✅ Its `loss/val` stays low and flat — dropout + weight decay stop the memorization. Check
`gap/val_minus_train_loss`: large and growing for plain, small for regularized. (Val
*accuracy* is similar here; on this tiny set regularization mainly fixes val **loss** /
overconfidence — a real and important distinction.)

## Part C — Where would you early-stop?

On the `overfit_plain` `loss/val` curve, find the **minimum** (the epoch before it turns
up). That's where early stopping would snapshot the best model.
✅ You can point to the early-stop epoch and explain why training past it hurts.

## Part D — Learning-rate schedules

```bash
python 06-training-techniques/code/lr_schedule.py
```
✅ Overlay `lr` for `sched_constant/step/cosine`: a flat line, a **staircase**, and a smooth
cosine. Now overlay `loss/val`: the step schedule takes a fresh **notch down** right after
each lr drop. Scheduling usually beats a constant lr (lower final val loss here).

## Part E — Hyperparameter sweep → the HPARAMS tab 🎛️

```bash
python 06-training-techniques/code/hparam_search.py
```
This trains 9 configs (3 lrs × 3 dropouts).
✅ Open the **HPARAMS** tab:
- **Table:** click the `hparam/val_acc` header to sort — the best config rises to the top
  (≈ lr `1e-3`, dropout `0.3`).
- **Parallel coordinates:** drag to see that the mid lr dominates; extreme lrs underperform.
- **Scatter:** plot `lr` vs `val_acc` — the inverted-U sweet spot, visualized.

## Part F — Reflect (3 sentences)

1. What two things must be true of the loss curves to call it overfitting (not underfitting)?
2. Why is val *loss* a more sensitive overfitting signal than val *accuracy*?
3. Why does dropping the learning rate late in training help?

---

✅ **Done when:** you've produced the train↓/val↑ overfitting chart, flattened it with
regularization, and found the best config in the HPARAMS tab.

**Next →** [challenge.md](./challenge.md) then [Module 07: Capstone](../07-capstone/)
