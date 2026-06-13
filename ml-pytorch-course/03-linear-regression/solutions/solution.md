# Solution 03 — notes

Run: `python 03-linear-regression/solutions/challenge_solution.py` then
`tensorboard --logdir runs`.

## Key points

- **`nn.Linear(3, 1)`** holds a `(1, 3)` weight and a `(1,)` bias. The forward pass is
  `X @ Wᵀ + b`, batched over all rows.

- **Scaling is the whole challenge.** With features spanning [0,1], [0,100], [−10,10], the
  gradient for the large-scale feature dwarfs the others — an ill-conditioned ravine. At
  `lr=0.05` the raw run diverges or stalls while the standardized run converges smoothly.
  This is the same lesson as Module 02's elongated bowl, now on real features.

- **Standardize the target too.** The reference standardizes *both* `X` and `y`. With raw
  targets spanning hundreds, gradients are huge and Adam in particular needs an awkwardly
  large lr; standardizing `y` to mean 0 / std 1 makes every optimizer behave at normal lrs.
  It's standard practice for regression.

- **De-standardizing the weights.** With `Xs=(X−μₓ)/σₓ` and `ys=(y−μ_y)/σ_y`, the model
  learns `ys = Xs·w_s + b_s`. Converting back to original units:
  `w_orig = w_s · σ_y / σₓ` and `b_orig = μ_y + σ_y·b_s − Σ(w_orig·μₓ)`. After that the
  learned weights match the true `[1.5, −2, 0.5]` and bias `4` (within noise). If you only
  standardize `X`, drop the `σ_y`/`μ_y` terms: `w_orig = w_s / σₓ`.

- **Train vs val.** A linear model has too little capacity to overfit clean data, so
  `loss/train` and `loss/val` stay glued together. When you see them *diverge* in later
  modules, that's overfitting — and Module 06 is about fixing it.

- **Optimizer study.** On a well-conditioned (standardized) problem, `SGD(0.2)` and
  `Adam(0.1)` both converge quickly; `SGD(0.05)` is steady but slower. Adam's advantage
  shrinks on easy convex problems — it shines more on the messy non-convex losses of neural
  nets.

- **Residual histograms.** Logging `preds − targets` as a histogram each epoch shows the
  error distribution tightening toward a narrow band around 0 (its width ≈ the irreducible
  noise you added). A great sanity check that the model is actually fitting.
