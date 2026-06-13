"""Reference solution for Challenge 06 — one reusable train(config) function with
LR scheduling, early stopping (+ best-weight restore), HParams logging, and a
save/reload check.

Run:
    python 06-training-techniques/solutions/challenge_solution.py
    tensorboard --logdir runs   # SCALARS + HPARAMS
"""

import copy
import itertools

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms


def get_loaders(train_n=4000, seed=0):
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.286,), (0.353,))])
    full = datasets.FashionMNIST("data", train=True, download=True, transform=tf)
    test = datasets.FashionMNIST("data", train=False, download=True, transform=tf)
    idx = torch.randperm(len(full), generator=torch.Generator().manual_seed(seed))[:train_n]
    return (DataLoader(Subset(full, idx.tolist()), batch_size=128, shuffle=True),
            DataLoader(test, batch_size=512))


def build_model(dropout=0.0):
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(28 * 28, 256), nn.ReLU(), nn.Dropout(dropout),
        nn.Linear(256, 128), nn.ReLU(), nn.Dropout(dropout),
        nn.Linear(128, 10),
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


def train(config, train_loader, test_loader):
    """One config in, trained model + best state + metrics out. Fully logged."""
    writer = SummaryWriter(log_dir=f"runs/chal06_{config['name']}")
    model = build_model(config.get("dropout", 0.0))
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=config["lr"],
                           weight_decay=config.get("weight_decay", 0.0))
    epochs = config.get("epochs", 40)
    sched = (torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
             if config.get("scheduler") == "cosine" else None)

    patience = config.get("patience", 6)
    best_val_loss, best_val_acc = float("inf"), 0.0
    best_state, bad_epochs, best_epoch = None, 0, 0

    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            opt.zero_grad(); loss_fn(model(xb), yb).backward(); opt.step()
        if sched is not None:
            sched.step()

        tr_loss, tr_acc = evaluate(model, train_loader, loss_fn)
        va_loss, va_acc = evaluate(model, test_loader, loss_fn)
        writer.add_scalar("loss/train", tr_loss, epoch)
        writer.add_scalar("loss/val", va_loss, epoch)
        writer.add_scalar("acc/train", tr_acc, epoch)
        writer.add_scalar("acc/val", va_acc, epoch)
        writer.add_scalar("lr", opt.param_groups[0]["lr"], epoch)

        if va_loss < best_val_loss - 1e-4:
            best_val_loss, best_val_acc, best_epoch = va_loss, va_acc, epoch
            best_state = copy.deepcopy(model.state_dict())   # snapshot the BEST weights
            bad_epochs = 0
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                print(f"  [{config['name']}] early stop at epoch {epoch} "
                      f"(best was epoch {best_epoch})")
                break

    writer.add_hparams(
        {k: config[k] for k in ("lr", "weight_decay", "dropout") if k in config},
        {"hparam/val_acc": best_val_acc, "hparam/val_loss": best_val_loss},
    )
    writer.close()
    return best_state, best_val_acc, best_val_loss, best_epoch


def main() -> None:
    train_loader, test_loader = get_loaders()

    print("== Task 2/3: baseline vs regularized vs scheduled ==")
    configs = [
        {"name": "a_baseline", "lr": 1e-3, "epochs": 40},
        {"name": "b_regularized", "lr": 1e-3, "weight_decay": 1e-3, "dropout": 0.3, "epochs": 40},
        {"name": "c_scheduled", "lr": 1e-3, "weight_decay": 1e-3, "dropout": 0.3,
         "scheduler": "cosine", "epochs": 40},
    ]
    best_overall = None
    for cfg in configs:
        state, acc, loss, ep = train(cfg, train_loader, test_loader)
        print(f"  {cfg['name']:14s} best_val_acc={acc:.4f}  best_val_loss={loss:.4f}  @epoch {ep}")
        if best_overall is None or acc > best_overall[1]:
            best_overall = (cfg["name"], acc, state)

    print("\n== Task 4: weight_decay x dropout grid (HPARAMS) ==")
    print("  wd       dropout   val_acc")
    for wd, do in itertools.product([0.0, 1e-4, 1e-3], [0.0, 0.3]):
        name = f"grid_wd{wd}_do{do}"
        _, acc, _, _ = train({"name": name, "lr": 1e-3, "weight_decay": wd,
                              "dropout": do, "epochs": 25}, train_loader, test_loader)
        print(f"  {wd:<8} {do:<9} {acc:.4f}")

    print("\n== Task 5: save / reload the best model ==")
    name, acc, state = best_overall
    torch.save(state, "best.pt")
    fresh = build_model(dropout=0.3)
    fresh.load_state_dict(torch.load("best.pt"))
    _, reloaded_acc = evaluate(fresh, test_loader, nn.CrossEntropyLoss())
    print(f"  best run: {name}  saved_acc={acc:.4f}  reloaded_acc={reloaded_acc:.4f}")
    assert abs(acc - reloaded_acc) < 1e-6, "reloaded model should match exactly"
    print("  reload matches ✅")
    print("\nView: tensorboard --logdir runs  (SCALARS + HPARAMS)")


if __name__ == "__main__":
    main()
