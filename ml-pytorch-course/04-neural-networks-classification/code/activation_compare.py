"""Compare activation functions on the same two-moons problem.

Trains four otherwise-identical MLPs that differ only in their activation:
none (linear), Sigmoid, Tanh, ReLU. Each is its own run so you can overlay val
accuracy in TensorBoard and see which learns the curved boundary best/fastest.

Run:
    python 04-neural-networks-classification/code/activation_compare.py
    tensorboard --logdir runs    # overlay acc/val across the four runs
"""

import os
import sys

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch.utils.tensorboard import SummaryWriter

sys.path.insert(0, os.path.dirname(__file__))
from data import make_moons, split  # noqa: E402

ACTIVATIONS = {
    "none": nn.Identity,
    "sigmoid": nn.Sigmoid,
    "tanh": nn.Tanh,
    "relu": nn.ReLU,
}


def build(act_cls, hidden=32):
    return nn.Sequential(
        nn.Linear(2, hidden), act_cls(),
        nn.Linear(hidden, hidden), act_cls(),
        nn.Linear(hidden, 2),
    )


def train(name, act_cls, Xtr, ytr, Xva, yva, epochs=80):
    writer = SummaryWriter(log_dir=f"runs/act_{name}")
    model = build(act_cls)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=0.05)
    loader = DataLoader(TensorDataset(Xtr, ytr), batch_size=64, shuffle=True)
    best_acc = 0.0
    for epoch in range(epochs):
        model.train()
        for xb, yb in loader:
            opt.zero_grad()
            loss_fn(model(xb), yb).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            logits = model(Xva)
            acc = (logits.argmax(1) == yva).float().mean().item()
            writer.add_scalar("loss/val", loss_fn(logits, yva).item(), epoch)
            writer.add_scalar("acc/val", acc, epoch)
        best_acc = max(best_acc, acc)
    writer.close()
    return best_acc


def main() -> None:
    X, y = make_moons(n=1000, noise=0.2)
    Xtr, ytr, Xva, yva = split(X, y)
    print("activation   best val acc")
    print("-" * 28)
    for name, cls in ACTIVATIONS.items():
        acc = train(name, cls, Xtr, ytr, Xva, yva)
        print(f"{name:10s}   {acc:.3f}")
    print("\n'none' (linear) plateaus low — it can't curve. ReLU/Tanh separate the moons.")
    print("Overlay acc/val: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
