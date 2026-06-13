"""Look at FashionMNIST before training: a labeled image grid + class balance.

Logs a grid of examples (one labeled montage) to TensorBoard and prints per-class
counts so you know the data is balanced and correctly loaded.

Run:
    python 05-cnn-images/code/inspect_data.py
    tensorboard --logdir runs   # IMAGES -> samples
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from torchvision import datasets, transforms

CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
           "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]


def main() -> None:
    train_ds = datasets.FashionMNIST("data", train=True, download=True,
                                     transform=transforms.ToTensor())

    # Class counts (FashionMNIST is balanced: 6000 each).
    counts = torch.bincount(train_ds.targets, minlength=10)
    print("class counts:")
    for i, c in enumerate(counts.tolist()):
        print(f"  {i} {CLASSES[i]:11s} {c}")

    # One labeled example per class.
    imgs, labels = next(iter(DataLoader(train_ds, batch_size=512, shuffle=True)))
    fig, axes = plt.subplots(2, 5, figsize=(11, 5))
    for cls, ax in enumerate(axes.flat):
        i = (labels == cls).nonzero()[0].item()
        ax.imshow(imgs[i, 0].numpy(), cmap="gray")
        ax.set_title(CLASSES[cls], fontsize=9)
        ax.axis("off")
    fig.suptitle("FashionMNIST — one example per class")
    fig.tight_layout()

    writer = SummaryWriter(log_dir="runs/inspect")
    writer.add_figure("samples", fig, 0)
    writer.close()
    print("\nLogged a labeled montage. View: tensorboard --logdir runs -> IMAGES")


if __name__ == "__main__":
    main()
