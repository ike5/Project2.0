"""Data loaders for the capstone, with optional train-time augmentation.

FashionMNIST, normalized with its dataset statistics. Augmentation (random crop with
padding + horizontal flip) is applied to TRAINING data only — never to validation/test.
"""

import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

MEAN, STD = 0.286, 0.353
CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
           "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]


def build_transforms(augment: bool):
    eval_tf = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((MEAN,), (STD,)),
    ])
    if not augment:
        return eval_tf, eval_tf
    train_tf = transforms.Compose([
        transforms.RandomCrop(28, padding=2),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((MEAN,), (STD,)),
    ])
    return train_tf, eval_tf


def get_loaders(batch_size: int = 128, augment: bool = False, num_workers: int = 0):
    train_tf, eval_tf = build_transforms(augment)
    train_ds = datasets.FashionMNIST("data", train=True, download=True, transform=train_tf)
    test_ds = datasets.FashionMNIST("data", train=False, download=True, transform=eval_tf)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=256, num_workers=num_workers)
    # A separate, un-augmented view of test data for image/embedding logging.
    return train_loader, test_loader, test_ds


def denormalize(x: torch.Tensor) -> torch.Tensor:
    """Undo Normalize for display (so logged images look natural)."""
    return (x * STD + MEAN).clamp(0, 1)
