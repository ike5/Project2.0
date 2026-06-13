"""Induce overfitting on purpose, then regularize it away — visible in TensorBoard.

A high-capacity MLP on a SMALL, noisy subset of FashionMNIST will memorize the training
set: train loss -> ~0 while val loss turns up. We run two configs:
  - 'plain'       : no regularization (overfits hard)
  - 'regularized' : dropout + weight decay (closes the gap)

Overlay loss/train and loss/val for both runs to see the generalization gap shrink.

Run:
    python 06-training-techniques/code/overfit_demo.py
    tensorboard --logdir runs
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms


def small_loaders(train_n=1000, seed=0):
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.286,), (0.353,))])
    full = datasets.FashionMNIST("data", train=True, download=True, transform=tf)
    test = datasets.FashionMNIST("data", train=False, download=True, transform=tf)
    g = torch.Generator().manual_seed(seed)
    idx = torch.randperm(len(full), generator=g)[:train_n]
    train = Subset(full, idx.tolist())
    return (DataLoader(train, batch_size=64, shuffle=True),
            DataLoader(test, batch_size=512))


def make_model(dropout=0.0):
    # Deliberately over-parameterized for 2000 samples.
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(28 * 28, 1024), nn.ReLU(), nn.Dropout(dropout),
        nn.Linear(1024, 1024), nn.ReLU(), nn.Dropout(dropout),
        nn.Linear(1024, 10),
    )


@torch.no_grad()
def evaluate(model, loader, loss_fn):
    model.eval()
    loss, correct, n = 0.0, 0, 0
    for xb, yb in loader:
        logits = model(xb)
        loss += loss_fn(logits, yb).item() * xb.size(0)
        correct += (logits.argmax(1) == yb).sum().item()
        n += xb.size(0)
    return loss / n, correct / n


def run(tag, dropout, weight_decay, train_loader, test_loader, epochs=60):
    writer = SummaryWriter(log_dir=f"runs/overfit_{tag}")
    model = make_model(dropout)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=weight_decay)
    best_val = float("inf")
    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            opt.zero_grad(); loss_fn(model(xb), yb).backward(); opt.step()
        tr_loss, tr_acc = evaluate(model, train_loader, loss_fn)
        va_loss, va_acc = evaluate(model, test_loader, loss_fn)
        writer.add_scalar("loss/train", tr_loss, epoch)
        writer.add_scalar("loss/val", va_loss, epoch)
        writer.add_scalar("acc/train", tr_acc, epoch)
        writer.add_scalar("acc/val", va_acc, epoch)
        writer.add_scalar("gap/val_minus_train_loss", va_loss - tr_loss, epoch)
        best_val = min(best_val, va_loss)
    writer.close()
    return tr_loss, tr_acc, va_loss, va_acc


def main() -> None:
    train_loader, test_loader = small_loaders()
    print("config        train_loss  train_acc  val_loss  val_acc")
    print("-" * 56)
    trl, tra, val, vaa = run("plain", dropout=0.0, weight_decay=0.0,
                             train_loader=train_loader, test_loader=test_loader)
    print(f"plain         {trl:9.4f}  {tra:8.3f}  {val:8.4f}  {vaa:.4f}   (memorizes: train≈0, val high)")
    trl, tra, val, vaa = run("regularized", dropout=0.4, weight_decay=1e-3,
                             train_loader=train_loader, test_loader=test_loader)
    print(f"regularized   {trl:9.4f}  {tra:8.3f}  {val:8.4f}  {vaa:.4f}   (smaller gap, far better val loss)")
    print("\nOverlay loss/train & loss/val for both runs: tensorboard --logdir runs")
    print("Plain: train loss -> ~0 (train acc -> 1.0) while val loss climbs = textbook overfit.")
    print("Watch 'gap/val_minus_train_loss' — large for plain, much smaller regularized.")


if __name__ == "__main__":
    main()
