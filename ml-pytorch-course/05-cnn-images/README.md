# Module 05 — Convolutional Networks on Images

**Goal:** classify images with a **CNN**, and use TensorBoard's image-centric tools — input
grids, prediction grids, learned filters, and embeddings — to *see* what the network does.
⏱️ ~3.5 h · 🎯 Prereq: 04.

---

## 1. Why not just flatten the image into an MLP?

A 28×28 image flattened is a 784-vector; an MLP throws away the fact that nearby pixels are
related and that a feature (an edge, a curve) means the same thing wherever it appears. A
**convolution** respects both: it slides a small learnable filter across the image, reusing
the same weights everywhere (**parameter sharing**) and capturing **local** structure.

## 2. The convolution, briefly

`nn.Conv2d(in_channels, out_channels, kernel_size)` learns `out_channels` little filters,
each `in_channels × k × k`. Each filter slides over the input and produces a **feature map**
highlighting where its pattern occurs.

```python
import torch.nn as nn
conv = nn.Conv2d(in_channels=1, out_channels=16, kernel_size=3, padding=1)
# input  (N, 1, 28, 28)  ->  output (N, 16, 28, 28)   (padding=1 keeps H,W)
```

- **channels** — depth of the volume (1 for grayscale, 3 for RGB; many after a conv).
- **kernel_size** — filter size (3×3 is the workhorse).
- **padding** — zero-border so output keeps spatial size.
- **stride** — step of the slide (2 halves the resolution).

## 3. Pooling & the typical block

**Max pooling** downsamples by taking the max in each window — shrinking spatial size while
keeping the strongest activations:

```python
nn.MaxPool2d(2)        # halves H and W
```

A classic block is **Conv → ReLU → Pool**, stacked a few times to go from many pixels/few
channels to few pixels/many channels, then **flatten** and finish with linear layers:

```python
model = nn.Sequential(
    nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # -> (16,14,14)
    nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # -> (32, 7, 7)
    nn.Flatten(),                                                 # -> (32*7*7,)
    nn.Linear(32 * 7 * 7, 128), nn.ReLU(),
    nn.Linear(128, 10),                                           # 10 FashionMNIST classes
)
```

> **Shape bookkeeping is the skill here.** Track `(N, C, H, W)` through every layer; the
> `Linear` input size must equal `C·H·W` after the last conv/pool. Get it wrong and PyTorch
> tells you with a shape mismatch.

## 4. The dataset: FashionMNIST

10 classes of 28×28 grayscale clothing images (T-shirt, trouser, … ankle boot).
torchvision downloads it and gives you a `Dataset`:

```python
from torchvision import datasets, transforms
tf = transforms.Compose([transforms.ToTensor(),                 # -> (1,28,28) in [0,1]
                         transforms.Normalize((0.286,), (0.353,))])  # FashionMNIST stats
train = datasets.FashionMNIST("data", train=True,  download=True, transform=tf)
test  = datasets.FashionMNIST("data", train=False, download=True, transform=tf)
```

`ToTensor` makes a `(1,28,28)` float tensor in `[0,1]`; `Normalize` standardizes it (the
feature-scaling lesson from Module 03, for pixels).

## 5. Device & the loop, scaled up

Everything from Module 04 holds; now we move batches to the GPU if present:

```python
device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
model.to(device)
for xb, yb in train_loader:
    xb, yb = xb.to(device), yb.to(device)
    ...
```

CPU is fine here — a few epochs of this small CNN trains in a couple of minutes.

## 6. The TensorBoard image toolkit 🖼️

This is where TensorBoard shines:

- **Input grid** — `add_image` a `make_grid` of a batch so you can eyeball your data and
  confirm normalization didn't mangle it.
- **Model graph** — `add_graph(model, example)` to see the conv stack.
- **Prediction grid** — each epoch, log a grid of test images titled with
  `pred (true)`, green if correct, red if wrong. Scrub it to watch mistakes get fixed.
- **Learned filters** — visualize the first conv layer's weights as images; they often
  become edge/blob detectors.
- **Histograms** — weights and gradients per layer, as before.
- **Embeddings (projector)** — `add_embedding` of the penultimate features colored by class;
  watch the 10 clusters separate.

## 7. Reading training like a pro

- `loss/train` ↓ and `acc/test` ↑ — the headline.
- A widening gap between train and test loss = **overfitting** (Module 06 fixes it).
- Filters that stay noise = that layer isn't learning (check lr/normalization).
- Embeddings that don't cluster = features aren't separating classes yet.

---

## Do the lab
Train the CNN, browse inputs/predictions/filters, and inspect the embedding projector.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
- [`code/cnn_fashion.py`](./code/cnn_fashion.py) — CNN on FashionMNIST with the full image
  toolkit (inputs, predictions, filters, histograms, embeddings)
- [`code/inspect_data.py`](./code/inspect_data.py) — log a labeled input grid + class counts

## Key terms
convolution / `Conv2d` · channel · kernel · stride · padding · feature map ·
parameter sharing · `MaxPool2d` · `Flatten` · (N,C,H,W) shapes · FashionMNIST ·
`ToTensor`/`Normalize` · `add_image`/`make_grid` · filter visualization ·
`add_embedding` / projector

**Next →** [Module 06: Training Techniques](../06-training-techniques/)
