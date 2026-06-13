# Lab 05 — Train a CNN & See What It Sees

**You'll:** inspect the data, train a CNN on FashionMNIST, and use TensorBoard's image tools
— input grid, prediction grid, learned filters, and the embedding projector. ⏱️ ~70 min.

> First run downloads FashionMNIST (~30 MB) into `data/`. CPU is fine; ~1–2 min/epoch.

---

## Part A — Look before you train

```bash
python 05-cnn-images/code/inspect_data.py
tensorboard --logdir runs
```
✅ Console shows 6000 images per class (balanced). **IMAGES → samples:** one labeled example
per class. Always eyeball your data first.

## Part B — Train the CNN

```bash
python 05-cnn-images/code/cnn_fashion.py --epochs 5
```
✅ `acc/test` climbs to ~0.90 over 5 epochs. **SCALARS:** `loss/train` (logged every 50
steps) is jagged — that's mini-batch noise — while `loss/test` and `acc/test` (per epoch) are
smooth.

## Part C — Watch predictions get fixed 🖼️

**IMAGES → predictions**, drag the **step slider** across epochs.
✅ Titles are `pred (true)`, green when right, red when wrong. Early epochs have several red
tiles (often Shirt↔T-shirt↔Coat — genuinely similar); later epochs turn most green.

## Part D — Inspect the learned filters

**IMAGES → conv1_filters**.
✅ The 16 first-layer 3×3 filters start as noise and become simple **edge/gradient
detectors**. This is the network learning low-level visual features from scratch.

## Part E — The embedding projector ✨

Open the **PROJECTOR** tab (top dropdown if hidden). Pick **t-SNE** or **PCA**, color by
label.
✅ The 256 test images' 128-d penultimate features form **10 clusters** by class. Overlapping
clusters (e.g. Shirt/Coat/Pullover) are exactly the classes the model confuses — the same
story as the red prediction tiles.

## Part F — Model graph & shapes

**GRAPHS:** expand the `CNN` node.
✅ Trace `(N,1,28,28) → conv/pool → (N,32,7,7) → flatten → (N,1568) → linear → (N,10)`.
Convince yourself the `Linear(32*7*7, 128)` input size *must* be `32·7·7 = 1568`.

## Part G — Experiment

- `--epochs 10` — accuracy keeps inching up; does `loss/test` start to flatten or rise
  (early overfitting)?
- `--lr 1e-2` vs `--lr 1e-4` — too-high lr makes `loss/train` spiky/unstable; too-low
  crawls. The Module 02 lesson, on a real net.

---

✅ **Done when:** you've scrubbed the prediction grid and explored the projector, and can
name two classes the model confuses and point to them in *both* views.

**Next →** [challenge.md](./challenge.md) then [Module 06](../06-training-techniques/)
