"""Evaluate a saved capstone checkpoint: test accuracy, confusion matrix, worst mistakes.

Run:
    python 07-capstone/code/evaluate.py --checkpoint checkpoints/baseline.pt --run eval_baseline
    tensorboard --logdir runs   # IMAGES -> confusion, mistakes
"""

import argparse
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

sys.path.insert(0, os.path.dirname(__file__))
from data import CLASSES, denormalize, get_loaders  # noqa: E402
from model import build_model  # noqa: E402


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def confusion_figure(cm):
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, cmap="Blues")
    fig.colorbar(im, ax=ax, fraction=0.046)
    ax.set_xticks(range(10)); ax.set_yticks(range(10))
    ax.set_xticklabels(CLASSES, rotation=90, fontsize=7)
    ax.set_yticklabels(CLASSES, fontsize=7)
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title("Confusion matrix (test)")
    fig.tight_layout()
    return fig


def mistakes_figure(imgs, titles):
    fig, axes = plt.subplots(4, 8, figsize=(12, 6))
    for i, ax in enumerate(axes.flat):
        if i < len(imgs):
            ax.imshow(denormalize(imgs[i][0]).numpy(), cmap="gray")
            p, t, conf = titles[i]
            ax.set_title(f"{CLASSES[p]} ({conf:.0%})\ntrue {CLASSES[t]}", color="red", fontsize=6)
        ax.axis("off")
    fig.suptitle("Most-confident mistakes: pred (confidence) / true")
    fig.tight_layout()
    return fig


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--run", default="eval")
    args = p.parse_args()

    device = get_device()
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    model = build_model(ckpt["config"]).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    print(f"loaded {args.checkpoint}  (val acc at save: {ckpt['best_val_acc']:.4f})")

    _, test_loader, _ = get_loaders(augment=False)

    cm = torch.zeros(10, 10)
    correct, total = 0, 0
    worst = []  # (confidence, image, pred, true) for wrong, confident predictions
    with torch.no_grad():
        for xb, yb in test_loader:
            logits = model(xb.to(device))
            probs = logits.softmax(1).cpu()
            preds = probs.argmax(1)
            conf = probs.max(1).values
            correct += (preds == yb).sum().item(); total += yb.size(0)
            for i in range(yb.size(0)):
                cm[yb[i], preds[i]] += 1
                if preds[i] != yb[i]:
                    worst.append((conf[i].item(), xb[i].cpu(), preds[i].item(), yb[i].item()))

    test_acc = correct / total
    print(f"TEST ACCURACY: {test_acc:.4f}  ({correct}/{total})")

    # Per-class accuracy.
    print("\nper-class accuracy:")
    for c in range(10):
        acc_c = cm[c, c].item() / cm[c].sum().item()
        print(f"  {CLASSES[c]:11s} {acc_c:.3f}")

    # Most-confused pair.
    off = cm.clone(); off.fill_diagonal_(0)
    i, j = divmod(int(off.argmax().item()), 10)
    print(f"\nmost-confused: true {CLASSES[i]} -> pred {CLASSES[j]} ({int(off[i, j])} cases)")

    writer = SummaryWriter(log_dir=f"runs/{args.run}")
    writer.add_scalar("test/accuracy", test_acc, 0)
    writer.add_figure("confusion", confusion_figure(cm), 0)
    worst.sort(key=lambda t: -t[0])               # most confident wrong first
    imgs = [w[1] for w in worst[:32]]
    titles = [(w[2], w[3], w[0]) for w in worst[:32]]
    writer.add_figure("mistakes", mistakes_figure(imgs, titles), 0)
    writer.close()
    print(f"\nLogged confusion + mistakes. View: tensorboard --logdir runs -> IMAGES")


if __name__ == "__main__":
    main()
