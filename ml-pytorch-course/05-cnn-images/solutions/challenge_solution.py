"""Reference solution for Challenge 05 — MLP vs CNN, an improved CNN, mistake mining,
and a confusion matrix, all on FashionMNIST.

Run (a few minutes on CPU):
    python 05-cnn-images/solutions/challenge_solution.py --epochs 5
    tensorboard --logdir runs
"""

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms

CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
           "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]


def device():
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def mlp():
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(28 * 28, 256), nn.ReLU(),
        nn.Linear(256, 128), nn.ReLU(),
        nn.Linear(128, 10),
    )


def cnn_basic():
    return nn.Sequential(
        nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        nn.Flatten(), nn.Linear(32 * 7 * 7, 128), nn.ReLU(), nn.Linear(128, 10),
    )


def cnn_improved():
    # + BatchNorm after convs, a third conv block, and Dropout before the classifier.
    return nn.Sequential(
        nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),   # 14
        nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),  # 7
        nn.Conv2d(64, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),                   # 7
        nn.Flatten(), nn.Dropout(0.3),
        nn.Linear(64 * 7 * 7, 128), nn.ReLU(), nn.Dropout(0.3), nn.Linear(128, 10),
    )


def loaders(batch=128):
    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.286,), (0.353,))])
    tr = datasets.FashionMNIST("data", train=True, download=True, transform=tf)
    te = datasets.FashionMNIST("data", train=False, download=True, transform=tf)
    return (DataLoader(tr, batch_size=batch, shuffle=True),
            DataLoader(te, batch_size=256), te)


@torch.no_grad()
def evaluate(model, loader, loss_fn, dev):
    model.eval()
    loss, correct, n = 0.0, 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(dev), yb.to(dev)
        logits = model(xb)
        loss += loss_fn(logits, yb).item() * xb.size(0)
        correct += (logits.argmax(1) == yb).sum().item()
        n += xb.size(0)
    return loss / n, correct / n


def train(tag, model, tr_loader, te_loader, epochs, dev):
    writer = SummaryWriter(log_dir=f"runs/chal05_{tag}")
    model.to(dev)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    best = 0.0
    for epoch in range(epochs):
        model.train()
        for xb, yb in tr_loader:
            xb, yb = xb.to(dev), yb.to(dev)
            opt.zero_grad(); loss_fn(model(xb), yb).backward(); opt.step()
        te_loss, te_acc = evaluate(model, te_loader, loss_fn, dev)
        writer.add_scalar("loss/test", te_loss, epoch)
        writer.add_scalar("acc/test", te_acc, epoch)
        best = max(best, te_acc)
    writer.close()
    return best, model


def log_mistakes_and_confusion(tag, model, te_ds, dev):
    writer = SummaryWriter(log_dir=f"runs/chal05_{tag}")
    loader = DataLoader(te_ds, batch_size=512)
    model.eval()
    cm = torch.zeros(10, 10)
    wrong_imgs, wrong_titles = [], []
    with torch.no_grad():
        for xb, yb in loader:
            preds = model(xb.to(dev)).argmax(1).cpu()
            for t, p in zip(yb.tolist(), preds.tolist()):
                cm[t, p] += 1
            for img, t, p in zip(xb, yb.tolist(), preds.tolist()):
                if p != t and len(wrong_imgs) < 32:
                    wrong_imgs.append(img); wrong_titles.append((p, t))
    # Mistake grid.
    fig, axes = plt.subplots(4, 8, figsize=(12, 6))
    for i, ax in enumerate(axes.flat):
        if i < len(wrong_imgs):
            ax.imshow((wrong_imgs[i][0] * 0.353 + 0.286).clamp(0, 1).numpy(), cmap="gray")
            p, t = wrong_titles[i]
            ax.set_title(f"{CLASSES[p]}\n({CLASSES[t]})", color="red", fontsize=6)
        ax.axis("off")
    fig.suptitle("misclassified: pred (true)")
    fig.tight_layout(); writer.add_figure("mistakes", fig, 0); plt.close(fig)
    # Confusion matrix.
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(10)); ax.set_yticks(range(10))
    ax.set_xticklabels(CLASSES, rotation=90, fontsize=7); ax.set_yticklabels(CLASSES, fontsize=7)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    fig.tight_layout(); writer.add_figure("confusion", fig, 0); plt.close(fig)
    writer.close()
    # Most-confused off-diagonal pair.
    off = cm.clone(); off.fill_diagonal_(0)
    i, j = divmod(int(off.argmax().item()), 10)
    print(f"  most-confused: true {CLASSES[i]} -> pred {CLASSES[j]} ({int(off[i, j])} times)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=5)
    args = p.parse_args()
    dev = device()
    print(f"device: {dev}")
    tr_loader, te_loader, te_ds = loaders()

    print("\nmodel        best acc")
    print("-" * 24)
    mlp_acc, _ = train("mlp", mlp(), tr_loader, te_loader, args.epochs, dev)
    print(f"mlp          {mlp_acc:.4f}")
    cnn_acc, _ = train("cnn_basic", cnn_basic(), tr_loader, te_loader, args.epochs, dev)
    print(f"cnn_basic    {cnn_acc:.4f}")
    imp_acc, imp_model = train("cnn_improved", cnn_improved(), tr_loader, te_loader, args.epochs, dev)
    print(f"cnn_improved {imp_acc:.4f}")

    print("\nerror analysis (improved CNN):")
    log_mistakes_and_confusion("cnn_improved", imp_model, te_ds, dev)
    print("\nView: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
