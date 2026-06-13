"""A small hyperparameter grid logged to TensorBoard's HPARAMS dashboard.

Sweeps learning rate x dropout, training a model for each combo and logging the config
plus its best validation accuracy/loss via add_hparams. Open the HPARAMS tab to sort,
filter, and compare configs (table / parallel coordinates / scatter).

Run:
    python 06-training-techniques/code/hparam_search.py
    tensorboard --logdir runs   # open the HPARAMS tab
"""

import itertools

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms


def loaders(train_n=4000, seed=0):
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.286,), (0.353,))])
    full = datasets.FashionMNIST("data", train=True, download=True, transform=tf)
    test = datasets.FashionMNIST("data", train=False, download=True, transform=tf)
    idx = torch.randperm(len(full), generator=torch.Generator().manual_seed(seed))[:train_n]
    return (DataLoader(Subset(full, idx.tolist()), batch_size=128, shuffle=True),
            DataLoader(test, batch_size=512))


def model(dropout):
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(28 * 28, 256), nn.ReLU(), nn.Dropout(dropout),
        nn.Linear(256, 128), nn.ReLU(), nn.Dropout(dropout),
        nn.Linear(128, 10),
    )


@torch.no_grad()
def evaluate(m, loader, loss_fn):
    m.eval()
    loss, correct, n = 0.0, 0, 0
    for xb, yb in loader:
        logits = m(xb)
        loss += loss_fn(logits, yb).item() * xb.size(0)
        correct += (logits.argmax(1) == yb).sum().item()
        n += xb.size(0)
    return loss / n, correct / n


def train_one(lr, dropout, train_loader, test_loader, epochs=15):
    # Each combo gets its own run dir AND an add_hparams summary so it appears in HPARAMS.
    run_name = f"runs/hparam_lr{lr}_do{dropout}"
    writer = SummaryWriter(log_dir=run_name)
    m = model(dropout)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    best_acc, best_loss = 0.0, float("inf")
    for epoch in range(epochs):
        m.train()
        for xb, yb in train_loader:
            opt.zero_grad(); loss_fn(m(xb), yb).backward(); opt.step()
        vl, va = evaluate(m, test_loader, loss_fn)
        writer.add_scalar("loss/val", vl, epoch)
        writer.add_scalar("acc/val", va, epoch)
        best_acc = max(best_acc, va)
        best_loss = min(best_loss, vl)
    writer.add_hparams(
        {"lr": lr, "dropout": dropout},
        {"hparam/val_acc": best_acc, "hparam/val_loss": best_loss},
    )
    writer.close()
    return best_acc


def main() -> None:
    train_loader, test_loader = loaders()
    lrs = [1e-2, 1e-3, 1e-4]
    dropouts = [0.0, 0.3, 0.5]
    print("lr        dropout   best val acc")
    print("-" * 36)
    results = []
    for lr, do in itertools.product(lrs, dropouts):
        acc = train_one(lr, do, train_loader, test_loader)
        results.append(((lr, do), acc))
        print(f"{lr:<9} {do:<9} {acc:.4f}")
    best = max(results, key=lambda r: r[1])
    print(f"\nbest config: lr={best[0][0]}, dropout={best[0][1]}  ->  acc={best[1]:.4f}")
    print("Compare all configs in the HPARAMS tab: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
