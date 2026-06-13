# Solution 05 — notes

Run (a few minutes on CPU): `python 05-cnn-images/solutions/challenge_solution.py --epochs 5`
then `tensorboard --logdir runs`.

## Key points

- **CNN > MLP, and why.** Under the same budget the CNN beats the MLP (typically ~0.89 vs
  ~0.87 in a few epochs, gap widening with training). The CNN wins because convolutions
  exploit **locality** (nearby pixels relate) and **parameter sharing** (the same edge
  detector is reused across the whole image), so it needs far fewer parameters to capture
  visual structure than a fully-connected layer that treats every pixel as independent.

- **Improving the CNN.** Three cheap, high-leverage upgrades:
  - **BatchNorm** after each conv — normalizes activations per batch, stabilizing and
    speeding training (you can often raise the lr).
  - **An extra conv block / wider channels** — more capacity for higher-level features.
  - **Dropout** before the classifier — randomly zeros activations during training to
    reduce overfitting (a Module 06 idea, applied here).
  Together these reach > 0.91 in ~5 epochs (~0.909 at 3 epochs in the sample run).

- **Mining mistakes.** The misclassified grid is mostly **genuinely ambiguous** clothing —
  the model's errors are reasonable, not random. The dominant confusion is **Shirt ↔
  T-shirt** (and Shirt ↔ Coat/Pullover): upper-body garments that look alike at 28×28
  grayscale. In the sample run, *true Shirt predicted T-shirt* was the single biggest
  off-diagonal cell (~155 cases).

- **Confusion matrix ↔ projector.** The bright off-diagonal cells (Shirt/T-shirt/Coat/
  Pullover) are exactly the **overlapping clusters** you saw in the embedding projector in
  the lab. Two different TensorBoard views, same truth: those classes share a region of
  feature space.

- **Augmentation (stretch).** `RandomCrop(28, padding=2)` usually helps a little (shift
  invariance). `RandomHorizontalFlip` helps symmetric items (bags, shirts) but can *hurt*
  classes where left/right matters less or where flips create unrealistic images — always
  apply augmentation to **train only**, never to test.

## Reading it in TensorBoard
Overlay `acc/test` across `chal05_mlp / cnn_basic / cnn_improved` for the model comparison;
open the `cnn_improved` run's `mistakes` and `confusion` figures for the error analysis.
