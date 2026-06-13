"""A self-contained two-moons dataset generator (no scikit-learn needed).

Two interleaving half circles with Gaussian noise — a classic non-linearly-separable
binary classification toy problem. Returns float32 features (N,2) and int64 labels (N,).
"""

import math

import torch


def make_moons(n: int = 1000, noise: float = 0.2, seed: int = 0):
    torch.manual_seed(seed)
    n_out = n // 2
    n_in = n - n_out

    # Outer moon (class 0): upper half circle.
    t_out = torch.linspace(0, math.pi, n_out)
    x_out = torch.stack([t_out.cos(), t_out.sin()], dim=1)

    # Inner moon (class 1): lower half circle, shifted right and down.
    t_in = torch.linspace(0, math.pi, n_in)
    x_in = torch.stack([1 - t_in.cos(), 0.5 - t_in.sin()], dim=1)

    X = torch.cat([x_out, x_in], dim=0)
    X = X + torch.randn_like(X) * noise
    y = torch.cat([torch.zeros(n_out), torch.ones(n_in)]).long()

    # Shuffle.
    perm = torch.randperm(n)
    return X[perm], y[perm]


def split(X, y, frac_train: float = 0.8, seed: int = 0):
    n = X.shape[0]
    idx = torch.randperm(n, generator=torch.Generator().manual_seed(seed))
    k = int(frac_train * n)
    tr, va = idx[:k], idx[k:]
    return X[tr], y[tr], X[va], y[va]
