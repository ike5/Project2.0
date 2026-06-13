# Module 07 — Capstone: Train, Instrument, Report

**Goal:** ship an end-to-end image classifier the right way — a clean, configurable training
pipeline; the full TensorBoard instrumentation you've learned; a saved best model; and a
short **experiment report** you write from your own TensorBoard. ⏱️ ~3+ h · 🎯 Prereq: 00–06.

This is the synthesis. No new concepts — you assemble everything: tensors, autograd,
gradient descent, a CNN, cross-entropy, regularization, LR scheduling, early stopping, and
the whole TensorBoard toolkit.

---

## The project

Train a CNN on **FashionMNIST** to the best test accuracy you can, then explain — with
TensorBoard evidence — *why* your final model works. The provided code is a real,
reusable scaffold; your job is to run experiments, tune, and report.

```
07-capstone/
├── code/
│   ├── data.py       ← loaders + train-time augmentation
│   ├── model.py      ← a configurable CNN (depth/width/dropout/batchnorm)
│   ├── train.py      ← the full pipeline: CLI, logging, scheduling, early stop, checkpoint
│   └── evaluate.py   ← load best.pt → test acc, confusion matrix, misclassified grid
├── REPORT_TEMPLATE.md  ← fill this in from YOUR TensorBoard
└── solutions/          ← a reference report + a strong baseline config
```

## What the scaffold already does

`train.py` is a production-shaped loop you can run as-is and then tune via flags:

```bash
# A solid baseline (a few minutes on CPU):
python 07-capstone/code/train.py --epochs 15 --run baseline

# Tune it — change ONE thing per run and name the run for it:
python 07-capstone/code/train.py --epochs 20 --augment --dropout 0.3 --weight-decay 1e-4 \
    --scheduler cosine --run aug_reg_cosine

tensorboard --logdir runs
```

It logs, every run: `loss/{train,val}`, `acc/{train,val}`, `lr`, per-layer weight & gradient
histograms, an input grid, a per-epoch prediction grid, the model graph, a final embedding
projector, and an `add_hparams` summary. It early-stops on val loss and saves the **best**
weights to `checkpoints/<run>.pt`.

`evaluate.py` loads a checkpoint and produces the final scorecard:

```bash
python 07-capstone/code/evaluate.py --checkpoint checkpoints/aug_reg_cosine.pt --run eval_best
```
→ test accuracy, a 10×10 confusion matrix figure, and a grid of the worst misclassifications.

## Your tasks

1. **Run the baseline** and read its TensorBoard. Note its test accuracy and where it starts
   to overfit (if it does).
2. **Run ≥ 4 tuning experiments**, changing one knob at a time (augmentation, dropout,
   weight decay, scheduler, width/depth, lr). Name each run.
3. **Use the HPARAMS tab** to pick your best config by val accuracy.
4. **Evaluate the best checkpoint** with `evaluate.py`; study the confusion matrix and the
   misclassified grid.
5. **Write the report** in [`REPORT_TEMPLATE.md`](./REPORT_TEMPLATE.md): your experiment
   table, the TensorBoard evidence (which curves/images told you what), your final config and
   test accuracy, the model's main error mode, and what you'd try next.

## Success criteria / rubric

- [ ] **Reproducible:** `train.py` runs from a clean `data/` and writes a checkpoint + logs.
- [ ] **Instrumented:** your TensorBoard has scalars, histograms, images (incl. predictions),
      a graph, an embedding, and HPARAMS — all populated.
- [ ] **Tuned with discipline:** ≥ 4 named runs, one variable changed each; comparisons
      overlaid in TensorBoard.
- [ ] **Generalizes:** best model uses early stopping / regularization sensibly; you can show
      the val-loss minimum you stopped at.
- [ ] **Evaluated:** `evaluate.py` output included — test accuracy + confusion matrix +
      mistakes.
- [ ] **Reported:** `REPORT_TEMPLATE.md` filled in with specific TensorBoard evidence (not
      vague claims). Target: **> 0.91 test accuracy** (strong: > 0.92).

## Stretch goals

- Swap in **CIFAR-10** (`datasets.CIFAR10`, 3×32×32) — change `in_channels=3` and the
  flatten size; everything else carries over. Much harder; a GPU helps.
- Add a **residual connection** or **BatchNorm** ablation and show its effect on the gradient
  histograms and convergence.
- Log a **learning-rate range test** (sweep lr up over a few hundred steps, plot loss vs lr)
  to pick the lr principially.

## Code
[`code/data.py`](./code/data.py) · [`code/model.py`](./code/model.py) ·
[`code/train.py`](./code/train.py) · [`code/evaluate.py`](./code/evaluate.py)

## Reference
[`solutions/`](./solutions/) — a reference report and a strong config. **Write your own
report first**, then compare.

---

🎓 **Finish this and you've trained, instrumented, tuned, evaluated, and explained a real
model** — the full loop of applied deep learning. Congratulations on completing the course!
