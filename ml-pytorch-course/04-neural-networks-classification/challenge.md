# Challenge 04 — A Three-Class Spiral

Solutions in [`solutions/`](./solutions/). Try first.

## Background
A **3-class spiral** is a harder toy: three intertwined arms that demand a genuinely curved,
multi-region boundary. Generate it (code in the solution, or write your own): for each class
`c ∈ {0,1,2}`, points along a spiral arm with radius growing from 0→1 and angle offset by
`c·(2π/3)`, plus noise.

## Tasks

1. **Generate & split.** Build the 3-class spiral (~300 points/class), make an 80/20
   train/val split, standardize the 2 features.

2. **Build a classifier.** An MLP `2 → hidden → hidden → 3` with ReLU. The final layer has
   **3** outputs (one logit per class). Use `CrossEntropyLoss` (it handles >2 classes with
   no code change) and `Adam`.

3. **Train with full logging.** Log `loss/train`, `loss/val`, `acc/val`, and a
   **decision-boundary figure** (3 colored regions) each few epochs. Reach ≥ 0.95 val
   accuracy.

4. **Capacity sweep.** Train with `hidden ∈ {4, 16, 64}` as separate runs. Overlay
   `acc/val` and describe the underfit→fit progression. Which is the smallest hidden size
   that cleanly separates the spiral?

5. **Confusion check.** At the end, compute and print a 3×3 confusion matrix on the
   validation set (rows = true class, cols = predicted). Which two classes get confused
   most, and where on the spiral does that happen?

6. **Stretch — log a confusion-matrix figure** to TensorBoard with `add_figure` (imshow of
   the matrix with class labels).

## Success criteria
- [ ] 3-class spiral generated, standardized, split.
- [ ] MLP with 3 output logits + `CrossEntropyLoss` reaching ≥ 0.95 val accuracy.
- [ ] Decision-boundary figure shows three curved regions.
- [ ] Capacity sweep overlaid with a one-line underfit→fit description.
- [ ] A printed (and/or logged) confusion matrix.
