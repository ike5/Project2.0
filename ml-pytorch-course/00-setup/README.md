# Module 00 — Setup & First Tensor

**Goal:** install PyTorch + TensorBoard, detect whether you have a GPU, create your first
tensor, and confirm the *log → dashboard* pipeline works end to end. ⏱️ ~30 min.

---

## 1. Install

From the course folder, in a fresh virtual environment (see [VERIFY.md](../VERIFY.md)):

```bash
pip install -r ../requirements.txt        # torch, torchvision, tensorboard, matplotlib, numpy
```

CPU wheels are the default and are **all this course needs**. A GPU just makes Modules
05–07 faster.

## 2. Devices: where tensors live

A tensor lives on a **device**:

- **`cpu`** — always available; fine for everything here.
- **`cuda`** — an NVIDIA GPU.
- **`mps`** — Apple Silicon GPU (M-series Macs).

The portable pattern, used in every later module:

```python
import torch
device = ("cuda" if torch.cuda.is_available()
          else "mps" if torch.backends.mps.is_available()
          else "cpu")
```

Move data/models with `.to(device)`. Write your code once; it runs anywhere.

## 3. Your first tensor

A **tensor** is an n-dimensional array — the only data structure PyTorch really has.

```python
import torch
x = torch.tensor([[1., 2., 3.],
                  [4., 5., 6.]])
print(x.shape)    # torch.Size([2, 3]) — 2 rows, 3 cols
print(x.dtype)    # torch.float32
print(x.mean())   # tensor(3.5000)
print(x * 2)      # elementwise
```

Scalars are 0-D tensors, vectors 1-D, matrices 2-D, and an image batch is 4-D
`(batch, channels, height, width)`. Most PyTorch bugs are **shape** bugs — get comfortable
printing `.shape`.

## 4. A one-line taste of autograd (the whole course in miniature)

```python
w = torch.tensor(0.0, requires_grad=True)   # a parameter to learn
loss = (w - 3) ** 2                          # minimized when w = 3
loss.backward()                              # autograd computes d loss / d w
print(w.grad)                                # tensor(-6.) → step the other way to reduce loss
```

That `w.grad` is the gradient. **Gradient descent** is just nudging `w` against its
gradient, over and over — which is exactly what Module 02 visualizes.

## 5. TensorBoard: from code to dashboard

Your training loop writes event files with a `SummaryWriter`; TensorBoard reads them:

```python
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter("runs/hello")
for step in range(100):
    writer.add_scalar("demo/sine", torch.sin(torch.tensor(step / 10.0)), step)
writer.close()
```

```bash
tensorboard --logdir runs        # open http://localhost:6006 → SCALARS
```

You'll see a sine wave you *generated programmatically* — proof the pipeline works. From
Module 02 on, the curves are real losses and gradients.

---

## Do the lab
Run the two provided scripts, read their output, and open TensorBoard.
👉 **[lab.md](./lab.md)**

## Code
- [`code/verify_install.py`](./code/verify_install.py) — versions, device, autograd check
- [`code/hello_tensorboard.py`](./code/hello_tensorboard.py) — writes a scalar curve to `runs/hello`

## Key terms
tensor · shape · dtype · device (`cpu`/`cuda`/`mps`) · `requires_grad` · `.grad` ·
`SummaryWriter` · run / `logdir` · scalar

**Next →** [Module 01: Tensors & Autograd](../01-tensors-autograd/)
