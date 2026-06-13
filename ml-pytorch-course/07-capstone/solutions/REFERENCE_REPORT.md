# Capstone Reference Report (example)

> A *worked example* of a strong report, so you can calibrate yours. Your numbers will
> differ with hardware, seeds, and epochs — what matters is the **structure** and that every
> claim cites TensorBoard evidence. **Write yours before reading this.**

**Author:** course reference · **Dataset:** FashionMNIST · **Compute:** CPU.

---

## 1. Goal & setup
10-class FashionMNIST classification with the capstone CNN (3 conv blocks, BatchNorm, a
128-d head). Optimized val loss for early stopping; report test accuracy via `evaluate.py`.

## 2. Experiments
One knob per run, ~15–20 epochs each:

| Run | Change | Key flags | Best val acc | Best val loss | @epoch |
|-----|--------|-----------|-------------:|--------------:|:------:|
| `baseline` | — | `--epochs 15` | 0.910 | 0.254 | 12 |
| `aug` | + augmentation | `--augment` | 0.915 | 0.236 | 17 |
| `aug_do` | + dropout 0.3 | `--augment --dropout 0.3` | 0.918 | 0.224 | 18 |
| `aug_do_wd` | + weight decay | `… --weight-decay 1e-4` | 0.919 | 0.221 | 19 |
| `aug_do_wd_cos` | + cosine LR | `… --scheduler cosine` | **0.923** | **0.214** | 19 |

(Representative numbers; exact values vary by run.)

## 3. What TensorBoard told me
- **Overfitting (SCALARS):** `baseline` showed `loss/train` pulling well below `loss/val`
  after ~epoch 10, with `loss/val` flattening then drifting up — mild overfitting.
  Augmentation alone closed most of the gap (train and val tracked far longer).
- **LR schedule:** with `--scheduler cosine`, `loss/val` made a final smooth descent in the
  last third of training as `lr` annealed toward 0 — the cosine run's best epoch was its
  last useful one before early stop.
- **Gradients (HISTOGRAMS):** `grads/*` stayed well-scaled across all conv layers (BatchNorm
  doing its job); no vanishing/exploding. Removing BatchNorm (`--no-batchnorm`) made early
  training noticeably slower and the first-layer gradients smaller.
- **Predictions (IMAGES):** the tiles that stayed red longest were Shirt/T-shirt/Coat —
  upper-body garments.
- **PROJECTOR:** Sneaker/Sandal/Ankle-boot formed tight, separate clusters; Shirt overlapped
  Coat and Pullover — exactly the confusion the matrix later confirmed.
- **HPARAMS:** sorting by `hparam/val_acc`, the augmented + dropout 0.3 + weight-decay +
  cosine config topped the table; dropout 0.5 slightly underperformed (mild underfit).

## 4. Final model
`lr=1e-3, weight_decay=1e-4, dropout=0.3, width=32, augment=True, batchnorm=True,
scheduler=cosine`, early-stopped around epoch 19. ~459k parameters. Checkpoint:
`checkpoints/aug_do_wd_cos.pt`.

## 5. Evaluation (`evaluate.py`)
- **Test accuracy ≈ 0.922.**
- **Weakest classes:** Shirt (~0.70) and T-shirt (~0.81) — everything else > 0.90.
- **Most-confused pair:** true **Shirt → predicted T-shirt** (and Shirt↔Coat close behind).
- **Mistakes grid:** the most-confident errors are genuinely ambiguous — plain shirts that
  look like tees, and coats that look like pullovers at 28×28 grayscale. These are hard for
  humans too.

## 6. Reflection
- **Helped most:** augmentation (best single jump) and BatchNorm (stable, fast training).
- **Helped a little:** dropout + weight decay (lower val loss / better calibration more than
  raw accuracy); cosine schedule for a clean final descent.
- **Biggest error mode:** the Shirt/T-shirt/Coat cluster. Hypotheses to fix: a slightly
  bigger model or higher input resolution, class-balanced loss weighting, or targeted
  augmentation; ultimately 28×28 grayscale caps how separable these are.
- **With a GPU / more time:** train longer with a wider model (`--width 64`), try CIFAR-10,
  and run an lr range test to set the lr principally.

---

**Takeaway:** disciplined, one-change-at-a-time experiments — each read off TensorBoard —
moved a 0.910 baseline to ~0.922, and the error analysis shows the remaining gap is mostly
irreducible class ambiguity rather than a training problem.
