"""Learning-rate schedules: constant vs step-decay vs cosine annealing.

Trains the same model three ways, logging both `lr` and `loss/val` per epoch. In
TensorBoard you'll see the lr curves (flat / staircase / cosine) and how the loss takes
a fresh step down right when step-decay drops the lr.

Run:
    python 06-training-techniques/code/lr_schedule.py
    tensorboard --logdir runs   # overlay 'lr' and 'loss/val' across the three runs
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms


def loaders(train_n=6000, seed=0):
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.286,), (0.353,))])
    full = datasets.FashionMNIST("data", train=True, download=True, transform=tf)
    test = datasets.FashionMNIST("data", train=False, download=True, transform=tf)
    idx = torch.randperm(len(full), generator=torch.Generator().manual_seed(seed))[:train_n]
    return (DataLoader(Subset(full, idx.tolist()), batch_size=128, shuffle=True),
            DataLoader(test, batch_size=512))


def model():
    return nn.Sequential(
        nn.Flatten(), nn.Linear(28 * 28, 256), nn.ReLU(),
        nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 10),
    )


@torch.no_grad()
def val_loss(m, loader, loss_fn):
    m.eval()
    tot, n = 0.0, 0
    for xb, yb in loader:
        tot += loss_fn(m(xb), yb).item() * xb.size(0); n += xb.size(0)
    return tot / n


def make_sched(name, opt, epochs):
    if name == "constant":
        return None
    if name == "step":
        return torch.optim.lr_scheduler.StepLR(opt, step_size=8, gamma=0.3)
    if name == "cosine":
        return torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    raise ValueError(name)


def run(name, train_loader, test_loader, epochs=30):
    writer = SummaryWriter(log_dir=f"runs/sched_{name}")
    m = model()
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.SGD(m.parameters(), lr=0.1, momentum=0.9)
    sched = make_sched(name, opt, epochs)
    for epoch in range(epochs):
        m.train()
        for xb, yb in train_loader:
            opt.zero_grad(); loss_fn(m(xb), yb).backward(); opt.step()
        writer.add_scalar("lr", opt.param_groups[0]["lr"], epoch)
        writer.add_scalar("loss/val", val_loss(m, test_loader, loss_fn), epoch)
        if sched is not None:
            sched.step()
    final = val_loss(m, test_loader, loss_fn)
    writer.close()
    return final


def main() -> None:
    train_loader, test_loader = loaders()
    print("schedule   final val loss")
    print("-" * 28)
    for name in ["constant", "step", "cosine"]:
        f = run(name, train_loader, test_loader)
        print(f"{name:10s} {f:.4f}")
    print("\nOverlay 'lr' (flat vs staircase vs cosine) and 'loss/val': tensorboard --logdir runs")
    print("Note the loss dropping a notch right after each StepLR decay.")


if __name__ == "__main__":
    main()
