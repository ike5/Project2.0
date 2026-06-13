# Challenge 01 — Tensors & Autograd

Solutions in [`solutions/`](./solutions/). Try first — no peeking until you've attempted
each task.

## Tasks

1. **Shape surgery.** Starting from `x = torch.arange(24.)`, produce — using only
   `reshape`/`view`/`permute`/`unsqueeze`/`squeeze` — tensors of shape `(2, 3, 4)`,
   `(4, 6)`, `(24, 1)`, and `(1, 2, 12)`. Print each shape to confirm.

2. **Broadcast a normalization.** Given `X = torch.randn(100, 5)`, standardize each
   **column** to mean 0, std 1 using broadcasting (compute per-column mean/std with
   `dim=0, keepdim=True`). Verify the result's column means are ~0 and stds ~1.

3. **Gradient by hand, then autograd.** For `f(w) = 3*w**2 + 5*w - 2` at `w = 4`:
   compute `df/dw` by hand, then with autograd, and assert they match to 1e-5.

4. **Two-parameter gradient.** For `loss = (a*b - 6)**2` with `a=1.0, b=2.0`
   (both `requires_grad=True`), call `backward()` and report `a.grad` and `b.grad`.
   Derive them by hand too (chain rule) and confirm.

5. **Minimize a quadratic with descent.** Minimize `f(w) = (w - 3)**2 + 2` from `w = -5`
   with `lr = 0.1` for 60 steps. Print the final `w` (should be ≈ 3) and final loss
   (≈ 2). Then find a learning rate that makes it **diverge** and one that **oscillates**
   without diverging.

6. **Stretch — no_grad accounting.** Show, with a printed example, that updating a
   parameter *without* `torch.no_grad()` either errors or pollutes the graph, and that
   wrapping the update in `no_grad()` fixes it.

## Success criteria
- [ ] All four target shapes produced from the same source tensor.
- [ ] Standardized columns have mean ≈ 0 and std ≈ 1.
- [ ] Hand-derived and autograd gradients match for tasks 3 and 4.
- [ ] Descent converges to ≈ 3; you can name a diverging and an oscillating lr.
- [ ] You can explain in one sentence why parameter updates go under `no_grad()`.
