"""A small CNN on FashionMNIST with the full TensorBoard image toolkit.

Logs: input grid, model graph, train/test loss & accuracy, per-layer weight/grad
histograms, first-conv filter images, a color-coded prediction grid each epoch, and a
final embedding of penultimate features (the projector).

Run:
    python 05-cnn-images/code/cnn_fashion.py --epochs 5
    tensorboard --logdir runs   # SCALARS, IMAGES, HISTOGRAMS, GRAPHS, PROJECTOR

CPU is fine (a few minutes). Use --epochs 1 for a quick smoke test.
"""

import argparse

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms
from torchvision.utils import make_grid

CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
           "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),   # (16,14,14)
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),  # (32, 7, 7)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 128), nn.ReLU(),
            nn.Linear(128, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))

    def penultimate(self, x):
        """128-d features before the final layer — for the embedding projector."""
        x = self.features(x)
        x = self.classifier[0](x)            # Flatten
        x = self.classifier[2](self.classifier[1](x))  # Linear -> ReLU
        return x


def denorm(x, mean=0.286, std=0.353):
    return (x * std + mean).clamp(0, 1)


def prediction_grid(model, images, labels, device):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    model.eval()
    with torch.no_grad():
        preds = model(images.to(device)).argmax(1).cpu()
    fig, axes = plt.subplots(4, 8, figsize=(12, 6))
    for i, ax in enumerate(axes.flat):
        ax.imshow(denorm(images[i, 0]).numpy(), cmap="gray")
        ok = preds[i] == labels[i]
        ax.set_title(f"{CLASSES[preds[i]]}\n({CLASSES[labels[i]]})",
                     color="green" if ok else "red", fontsize=7)
        ax.axis("off")
    fig.tight_layout()
    return fig


@torch.no_grad()
def evaluate(model, loader, loss_fn, device):
    model.eval()
    total_loss, correct, n = 0.0, 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        logits = model(xb)
        total_loss += loss_fn(logits, yb).item() * xb.size(0)
        correct += (logits.argmax(1) == yb).sum().item()
        n += xb.size(0)
    return total_loss / n, correct / n


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--batch-size", type=int, default=128)
    args = p.parse_args()

    device = get_device()
    print(f"device: {device}")

    tf = transforms.Compose([transforms.ToTensor(),
                             transforms.Normalize((0.286,), (0.353,))])
    train_ds = datasets.FashionMNIST("data", train=True, download=True, transform=tf)
    test_ds = datasets.FashionMNIST("data", train=False, download=True, transform=tf)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=256)

    model = CNN().to(device)
    loss_fn = nn.CrossEntropyLoss()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    writer = SummaryWriter(log_dir="runs/cnn_fashion")

    # A fixed batch we reuse for the input/prediction grids so the slider is comparable.
    sample_imgs, sample_labels = next(iter(DataLoader(test_ds, batch_size=32, shuffle=True)))
    writer.add_image("inputs", make_grid(denorm(sample_imgs), nrow=8), 0)
    writer.add_graph(model, sample_imgs.to(device))

    step = 0
    for epoch in range(args.epochs):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            if step % 50 == 0:
                writer.add_scalar("loss/train", loss.item(), step)
            step += 1

        test_loss, test_acc = evaluate(model, test_loader, loss_fn, device)
        writer.add_scalar("loss/test", test_loss, epoch)
        writer.add_scalar("acc/test", test_acc, epoch)

        for name, param in model.named_parameters():
            writer.add_histogram(f"weights/{name}", param, epoch)
            if param.grad is not None:
                writer.add_histogram(f"grads/{name}", param.grad, epoch)

        # First-conv filters as images (16 filters, 1x3x3 each).
        filters = model.features[0].weight.detach().cpu()
        filters = (filters - filters.min()) / (filters.max() - filters.min() + 1e-8)
        writer.add_image("conv1_filters", make_grid(filters, nrow=8, padding=1), epoch)

        writer.add_figure("predictions", prediction_grid(model, sample_imgs, sample_labels, device), epoch)
        print(f"epoch {epoch + 1}/{args.epochs}  test_loss={test_loss:.4f}  test_acc={test_acc:.4f}")

    # Embedding projector: 256 test images -> 128-d features, colored by class.
    emb_imgs, emb_labels = next(iter(DataLoader(test_ds, batch_size=256, shuffle=True)))
    feats = model.penultimate(emb_imgs.to(device)).cpu()
    writer.add_embedding(feats, metadata=[CLASSES[i] for i in emb_labels.tolist()],
                         label_img=denorm(emb_imgs), global_step=args.epochs)

    writer.close()
    print(f"\nfinal test accuracy: {test_acc:.4f}")
    print("View: tensorboard --logdir runs  (IMAGES, PROJECTOR, HISTOGRAMS, GRAPHS)")


if __name__ == "__main__":
    main()
