# Lab 01 — Tensors & Autograd

**You'll:** run the two scripts, then reproduce key results yourself in the REPL.
⏱️ ~50 min. From the `ml-pytorch-course` folder.

---

## Part A — Tensor basics

```bash
python 01-tensors-autograd/code/tensor_basics.py
```
✅ Read every printed shape. Before each `@` / reduction, cover the output and **predict
the shape**, then check.

Now in the REPL, reproduce broadcasting:
```python
>>> import torch
>>> A = torch.ones(4, 3); b = torch.tensor([10., 20., 30.])
>>> (A + b).shape          # torch.Size([4, 3])
>>> A + torch.arange(4.).reshape(4, 1)   # per-row scalar
```
✅ You can explain *why* `(4,3) + (3,)` works but `(4,3) + (4,)` raises an error
(alignment is from the right; `(4,)` would need to match the last dim, which is 3).

## Part B — Autograd vs hand math

```bash
python 01-tensors-autograd/code/autograd_basics.py
```
✅ The autograd gradients match the hand-derived ones in sections 1–2.

Confirm one yourself:
```python
>>> x = torch.tensor(3.0, requires_grad=True)
>>> y = (2 * x + 1) ** 2
>>> y.backward()
>>> x.grad            # 2*(2x+1)*2 = 4*(2*3+1) = 28  -> tensor(28.)
```

## Part C — Why we zero gradients

```python
>>> w = torch.tensor(5.0, requires_grad=True)
>>> for _ in range(3):
...     (w * 1).backward()
...     print(w.grad)        # 1, then 2, then 3 — accumulation!
>>> w.grad.zero_(); w.grad   # tensor(0.)
```
✅ You can state the rule: **`.grad` accumulates; call `zero_grad()`/`zero_()` each step.**

## Part D — Hand-rolled descent

In the REPL, minimize `f(w) = (w - 7)**2` from `w=0`:
```python
>>> w = torch.tensor(0.0, requires_grad=True); lr = 0.1
>>> for step in range(40):
...     loss = (w - 7) ** 2
...     loss.backward()
...     with torch.no_grad():
...         w -= lr * w.grad
...     w.grad.zero_()
>>> w            # ≈ tensor(7.)
```
✅ `w` converges to ~7. Try `lr=0.6` (faster but oscillates) and `lr=1.1` (**diverges** —
the loss blows up). That instability is the central lesson of Module 02.

## Part E — Stretch

- Set `requires_grad=True` on a `(2,2)` matrix `W`, compute `loss = (W @ W.T).sum()`, call
  `backward()`, and inspect `W.grad`'s shape (it matches `W`).
- Wrap a computation in `with torch.no_grad():` and confirm the result has
  `requires_grad == False`.

---

✅ **Done when:** you can compute a simple gradient by hand and confirm it with autograd,
and you can explain why descent diverges at too-large a learning rate.

**Next →** [challenge.md](./challenge.md) then
[Module 02](../02-gradient-descent-tensorboard/)
