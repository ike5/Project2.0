"""Reference solution for Challenge 04 — 3-class spiral classification.

Run:
    python 04-neural-networks-classification/solutions/challenge_solution.py
    tensorboard --logdir runs
"""

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.tensorboard import SummaryWriter

N_CLASSES = 3


def make_spiral(points_per_class: int = 300, noise: float = 0.2, seed: int = 0):
    torch.manual_seed(seed)
    Xs, ys = [], []
    for c in range(N_CLASSES):
        r = torch.linspace(0.0, 1.0, points_per_class)
        theta = torch.linspace(0, 4 * math.pi, points_per_class) + c * (2 * math.pi / N_CLASSES)
        theta = theta + torch.randn(points_per_class) * noise
        Xs.append(torch.stack([r * theta.cos(), r * theta.sin()], dim=1))
        ys.append(torch.full((points_per_class,), c))
    X = torch.cat(Xs); y = torch.cat(ys).long()
    perm = torch.randperm(X.shape[0])
    return X[perm], y[perm]


def split(X, y, frac=0.8, seed=0):
    n = X.shape[0]
    idx = torch.randperm(n, generator=torch.Generator().manual_seed(seed))
    k = int(frac * n)
    return X[idx[:k]], y[idx[:k]], X[idx[k:]], y[idx[k:]]


def build(hidden):
    return nn.Sequential(
        nn.Linear(2, hidden), nn.ReLU(),
        nn.Linear(hidden, hidden), nn.ReLU(),
        nn.Linear(hidden, N_CLASSES),
    )


def boundary_fig(model, X, y, mean, std, step):
    xx = torch.linspace(X[:, 0].min() - 0.3, X[:, 0].max() + 0.3, 200)
    yy = torch.linspace(X[:, 1].min() - 0.3, X[:, 1].max() + 0.3, 200)
    gx, gy = torch.meshgrid(xx, yy, indexing="xy")
    grid = torch.stack([gx.reshape(-1), gy.reshape(-1)], dim=1)
    grid_s = (grid - mean) / std
    with torch.no_grad():
        zz = model(grid_s).argmax(1).reshape(gx.shape)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.contourf(gx.numpy(), gy.numpy(), zz.numpy(), levels=2, alpha=0.3, cmap="brg")
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap="brg", s=8, edgecolor="k", linewidth=0.2)
    ax.set_title(f"3-class spiral boundary (epoch {step})")
    fig.tight_layout()
    return fig


def confusion_fig(cm):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(cm, cmap="Blues")
    for i in range(N_CLASSES):
        for j in range(N_CLASSES):
            ax.text(j, i, int(cm[i, j].item()), ha="center", va="center")
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_xticks(range(N_CLASSES)); ax.set_yticks(range(N_CLASSES))
    fig.tight_layout()
    return fig


def train(tag, hidden, Xtr, ytr, Xva, yva, Xraw, yraw, mean, std, epochs=200, log_fig=False):
    writer = SummaryWriter(log_dir=f"runs/spiral_{tag}")
    model = build(hidden)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=0.02)
    loader = DataLoader(TensorDataset(Xtr, ytr), batch_size=64, shuffle=True)
    for epoch in range(epochs):
        model.train()
        for xb, yb in loader:
            opt.zero_grad(); loss_fn(model(xb), yb).backward(); opt.step()
        model.eval()
        with torch.no_grad():
            logits = model(Xva)
            acc = (logits.argmax(1) == yva).float().mean().item()
            writer.add_scalar("loss/train", loss_fn(model(Xtr), ytr).item(), epoch)
            writer.add_scalar("loss/val", loss_fn(logits, yva).item(), epoch)
            writer.add_scalar("acc/val", acc, epoch)
        if log_fig and (epoch % 20 == 0 or epoch == epochs - 1):
            writer.add_figure("boundary", boundary_fig(model, Xraw, yraw, mean, std, epoch), epoch)
    # Confusion matrix on val.
    with torch.no_grad():
        preds = model(Xva).argmax(1)
    cm = torch.zeros(N_CLASSES, N_CLASSES)
    for t, pr in zip(yva.tolist(), preds.tolist()):
        cm[t, pr] += 1
    if log_fig:
        writer.add_figure("confusion", confusion_fig(cm), epochs)
    writer.close()
    return acc, cm


def main() -> None:
    Xraw, yraw = make_spiral()
    mean, std = Xraw.mean(0, keepdim=True), Xraw.std(0, keepdim=True)
    X = (Xraw - mean) / std
    Xtr, ytr, Xva, yva = split(X, yraw)

    print("== Task 4: capacity sweep ==")
    print("hidden   val acc")
    for h in [4, 16, 64]:
        acc, cm = train(f"h{h}", h, Xtr, ytr, Xva, yva, Xraw, yraw, mean, std,
                        log_fig=(h == 64))
        print(f"{h:<8} {acc:.3f}")
        if h == 64:
            best_cm = cm
    print("  4 underfits (arms blur together); 16 mostly separates; 64 cleanly separates.")

    print("\n== Task 5: confusion matrix (hidden=64, val) ==")
    print("       pred0 pred1 pred2")
    for i in range(N_CLASSES):
        row = "  ".join(f"{int(best_cm[i, j].item()):5d}" for j in range(N_CLASSES))
        print(f"true{i}  {row}")
    print("  Confusion concentrates near the spiral center, where the arms nearly meet.")
    print("\nView: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
