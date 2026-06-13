"""A configurable CNN for the capstone.

Knobs: base channel width, dropout probability, and whether to use BatchNorm. The
architecture is three Conv blocks (with pooling on the first two) -> a small classifier
head. `penultimate()` exposes the pre-logit features for the embedding projector.
"""

import torch.nn as nn


class CapstoneCNN(nn.Module):
    def __init__(self, in_channels: int = 1, num_classes: int = 10,
                 width: int = 32, dropout: float = 0.0, batchnorm: bool = True):
        super().__init__()

        def block(cin, cout, pool):
            layers = [nn.Conv2d(cin, cout, 3, padding=1)]
            if batchnorm:
                layers.append(nn.BatchNorm2d(cout))
            layers.append(nn.ReLU())
            if pool:
                layers.append(nn.MaxPool2d(2))
            return layers

        self.features = nn.Sequential(
            *block(in_channels, width, pool=True),    # 28 -> 14
            *block(width, width * 2, pool=True),      # 14 -> 7
            *block(width * 2, width * 2, pool=False),  # 7 -> 7
        )
        feat_dim = (width * 2) * 7 * 7
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(feat_dim, 128),
            nn.ReLU(),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        return self.classifier(self.head(self.features(x)))

    def penultimate(self, x):
        """128-d features before the final linear layer (for add_embedding)."""
        return self.head(self.features(x))


def build_model(config: dict) -> CapstoneCNN:
    return CapstoneCNN(
        in_channels=config.get("in_channels", 1),
        num_classes=config.get("num_classes", 10),
        width=config.get("width", 32),
        dropout=config.get("dropout", 0.0),
        batchnorm=config.get("batchnorm", True),
    )


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
