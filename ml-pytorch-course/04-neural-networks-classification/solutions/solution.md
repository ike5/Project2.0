# Solution 04 — notes

Run: `python 04-neural-networks-classification/solutions/challenge_solution.py` then
`tensorboard --logdir runs`.

## Key points

- **Multi-class is free.** Going from 2 to 3 classes means only: final layer outputs
  `N_CLASSES` logits, and labels are `int64` in `{0,1,2}`. `CrossEntropyLoss` handles any
  number of classes with no other change — it softmaxes the logits and compares to the true
  class internally.

- **Standardize, then un-standardize for plotting.** We standardize the 2 features for
  training, but the decision-boundary figure is drawn in *original* coordinates, so the grid
  is transformed by the same `(x − mean)/std` before being fed to the model. Keeping that
  straight is a common source of "why is my boundary in the wrong place" bugs.

- **Capacity sweep (Task 4).** Expect a clear underfit→fit curve:
  - `hidden=4` (~0.46): far too weak — the arms blur into each other.
  - `hidden=16` (~0.91): mostly separates, ragged near the center.
  - `hidden=64` (~0.99): cleanly carves three spiral regions.
  The smallest size that *cleanly* separates this spiral is around 32–64; below that you see
  underfitting. (Push capacity + noise far enough and you'd start to overfit — Module 06.)

- **Confusion matrix (Task 5).** Errors cluster near the **spiral center**, where the three
  arms wind close together and the noise makes classes overlap — exactly where any model
  struggles. Off-diagonal entries tell you *which* classes are mistaken for which; here it's
  whichever arms are adjacent at small radius.

- **Reading it in TensorBoard.** Overlay `acc/val` across `spiral_h4/h16/h64` to see the
  capacity effect in one chart; scrub `boundary` (h64 run) to watch three curved regions
  emerge; and check the logged `confusion` figure for the error structure.
