# Module 03 — Linear Regression, the PyTorch Way

**Goal:** turn the hand-rolled descent of Module 02 into a *real* PyTorch workflow:
`nn.Module` for the model, a `Dataset`/`DataLoader` for batching, a loss function, and a
`torch.optim` optimizer — all instrumented with TensorBoard. ⏱️ ~3 h · 🎯 Prereq: 02.

---

## 1. The problem: fit a line to data

Given points `(x, y)` that roughly follow `y = w·x + b + noise`, recover `w` and `b`. It's
the simplest model — but it introduces every moving part you'll reuse forever.

## 2. A model is an `nn.Module`

Instead of bare tensors, wrap parameters in a module. `nn.Linear(in, out)` *is* `w·x + b`
with the parameters created for you:

```python
import torch.nn as nn
model = nn.Linear(in_features=1, out_features=1)   # one input, one output
list(model.parameters())                            # weight (1,1) and bias (1,)
model(x)                                             # forward pass: predictions
```

Subclassing gives full control and is the pattern for everything later:

```python
class LinReg(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(1, 1)
    def forward(self, x):
        return self.linear(x)
```

`model.parameters()` is exactly what you hand the optimizer.

## 3. A loss function measures wrongness

For regression, **mean squared error**:

```python
loss_fn = nn.MSELoss()
loss = loss_fn(preds, targets)     # mean of (preds - targets)^2
```

This replaces the `(w - 3)**2` you wrote by hand — same idea, batched over all samples.

## 4. An optimizer applies the update

`torch.optim` packages the "step against the gradient" you did manually:

```python
import torch.optim as optim
opt = optim.SGD(model.parameters(), lr=0.1)

opt.zero_grad()     # clear old grads (was w.grad.zero_())
loss.backward()     # compute grads (same as before)
opt.step()          # apply update (was: w -= lr * w.grad, for every param)
```

That three-line ritual — **zero, backward, step** — is the heartbeat of all training.

## 5. Datasets & DataLoaders: batching for free

Real training feeds the model **mini-batches**, not the whole dataset at once. A `Dataset`
holds samples; a `DataLoader` shuffles and batches them:

```python
from torch.utils.data import TensorDataset, DataLoader, random_split
ds = TensorDataset(X, y)                      # X:(N,1)  y:(N,1)
train_ds, val_ds = random_split(ds, [0.8, 0.2])
train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
val_loader   = DataLoader(val_ds, batch_size=64)
```

Iterating yields `(xb, yb)` batches. Using batches = **stochastic** gradient descent: each
step uses a noisy-but-cheap gradient estimate, which is faster and often generalizes better.

## 6. The training loop (memorize this shape)

```python
for epoch in range(num_epochs):
    model.train()
    for xb, yb in train_loader:
        opt.zero_grad()
        preds = model(xb)
        loss = loss_fn(preds, yb)
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        val_loss = sum(loss_fn(model(xb), yb).item() for xb, yb in val_loader) / len(val_loader)
    writer.add_scalar("loss/train", loss.item(), epoch)
    writer.add_scalar("loss/val",   val_loss,    epoch)
```

Every later module is this loop with a bigger model and more metrics.

## 7. What to watch in TensorBoard

- **`loss/train` and `loss/val`** on one chart — both should fall and roughly track each
  other. A gap that widens later = overfitting (Module 06).
- **`params/w` and `params/b`** — watch them converge to the true generating values.
- **The fitted line vs the data** — log a matplotlib figure each epoch (`add_figure`) and
  scrub the IMAGES slider to *watch the line rotate into place*.
- **The model graph** — `writer.add_graph(model, example_x)` to see the structure.

## 8. Feature scaling (a preview of why it matters)

If `x` spans 0–1000 and another feature spans 0–1, their gradients have wildly different
scales — the loss surface becomes ill-conditioned (the zig-zag of Module 02!). **Standardize
features** (subtract mean, divide by std) so the optimizer sees a nice round bowl. You'll do
this in the lab and *see* the difference in convergence speed.

---

## Do the lab
Build the dataset, train with a real loop, and watch the line fit in TensorBoard — then
compare scaled vs unscaled features. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/linreg.py`](./code/linreg.py) — full pipeline: data, model, loop, TensorBoard
- [`code/feature_scaling.py`](./code/feature_scaling.py) — scaled vs unscaled convergence

## Key terms
`nn.Module` · `nn.Linear` · `forward` · `MSELoss` · `optim.SGD`/`Adam` ·
zero/backward/step · `TensorDataset`/`DataLoader`/`random_split` · batch · epoch ·
train/val split · `model.train()`/`model.eval()` · feature scaling · `add_figure`/`add_graph`

**Next →** [Module 04: Neural Nets & Classification](../04-neural-networks-classification/)
