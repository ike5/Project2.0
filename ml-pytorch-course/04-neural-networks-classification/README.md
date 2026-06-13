# Module 04 — Neural Networks & Classification

**Goal:** stack layers with **nonlinear activations** to model curved decision boundaries,
train a classifier with **cross-entropy**, track **accuracy**, and *watch the decision
boundary form* in TensorBoard. ⏱️ ~3 h · 🎯 Prereq: 03.

---

## 1. Why a single linear layer isn't enough

`nn.Linear` can only draw a **straight** boundary. Stack two linear layers with nothing
between them and — algebraically — you still have a single linear layer (`W₂(W₁x) = Wx`).
To bend the boundary you need a **nonlinearity** between layers.

## 2. Activation functions: the bend

An **activation** applies a nonlinear function elementwise after a linear layer:

- **ReLU** `max(0, x)` — the default. Cheap, avoids vanishing gradients, works.
- **Sigmoid** `1/(1+e⁻ˣ)` — squashes to (0,1); saturates (tiny gradients) at the ends.
- **Tanh** — squashes to (−1,1); zero-centered but also saturates.

Linear → ReLU → Linear → ReLU → Linear gives a model that can carve **curved, multi-region**
boundaries. More layers/width = more expressive (and more prone to overfit — Module 06).

## 3. A multi-layer perceptron (MLP)

```python
import torch.nn as nn
model = nn.Sequential(
    nn.Linear(2, 32), nn.ReLU(),
    nn.Linear(32, 32), nn.ReLU(),
    nn.Linear(32, 2),                 # 2 outputs = 2 class logits
)
```

The final layer outputs **logits** — raw scores, one per class. No softmax here; the loss
function applies it internally (see below).

## 4. Cross-entropy: the classification loss

For classification, MSE is the wrong tool. Use **cross-entropy**, which measures how far the
predicted class *distribution* is from the true class:

```python
loss_fn = nn.CrossEntropyLoss()
loss = loss_fn(logits, labels)        # logits:(N,C) float ; labels:(N,) int64
```

> Two gotchas baked into `CrossEntropyLoss`:
> 1. It takes **raw logits**, *not* softmax outputs — it does softmax internally (stably).
> 2. Labels are **integer class indices** `(N,)`, not one-hot vectors.

To get probabilities for inspection: `probs = logits.softmax(dim=1)`. To get predictions:
`preds = logits.argmax(dim=1)`.

## 5. Accuracy (and why loss isn't enough)

Loss is what you optimize; **accuracy** is what you report. Compute it on the validation set:

```python
preds = logits.argmax(dim=1)
acc = (preds == labels).float().mean().item()
```

Log both `loss/val` and `acc/val` — loss can wiggle while accuracy climbs, and accuracy is
what a stakeholder understands.

## 6. The training loop (now with metrics)

Same `zero → backward → step`, plus per-epoch validation metrics:

```python
for epoch in range(epochs):
    model.train()
    for xb, yb in train_loader:
        opt.zero_grad()
        loss = loss_fn(model(xb), yb)
        loss.backward()
        opt.step()

    model.eval()
    with torch.no_grad():
        logits = model(X_val)
        val_loss = loss_fn(logits, y_val).item()
        val_acc = (logits.argmax(1) == y_val).float().mean().item()
    writer.add_scalar("loss/val", val_loss, epoch)
    writer.add_scalar("acc/val",  val_acc,  epoch)
```

## 7. See the boundary form 🌀

The dataset (`make_moons`-style) is two interleaving half-moons — **not** linearly
separable. Each epoch we evaluate the model on a fine grid and log a **decision-boundary
figure**: colored regions for each predicted class with the data on top. Scrub the IMAGES
slider and watch a straight-ish split warp into the curved boundary that separates the
moons. That's representation learning, visualized.

We also log **weight and gradient histograms** so you can watch the parameters spread out as
the network learns — and catch dead/exploding units.

## 8. Initialization & a word on depth

Parameters start random; PyTorch's defaults (Kaiming for ReLU layers) are sensible. Watch
the gradient histograms: if early-layer gradients collapse toward 0 (**vanishing**) the net
won't learn — a sign to check activations, scaling, or depth. ReLU + reasonable width keeps
gradients healthy here.

---

## Do the lab
Train an MLP on the moons, watch the boundary and metrics, and compare activations and
widths. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/mlp_classify.py`](./code/mlp_classify.py) — MLP on two-moons; logits, cross-entropy,
  accuracy, decision-boundary figures, weight/grad histograms
- [`code/activation_compare.py`](./code/activation_compare.py) — ReLU vs Sigmoid vs Tanh (and
  no activation) on the same data

## Key terms
MLP · hidden layer · activation (ReLU/Sigmoid/Tanh) · nonlinearity · logits · softmax ·
`CrossEntropyLoss` · class indices vs one-hot · accuracy · decision boundary ·
weight/grad histograms · vanishing gradients · `nn.Sequential`

**Next →** [Module 05: CNNs on Images](../05-cnn-images/)
