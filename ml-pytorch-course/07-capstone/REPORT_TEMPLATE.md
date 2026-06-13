# Capstone Experiment Report

> Fill this in from **your own** TensorBoard. Replace every _(…)_ with specifics — numbers,
> run names, and what a particular curve/image actually showed you. Vague claims ("it got
> better") score low; evidence ("val loss bottomed at epoch 12 in `aug_reg_cosine`, vs
> epoch 6 in `baseline`") scores high.

**Author:** _(you)_ · **Date:** _(date)_ · **Dataset:** FashionMNIST (or _(CIFAR-10)_)

---

## 1. Goal & setup

- Task: 10-class image classification on _(dataset)_.
- Compute: _(CPU / GPU)_ · framework: PyTorch + TensorBoard.
- Metric I optimized for: **val loss** (early-stopping signal); metric I report: **test
  accuracy**.

## 2. Experiments

One variable changed per run. (Add rows as needed.)

| Run name | Change from previous | Key flags | Best val acc | Best val loss | @epoch |
|----------|----------------------|-----------|--------------|---------------|--------|
| `baseline` | — | `--epochs 15` | _( )_ | _( )_ | _( )_ |
| _( )_ | _(+ augmentation)_ | `--augment` | _( )_ | _( )_ | _( )_ |
| _( )_ | _(+ dropout)_ | `--dropout 0.3` | _( )_ | _( )_ | _( )_ |
| _( )_ | _(+ weight decay)_ | `--weight-decay 1e-4` | _( )_ | _( )_ | _( )_ |
| _( )_ | _(+ cosine schedule)_ | `--scheduler cosine` | _( )_ | _( )_ | _( )_ |

## 3. What TensorBoard told me

- **Overfitting / gap (SCALARS):** _(describe the `loss/train` vs `loss/val` gap for the
  baseline vs your regularized run — where did val loss turn up, if at all?)_
- **LR schedule (SCALARS `lr` + `loss/val`):** _(did the loss step down after lr drops /
  cosine decay?)_
- **Gradients (HISTOGRAMS `grads/*`):** _(healthy, or any vanishing/exploding? which layer?)_
- **Predictions (IMAGES `predictions`):** _(which tiles stayed red the longest?)_
- **Embedding (PROJECTOR):** _(which class clusters overlapped?)_
- **HPARAMS:** _(which config won when you sorted by `hparam/val_acc`?)_

## 4. Final model

- **Config:** `lr=_( )_, weight_decay=_( )_, dropout=_( )_, width=_( )_, augment=_( )_,
  batchnorm=_( )_, scheduler=_( )_`, early-stopped at epoch _( )_.
- **Parameters:** _( )_.
- **Checkpoint:** `checkpoints/_( )_.pt`.

## 5. Evaluation (from `evaluate.py`)

- **Test accuracy:** **_( )_** (target > 0.91).
- **Weakest classes (per-class acc):** _(e.g. Shirt 0.70, T-shirt 0.81)_.
- **Most-confused pair:** _(true → pred, count)_.
- **Mistakes grid:** _(are the errors genuinely ambiguous? give an example.)_

## 6. Reflection

- **What helped most, and why:** _( )_
- **What didn't help (or hurt):** _( )_
- **Biggest error mode & a hypothesis to fix it:** _( )_
- **If I had a GPU / more time, I'd try:** _( )_

---

_Attach or screenshot: the overlaid `loss/val` chart, the confusion matrix, and the mistakes
grid._
