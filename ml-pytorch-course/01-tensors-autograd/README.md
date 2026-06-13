# Module 01 — Tensors & Autograd

**Goal:** get fluent with tensors (create, shape, broadcast, reduce) and understand
**autograd** — how PyTorch computes exact gradients for you. These two ideas power
everything else. ⏱️ ~2 h · 🎯 Prereq: 00.

---

## 1. Tensors are typed, shaped, n-D arrays

```python
import torch
s = torch.tensor(3.14)                 # 0-D: a scalar
v = torch.tensor([1., 2., 3.])         # 1-D: a vector,  shape (3,)
M = torch.tensor([[1., 2.], [3., 4.]]) # 2-D: a matrix,  shape (2, 2)
img = torch.randn(3, 28, 28)           # 3-D: a (C,H,W) image
batch = torch.randn(32, 3, 28, 28)     # 4-D: a batch of images
```

Three properties define a tensor: **shape** (sizes per dim), **dtype** (`float32`,
`int64`, …), and **device** (`cpu`/`cuda`/`mps`). Inspect them constantly:

```python
batch.shape    # torch.Size([32, 3, 28, 28])
batch.dtype    # torch.float32
batch.ndim     # 4
batch.numel()  # 32*3*28*28 = 75264
```

> **Convention:** model inputs are usually `(batch, features…)`. The first dim is almost
> always the batch.

## 2. Reshaping (no data copied)

```python
x = torch.arange(12.)          # shape (12,)
x.reshape(3, 4)                # (3, 4)
x.reshape(3, -1)               # -1 = "infer this dim" -> (3, 4)
x.view(2, 6)                   # like reshape, needs contiguous memory
x.unsqueeze(0).shape           # (1, 12)  add a batch dim
torch.randn(1, 12).squeeze().shape   # (12,) drop size-1 dims
torch.randn(2, 3).permute(1, 0).shape  # (3, 2) reorder dims
x.flatten(1)                   # flatten everything from dim 1 onward (common before a Linear)
```

## 3. Broadcasting (shape magic that avoids loops)

When shapes differ, PyTorch aligns them **from the right** and stretches size-1 dims:

```python
A = torch.ones(4, 3)
row = torch.tensor([10., 20., 30.])   # (3,) -> treated as (1,3)
A + row                                # adds row to every row of A  -> (4,3)

col = torch.tensor([[1.], [2.], [3.], [4.]])  # (4,1)
A + col                                # adds per-row scalar          -> (4,3)
```

Rules: dims are compatible if equal or one of them is 1. This is how a bias vector adds to a
whole batch.

## 4. Math & reductions

```python
a, b = torch.randn(3), torch.randn(3)
a + b, a * b           # elementwise
a @ b                  # dot product (1-D @ 1-D)
M = torch.randn(2, 3); N = torch.randn(3, 4)
M @ N                  # matrix multiply -> (2, 4)

x = torch.randn(4, 5)
x.sum(); x.mean(); x.std()          # over everything
x.sum(dim=0)                         # collapse rows  -> (5,)
x.mean(dim=1, keepdim=True)          # collapse cols, keep dim -> (4,1)
x.max(dim=1)                         # values AND indices
x.argmax(dim=1)                      # just indices (classification preds)
```

## 5. Autograd — the engine

When a tensor has `requires_grad=True`, PyTorch **records every operation** on it into a
**computation graph**. Calling `.backward()` walks that graph backward (the chain rule) and
fills each input's `.grad`.

```python
x = torch.tensor(2.0, requires_grad=True)
y = x ** 3 + 2 * x            # y = x^3 + 2x
y.backward()                  # dy/dx = 3x^2 + 2 = 14 at x=2
x.grad                        # tensor(14.)
```

With several parameters, you get the **gradient vector** — one partial derivative each:

```python
w = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
loss = (w ** 2).sum()         # d loss/dw_i = 2 w_i
loss.backward()
w.grad                        # tensor([2., 4., 6.])
```

> `backward()` only works from a **scalar** (the loss). If your output is a vector, reduce
> it first (`.sum()`/`.mean()`) — which is exactly what a loss function does.

## 6. Three rules you must internalize

**(a) Gradients accumulate.** `.grad` *adds up* across `backward()` calls. Zero it each
step or your updates are wrong:

```python
w.grad.zero_()        # before the next backward()
```

**(b) Updates happen under `no_grad`.** Changing a parameter is bookkeeping, not something
to differentiate:

```python
with torch.no_grad():
    w -= 0.1 * w.grad     # a gradient-descent step
```

**(c) `detach()` / `no_grad()` cut the graph.** Use them for evaluation, metrics, or moving
results to NumPy — anywhere you don't want gradients.

## 7. Putting it together: descent on a vector

```python
w = torch.zeros(3, requires_grad=True)
target = torch.tensor([1., 2., 3.])
for step in range(50):
    loss = ((w - target) ** 2).mean()
    loss.backward()
    with torch.no_grad():
        w -= 0.3 * w.grad
    w.grad.zero_()
print(w)            # ≈ tensor([1., 2., 3.])
```

That's the entire skeleton of training — Module 02 instruments it with TensorBoard so you
can *watch* it converge.

---

## Do the lab
Shape gymnastics, broadcasting, and computing gradients by hand vs autograd.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/tensor_basics.py`](./code/tensor_basics.py) — shapes, broadcasting, reductions
- [`code/autograd_basics.py`](./code/autograd_basics.py) — autograd vs hand-derivatives

## Key terms
tensor · shape/dtype/device · reshape/`view`/`unsqueeze`/`squeeze`/`permute`/`flatten` ·
broadcasting · matmul (`@`) · reduction (`sum`/`mean`/`argmax`) · `requires_grad` ·
computation graph · `.backward()` · `.grad` · gradient accumulation · `zero_()` ·
`no_grad` · `detach`

**Next →** [Module 02: Gradient Descent, Visualized](../02-gradient-descent-tensorboard/)
