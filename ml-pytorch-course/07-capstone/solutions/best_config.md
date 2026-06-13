# Strong reference config

A config that reliably reaches **> 0.92 test accuracy** on FashionMNIST in ~20 epochs
(a few minutes on a modern CPU, faster on GPU):

```bash
python 07-capstone/code/train.py \
    --run aug_do_wd_cos \
    --epochs 20 \
    --augment \
    --dropout 0.3 \
    --weight-decay 1e-4 \
    --scheduler cosine \
    --width 32 \
    --patience 6

python 07-capstone/code/evaluate.py \
    --checkpoint checkpoints/aug_do_wd_cos.pt \
    --run eval_best
```

## Why these choices

- `--augment` (random crop + horizontal flip) — the biggest single gain; cheap extra data.
- `--dropout 0.3` + `--weight-decay 1e-4` — modest regularization; improves val loss and
  calibration more than raw accuracy.
- `--scheduler cosine` — smooth lr decay for a clean final descent.
- **BatchNorm on** (default) — stable, fast training; keeps gradients well-scaled.
- `--width 32` — ~459k params; a good CPU-friendly capacity. `--width 64` squeezes out a
  little more if you have the compute.

## Ablations worth running (one change each)

| Flag change | Expected effect |
|-------------|-----------------|
| drop `--augment` | val/train gap widens; ~0.5–1% lower test acc |
| `--no-batchnorm` | slower early training; smaller first-layer gradients |
| `--dropout 0.5` | slight underfit; val acc dips a touch |
| `--scheduler none` | slightly higher final val loss; no clean end-of-training descent |
| `--width 64` | a bit higher acc, ~4× params, slower |

Compare them by overlaying `acc/val` in TensorBoard and sorting the **HPARAMS** table.
