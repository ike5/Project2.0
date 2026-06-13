"""Capstone training pipeline: one configurable, fully-instrumented run.

Brings together everything from the course:
  - device-agnostic (CPU/CUDA/MPS)
  - optional augmentation, dropout, weight decay, BatchNorm, LR scheduler
  - the canonical zero/backward/step loop
  - early stopping on val loss with BEST-checkpoint saving
  - TensorBoard: scalars, weight/grad histograms, input grid, prediction grid,
    model graph, embedding projector, and an add_hparams summary

Run:
    python 07-capstone/code/train.py --epochs 15 --run baseline
    python 07-capstone/code/train.py --epochs 20 --augment --dropout 0.3 \
        --weight-decay 1e-4 --scheduler cosine --run aug_reg_cosine
    tensorboard --logdir runs
"""

import argparse
import copy
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision.utils import make_grid

sys.path.insert(0, os.path.dirname(__file__))
from data import CLASSES, denormalize, get_loaders  # noqa: E402
from model import build_model, count_parameters  # noqa: E402


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@torch.no_grad()
def evaluate(model, loader, loss_fn, device):
    model.eval()
    loss, correct, n = 0.0, 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        logits = model(xb)
        loss += loss_fn(logits, yb).item() * xb.size(0)
        correct += (logits.argmax(1) == yb).sum().item()
        n += xb.size(0)
    return loss / n, correct / n


def prediction_grid(model, images, labels, device):
    model.eval()
    with torch.no_grad():
        preds = model(images.to(device)).argmax(1).cpu()
    fig, axes = plt.subplots(4, 8, figsize=(12, 6))
    for i, ax in enumerate(axes.flat):
        ax.imshow(denormalize(images[i, 0]).numpy(), cmap="gray")
        ok = preds[i] == labels[i]
        ax.set_title(f"{CLASSES[preds[i]]}\n({CLASSES[labels[i]]})",
                     color="green" if ok else "red", fontsize=7)
        ax.axis("off")
    fig.tight_layout()
    return fig


def make_scheduler(name, opt, epochs):
    if name == "cosine":
        return torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    if name == "step":
        return torch.optim.lr_scheduler.StepLR(opt, step_size=max(1, epochs // 3), gamma=0.3)
    return None


def train(config: dict) -> dict:
    device = get_device()
    print(f"device: {device}  |  run: {config['run']}")

    train_loader, test_loader, test_ds = get_loaders(
        batch_size=config["batch_size"], augment=config["augment"])

    model = build_model(config).to(device)
    print(f"parameters: {count_parameters(model):,}")
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=config["lr"],
                           weight_decay=config["weight_decay"])
    sched = make_scheduler(config["scheduler"], opt, config["epochs"])

    writer = SummaryWriter(log_dir=f"runs/{config['run']}")

    # Fixed sample batch for input/prediction grids.
    sample_imgs, sample_labels = next(iter(DataLoader(test_ds, batch_size=32, shuffle=True)))
    writer.add_image("inputs", make_grid(denormalize(sample_imgs), nrow=8), 0)
    writer.add_graph(model, sample_imgs.to(device))

    best_val_loss, best_val_acc, best_state, best_epoch, bad = float("inf"), 0.0, None, 0, 0
    step = 0
    for epoch in range(config["epochs"]):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            if step % 100 == 0:
                writer.add_scalar("loss/train_step", loss.item(), step)
            step += 1
        if sched is not None:
            sched.step()

        tr_loss, tr_acc = evaluate(model, train_loader, loss_fn, device)
        va_loss, va_acc = evaluate(model, test_loader, loss_fn, device)
        writer.add_scalar("loss/train", tr_loss, epoch)
        writer.add_scalar("loss/val", va_loss, epoch)
        writer.add_scalar("acc/train", tr_acc, epoch)
        writer.add_scalar("acc/val", va_acc, epoch)
        writer.add_scalar("lr", opt.param_groups[0]["lr"], epoch)
        for name, p in model.named_parameters():
            writer.add_histogram(f"weights/{name}", p, epoch)
            if p.grad is not None:
                writer.add_histogram(f"grads/{name}", p.grad, epoch)
        writer.add_figure("predictions", prediction_grid(model, sample_imgs, sample_labels, device), epoch)

        print(f"epoch {epoch + 1:2d}/{config['epochs']}  "
              f"train_acc={tr_acc:.4f}  val_acc={va_acc:.4f}  val_loss={va_loss:.4f}")

        if va_loss < best_val_loss - 1e-4:
            best_val_loss, best_val_acc, best_epoch = va_loss, va_acc, epoch
            best_state, bad = copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= config["patience"]:
                print(f"early stop at epoch {epoch + 1} (best epoch {best_epoch + 1})")
                break

    # Embedding projector from the BEST model.
    model.load_state_dict(best_state)
    emb_imgs, emb_labels = next(iter(DataLoader(test_ds, batch_size=256, shuffle=True)))
    feats = model.penultimate(emb_imgs.to(device)).detach().cpu()
    writer.add_embedding(feats, metadata=[CLASSES[i] for i in emb_labels.tolist()],
                         label_img=denormalize(emb_imgs), global_step=config["epochs"])

    writer.add_hparams(
        {k: config[k] for k in ("lr", "weight_decay", "dropout", "width", "augment",
                                "batchnorm", "scheduler")},
        {"hparam/val_acc": best_val_acc, "hparam/val_loss": best_val_loss},
    )
    writer.close()

    os.makedirs("checkpoints", exist_ok=True)
    ckpt = f"checkpoints/{config['run']}.pt"
    torch.save({"state_dict": best_state, "config": config,
                "best_val_acc": best_val_acc, "best_epoch": best_epoch}, ckpt)
    print(f"\nbest val acc {best_val_acc:.4f} @ epoch {best_epoch + 1}  ->  saved {ckpt}")
    print("View: tensorboard --logdir runs")
    return {"best_val_acc": best_val_acc, "checkpoint": ckpt}


def parse_args() -> dict:
    p = argparse.ArgumentParser(description="Capstone CNN training")
    p.add_argument("--run", default="baseline", help="run name (TensorBoard + checkpoint)")
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=0.0)
    p.add_argument("--dropout", type=float, default=0.0)
    p.add_argument("--width", type=int, default=32, help="base conv channel width")
    p.add_argument("--augment", action="store_true", help="train-time crop+flip augmentation")
    p.add_argument("--no-batchnorm", action="store_true")
    p.add_argument("--scheduler", choices=["none", "cosine", "step"], default="none")
    p.add_argument("--patience", type=int, default=5)
    a = p.parse_args()
    return {
        "run": a.run, "epochs": a.epochs, "batch_size": a.batch_size, "lr": a.lr,
        "weight_decay": a.weight_decay, "dropout": a.dropout, "width": a.width,
        "augment": a.augment, "batchnorm": not a.no_batchnorm, "scheduler": a.scheduler,
        "patience": a.patience, "in_channels": 1, "num_classes": 10,
    }


if __name__ == "__main__":
    train(parse_args())
