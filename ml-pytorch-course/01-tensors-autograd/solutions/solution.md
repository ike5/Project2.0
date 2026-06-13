# Solution 01 — notes

Run the reference: `python 01-tensors-autograd/solutions/challenge_solution.py`
(prints results and asserts every check).

## Key points

1. **Shape surgery.** `reshape` is the safe default; `view` works only on contiguous
   memory (after some `permute`s you'd need `.contiguous()` first). The product of the new
   shape must equal `numel()` (24 here).

2. **Standardization.** Use `dim=0` to reduce *down columns*, and `keepdim=True` so the
   `(1, 5)` stats broadcast back over the `(100, 5)` data. Use std (population vs sample
   differs by `unbiased=`); columns end up mean ≈ 0, std ≈ 1.

3. **One-parameter gradient.** `d/dw (3w² + 5w − 2) = 6w + 5 = 29` at `w = 4`.

4. **Two-parameter gradient.** With `loss = (ab − 6)²`, the chain rule gives
   `∂/∂a = 2(ab−6)·b = −16` and `∂/∂b = 2(ab−6)·a = −8` at `a=1, b=2`. Both negative →
   increasing `a` or `b` lowers the loss (makes `ab` closer to 6).

5. **Convergence vs divergence.** For `f(w) = (w−3)²`, the GD update simplifies to
   `w ← w(1 − 2·lr) + 6·lr`. It's stable iff `|1 − 2·lr| < 1`, i.e. `0 < lr < 1`. For
   `0.5 < lr < 1` it overshoots and **oscillates** while still converging; at `lr ≥ 1` it
   **diverges**. This closed form is why Module 02's learning-rate experiments behave the
   way they do.

6. **`no_grad` for updates.** An in-place update on a leaf tensor that `requires_grad`
   raises a RuntimeError (or, if done out-of-place, silently builds graph history you don't
   want). Wrapping the update in `torch.no_grad()` tells autograd "this is bookkeeping,
   don't track it." Optimizers do this internally.
