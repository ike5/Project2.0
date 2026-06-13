"""Train an MLP to classify the two-moons dataset, with rich TensorBoard logging.

Logs: train/val cross-entropy loss, val accuracy, weight & gradient histograms, and a
decision-boundary figure each epoch (scrub the IMAGES slider to watch the boundary curve
into shape).

Run:
    python 04-neural-networks-classification/code/mlp_classify.py
    tensorboard --logdir runs    # SCALARS: loss+acc ; IMAGES: boundary ; HISTOGRAMS

Try --hidden 2 (too weak) or --no-relu (a linear model can't separate the moons).
"""

import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.tensorboard import SummaryWriter

sys.path.insert(0, os.path.dirname(__file__))
from data import make_moons, split  # noqa: E402


def build_model(hidden: int, use_relu: bool) -> nn.Module:
    act = nn.ReLU if use_relu else nn.Identity
    return nn.Sequential(
        nn.Linear(2, hidden), act(),
        nn.Linear(hidden, hidden), act(),
        nn.Linear(hidden, 2),
    )


def boundary_figure(model, X, y, step):
    # Evaluate the model over a grid to color the predicted regions.
    xx = torch.linspace(X[:, 0].min() - 0.5, X[:, 0].max() + 0.5, 200)
    yy = torch.linspace(X[:, 1].min() - 0.5, X[:, 1].max() + 0.5, 200)
    gx, gy = torch.meshgrid(xx, yy, indexing="xy")
    grid = torch.stack([gx.reshape(-1), gy.reshape(-1)], dim=1)
    with torch.no_grad():
        zz = model(grid).argmax(1).reshape(gx.shape)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.contourf(gx.numpy(), gy.numpy(), zz.numpy(), levels=1, alpha=0.3, cmap="coolwarm")
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap="coolwarm", s=10, edgecolor="k", linewidth=0.2)
    ax.set_title(f"decision boundary (epoch {step})")
    ax.set_xlabel("x1"); ax.set_ylabel("x2")
    fig.tight_layout()
    return fig


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--hidden", type=int, default=32)
    p.add_argument("--epochs", type=int, default=80)
    p.add_argument("--lr", type=float, default=0.05)
    p.add_argument("--no-relu", action="store_true", help="remove activations (stays linear)")
    args = p.parse_args()

    X, y = make_moons(n=1000, noise=0.2)
    Xtr, ytr, Xva, yva = split(X, y)
    train_loader = DataLoader(TensorDataset(Xtr, ytr), batch_size=64, shuffle=True)

    model = build_model(args.hidden, use_relu=not args.no_relu)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    tag = f"mlp_h{args.hidden}" + ("_norelu" if args.no_relu else "")
    writer = SummaryWriter(log_dir=f"runs/{tag}")
    writer.add_graph(model, Xtr[:1])

    for epoch in range(args.epochs):
        model.train()
        for xb, yb in train_loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            tr_logits = model(Xtr)
            va_logits = model(Xva)
            tr_loss = loss_fn(tr_logits, ytr).item()
            va_loss = loss_fn(va_logits, yva).item()
            va_acc = (va_logits.argmax(1) == yva).float().mean().item()

        writer.add_scalar("loss/train", tr_loss, epoch)
        writer.add_scalar("loss/val", va_loss, epoch)
        writer.add_scalar("acc/val", va_acc, epoch)

        # Weight & gradient distributions (gradients exist after the last backward()).
        for name, param in model.named_parameters():
            writer.add_histogram(f"weights/{name}", param, epoch)
            if param.grad is not None:
                writer.add_histogram(f"grads/{name}", param.grad, epoch)

        if epoch % 5 == 0 or epoch == args.epochs - 1:
            writer.add_figure("boundary", boundary_figure(model, X, y, epoch), epoch)
            print(f"epoch {epoch:2d}  train={tr_loss:.4f}  val={va_loss:.4f}  acc={va_acc:.3f}")

    writer.close()
    print(f"\nfinal val accuracy: {va_acc:.3f}")
    print("View: tensorboard --logdir runs  -> IMAGES -> boundary (scrub the slider)")


if __name__ == "__main__":
    main()
