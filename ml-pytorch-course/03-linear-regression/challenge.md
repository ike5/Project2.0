# Challenge 03 — Multiple Linear Regression

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **More features.** Generate data with **3 input features**:
   `y = 1.5·x1 − 2·x2 + 0.5·x3 + 4 + noise`, with the three features on *different scales*
   (e.g. x1 ~ [0,1], x2 ~ [0,100], x3 ~ [−10,10]). Use `nn.Linear(3, 1)`.

2. **Standardize.** Standardize each feature column (mean 0, std 1) before training. Log to
   TensorBoard and confirm convergence with a normal lr (e.g. SGD `lr=0.05`). Then try
   training on the **unstandardized** features and show it's much worse at the same lr.

3. **Recover the weights.** After training on standardized features, report the learned
   weights. (They'll be in *standardized* space — bonus: convert them back to the original
   feature scale and compare to the true `[1.5, −2, 0.5]`.)

4. **Train/val split + early read.** Use an 80/20 split and log `loss/train` and
   `loss/val`. Confirm they track each other (no overfitting expected for a linear model on
   clean-ish data).

5. **Optimizer & lr study.** Run the same setup with `SGD(lr=0.05)`, `SGD(lr=0.2)`, and
   `Adam(lr=0.1)` as three named runs. Overlay `loss/val` in TensorBoard and write one
   sentence on which converged fastest and most stably.

6. **Stretch — log the residuals.** Each epoch, log a histogram of residuals
   (`preds − targets`) with `add_histogram`. Watch the distribution tighten around 0 as
   training proceeds.

## Success criteria
- [ ] A 3-feature model trains to low loss on standardized inputs.
- [ ] You demonstrate standardized ≫ unstandardized at the same lr.
- [ ] Learned weights are close to the true ones (in the appropriate scale).
- [ ] `loss/train` and `loss/val` logged and tracking together.
- [ ] Three optimizer/lr runs overlaid with a one-sentence verdict.
