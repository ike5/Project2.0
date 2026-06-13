# Machine Learning with PyTorch & TensorBoard 🔥📉

A hands-on course that takes you from **raw tensors** to **training real neural networks**,
with **TensorBoard** wired in from the very first gradient so you can *watch* learning
happen — loss curves bending down, gradients flowing, weights shifting, and the descent
path crawling across a loss surface.

> **Who this is for:** You can write basic Python (functions, loops, lists) and remember a
> little high-school algebra. No calculus degree, no prior ML, no GPU required. We build
> the intuition for derivatives, gradients, and optimization as we go — and *visualize*
> every piece.

---

## Why PyTorch (and why TensorBoard)

Machine learning is mostly one idea repeated: **define a model, measure how wrong it is,
nudge it to be less wrong.** That nudging is **gradient descent**. The hard part for
beginners is that it's invisible — numbers change in a loop and *somehow* a model appears.

This course makes it visible.

- **PyTorch** gives you **tensors** (fast n-dimensional arrays) and **autograd**
  (automatic derivatives). You write math that looks like NumPy; PyTorch computes the
  gradients for you and runs on CPU or GPU unchanged.
- **TensorBoard** is a dashboard that reads logs your training loop writes and draws
  **live charts**: loss over time, weight histograms, the model graph, images, embeddings,
  and the **gradient-descent trajectory** itself.

```
   your training loop                       TensorBoard (browser)
 ┌────────────────────────┐   writes   ┌────────────────────────────┐
 │ forward → loss         │ ─────────▶ │  Scalars: loss ↓           │
 │ loss.backward()        │  ./runs/   │  Histograms: weights       │
 │ optimizer.step()       │            │  Graphs / Images / Embeds  │
 └────────────────────────┘            └────────────────────────────┘
```

---

## What makes it effective

- **Learn by doing.** Every module = concepts + a guided lab you run + an unguided
  challenge + reference solutions.
- **See the gradient descend.** From Module 02 on, every experiment logs to TensorBoard.
  You won't just *read* that loss goes down — you'll scrub the curve and watch the path
  roll into the valley.
- **Build up real skill.** You go from one parameter optimized by hand → linear regression
  → a multi-layer classifier → a convolutional network on images → a regularized,
  scheduled, tuned training pipeline.
- **A capstone.** Train an image classifier end-to-end with a clean training loop, full
  TensorBoard instrumentation, and a short experiment report you write yourself.

---

## Prerequisites

- **Python 3.9+** and `pip` (or conda). A laptop CPU is enough for the whole course.
- Comfort running commands in a terminal and opening a browser tab.
- ~2 GB free disk (PyTorch + a couple of small datasets + TensorBoard logs).

Versions: **PyTorch 2.x**, **torchvision 0.17+**, **TensorBoard 2.x**. A GPU (CUDA or
Apple `mps`) speeds up Modules 05–07 but is **never required** — Module 00 detects what
you have and the code adapts.

---

## The learning path

| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 00 | [Setup & First Tensor](./00-setup/) | Install the stack; detect CPU/GPU; launch TensorBoard | 0.5 h |
| 01 | [Tensors & Autograd](./01-tensors-autograd/) | Create/shape tensors; let autograd compute gradients | 2 h |
| 02 | [Gradient Descent, Visualized](./02-gradient-descent-tensorboard/) | Hand-code GD; **watch it descend in TensorBoard** | 3 h |
| 03 | [Linear Regression](./03-linear-regression/) | `nn.Module`, `DataLoader`, optimizers, a real fit | 3 h |
| 04 | [Neural Nets & Classification](./04-neural-networks-classification/) | Build an MLP; activations; cross-entropy; metrics | 3 h |
| 05 | [CNNs on Images](./05-cnn-images/) | Convolutions; train on FashionMNIST; log images/histograms | 3.5 h |
| 06 | [Training Techniques](./06-training-techniques/) | Overfitting, regularization, LR schedules, HParams | 3 h |
| 07 | [Capstone: Train & Report](./07-capstone/) | Ship a full pipeline + a TensorBoard experiment report | 3+ h |

**Total: a realistic ~21 hours.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts. Read first.
├── lab.md         ← Step-by-step guided lab with expected output. Do second.
├── code/          ← Runnable .py scripts the lab uses (all log to ./runs/).
├── challenge.md   ← An unguided task. Do third.
└── solutions/     ← Reference answers — peek only after trying.
```

Every code script is a plain `python script.py` — no notebooks required (though they work
great in one if you prefer). Scripts that train write TensorBoard logs to a `runs/`
directory you point TensorBoard at.

---

## Reference material

- **[cheatsheets/pytorch.md](./cheatsheets/pytorch.md)** — tensors, autograd, `nn`, training loop
- **[cheatsheets/tensorboard.md](./cheatsheets/tensorboard.md)** — every `SummaryWriter` call
- **[GLOSSARY.md](./GLOSSARY.md)** — every term in plain English
- **[VERIFY.md](./VERIFY.md)** — confirm your install + TensorBoard work
- **[requirements.txt](./requirements.txt)** — exact packages to `pip install`

## Quick start

```bash
cd ml-pytorch-course
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python 00-setup/code/verify_install.py              # prints versions + device
tensorboard --logdir runs                            # then open http://localhost:6006
```

Ready? **→ [Start with Module 00: Setup & First Tensor](./00-setup/)**
