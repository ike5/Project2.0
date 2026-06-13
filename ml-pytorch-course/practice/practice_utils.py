"""Shared helpers for the self-graded practice drills.

The big idea: every drill generates a FRESH, RANDOM task each time you run it, so you can
practice the same lesson over and over with different numbers/targets to "train for". The
grader holds the hidden ground truth and checks YOUR result against it — pass/fail with a
helpful message, never revealing the answer.

Typical use in a notebook:

    from practice_utils import Grader, regression_task
    task = regression_task()          # a new random line/relationship each call
    Xtr, ytr = task.train_data()      # train on this
    # ... you build & train a model ...
    task.grade(model)                 # checks your model on hidden test inputs

Re-run the task cell for a brand-new problem. Aim to pass 5+ different draws in a row.
"""

from __future__ import annotations

import random as _random

import torch


# --------------------------------------------------------------------------------------
# A tiny pass/fail grader with friendly output.
# --------------------------------------------------------------------------------------
class Grader:
    """Collects checks and prints a clear PASS/FAIL summary."""

    def __init__(self, title: str = "Check"):
        self.title = title
        self._results: list[tuple[bool, str]] = []

    def check(self, passed: bool, msg: str) -> bool:
        self._results.append((bool(passed), msg))
        mark = "✅" if passed else "❌"
        print(f"  {mark} {msg}")
        return passed

    def almost(self, actual, expected, tol, msg: str) -> bool:
        a = float(actual)
        e = float(expected)
        ok = abs(a - e) <= tol
        return self.check(ok, f"{msg}  (got {a:.4g}, want {e:.4g} ± {tol:g})")

    def at_least(self, actual, threshold, msg: str) -> bool:
        ok = float(actual) >= float(threshold)
        return self.check(ok, f"{msg}  (got {float(actual):.4g}, need ≥ {float(threshold):g})")

    def at_most(self, actual, threshold, msg: str) -> bool:
        ok = float(actual) <= float(threshold)
        return self.check(ok, f"{msg}  (got {float(actual):.4g}, need ≤ {float(threshold):g})")

    def shape(self, tensor, expected_shape, msg: str = "shape") -> bool:
        got = tuple(tensor.shape) if hasattr(tensor, "shape") else None
        ok = got == tuple(expected_shape)
        return self.check(ok, f"{msg}  (got {got}, want {tuple(expected_shape)})")

    def summary(self) -> bool:
        passed = sum(1 for ok, _ in self._results if ok)
        total = len(self._results)
        allok = passed == total and total > 0
        banner = "🎉 ALL PASSED" if allok else "🔁 NOT YET — tweak and re-run"
        print(f"\n{banner}  ({passed}/{total})  [{self.title}]")
        if not allok:
            print("   Re-run the task cell for a fresh problem once you're passing consistently.")
        return allok


def _seed():
    """A fresh, time-ish seed so each task draw differs (override by passing seed=...)."""
    return _random.randint(0, 2_000_000_000)


# --------------------------------------------------------------------------------------
# Task generators. Each holds a HIDDEN ground truth and grades your model against it.
# --------------------------------------------------------------------------------------
class _SupervisedTask:
    """Base: exposes train data; grades a model on a hidden held-out set."""

    def __init__(self, name, Xtr, ytr, Xte, yte, metric, threshold, mean=None, std=None):
        self.name = name
        self._Xtr, self._ytr = Xtr, ytr
        self._Xte, self._yte = Xte, yte
        self._metric = metric            # "rmse" (lower better) or "acc" (higher better)
        self._threshold = threshold
        self.mean, self.std = mean, std  # standardization stats, if the task is standardized

    def train_data(self):
        return self._Xtr, self._ytr

    def describe(self):
        print(f"Task: {self.name}")
        print(f"  train X: {tuple(self._Xtr.shape)}   train y: {tuple(self._ytr.shape)}")
        print(f"  goal: hidden-set {self._metric.upper()} "
              f"{'≤' if self._metric == 'rmse' else '≥'} {self._threshold}")

    @torch.no_grad()
    def grade(self, model) -> bool:
        g = Grader(self.name)
        model.eval()
        preds = model(self._Xte)
        if self._metric == "rmse":
            rmse = ((preds.reshape(self._yte.shape) - self._yte) ** 2).mean().sqrt().item()
            g.at_most(rmse, self._threshold, "held-out RMSE")
        else:  # accuracy
            acc = (preds.argmax(1) == self._yte).float().mean().item()
            g.at_least(acc, self._threshold, "held-out accuracy")
        return g.summary()


def regression_task(seed: int | None = None, n_features: int = 1,
                    noise_mult: float = 1.6) -> _SupervisedTask:
    """A random linear relationship y = X·w + b + noise. Recover it by training.

    Different w, b, feature scales, and noise each call. Train an nn.Linear (or your own)
    on train_data() and pass .grade(model). Features may be on different scales — consider
    standardizing.

    The pass threshold is set RELATIVE to the (hidden) noise floor: a perfect model's RMSE
    is ≈ the noise std, so `threshold = noise * noise_mult`. Lower `noise_mult` (toward ~1.1)
    makes a *tighter* drill that still stays achievable; the default 1.6 is forgiving.
    """
    g = torch.Generator().manual_seed(seed if seed is not None else _seed())
    w = (torch.rand(n_features, 1, generator=g) * 6 - 3)        # weights in [-3, 3]
    b = (torch.rand(1, generator=g) * 10 - 5).item()            # bias in [-5, 5]
    scales = torch.exp(torch.rand(n_features, generator=g) * 3 - 1)  # varied feature scales
    noise = 0.2 + torch.rand(1, generator=g).item()             # noise std in [0.2, 1.2]

    def gen(n):
        X = (torch.randn(n, n_features, generator=g)) * scales
        y = X @ w + b + torch.randn(n, 1, generator=g) * noise
        return X, y

    Xtr, ytr = gen(400)
    Xte, yte = gen(200)
    thr = noise * noise_mult                                    # always ≥ noise floor -> beatable
    return _SupervisedTask(f"regression (n_features={n_features})", Xtr, ytr, Xte, yte,
                           "rmse", round(thr, 3))


def classification_task(seed: int | None = None, n_classes: int | None = None,
                        threshold: float = 0.9) -> _SupervisedTask:
    """Random Gaussian 'blobs': n_classes clusters at random centers in 2-D.

    Different number of classes (2–4), centers, and spread each call. Train a classifier
    that outputs logits of shape (N, n_classes) and pass .grade(model).
    """
    import math
    g = torch.Generator().manual_seed(seed if seed is not None else _seed())
    if n_classes is None:
        n_classes = int(torch.randint(2, 5, (1,), generator=g).item())
    # Place centers evenly around a circle (+ small random rotation/jitter) so clusters are
    # reliably separable — the task is always passable, just with fresh positions each draw.
    radius = 4.0
    rot = torch.rand(1, generator=g).item() * 2 * math.pi
    angles = torch.tensor([rot + 2 * math.pi * k / n_classes for k in range(n_classes)])
    centers = torch.stack([radius * angles.cos(), radius * angles.sin()], dim=1)
    centers = centers + torch.randn(n_classes, 2, generator=g) * 0.3
    spread = 0.7 + torch.rand(1, generator=g).item() * 0.5

    def gen(per):
        Xs, ys = [], []
        for c in range(n_classes):
            Xs.append(centers[c] + torch.randn(per, 2, generator=g) * spread)
            ys.append(torch.full((per,), c))
        X = torch.cat(Xs); y = torch.cat(ys).long()
        perm = torch.randperm(X.shape[0], generator=g)
        return X[perm], y[perm]

    Xtr, ytr = gen(200)
    Xte, yte = gen(100)
    return _SupervisedTask(f"classification ({n_classes} classes)", Xtr, ytr, Xte, yte,
                           "acc", threshold)


def moons_task(seed: int | None = None, threshold: float = 0.9) -> _SupervisedTask:
    """Two interleaving half-moons with random noise/rotation — needs a non-linear model."""
    import math
    g = torch.Generator().manual_seed(seed if seed is not None else _seed())
    noise = 0.12 + torch.rand(1, generator=g).item() * 0.12
    rot = torch.rand(1, generator=g).item() * math.pi

    def gen(n):
        half = n // 2
        t0 = torch.linspace(0, math.pi, half)
        a = torch.stack([t0.cos(), t0.sin()], 1)
        t1 = torch.linspace(0, math.pi, n - half)
        b = torch.stack([1 - t1.cos(), 0.5 - t1.sin()], 1)
        X = torch.cat([a, b]) + torch.randn(n, 2, generator=g) * noise
        c, s = math.cos(rot), math.sin(rot)
        R = torch.tensor([[c, -s], [s, c]])
        X = X @ R.T
        y = torch.cat([torch.zeros(half), torch.ones(n - half)]).long()
        perm = torch.randperm(X.shape[0], generator=g)
        return X[perm], y[perm]

    Xtr, ytr = gen(800)
    Xte, yte = gen(400)
    return _SupervisedTask("two-moons", Xtr, ytr, Xte, yte, "acc", threshold)


# --------------------------------------------------------------------------------------
# Function-fitting / optimization drills (no dataset; minimize a hidden function).
# --------------------------------------------------------------------------------------
class _QuadraticTask:
    """Minimize f(w) = a·(w - c)^2 + d for hidden random a>0, c, d. Reach the minimizer c."""

    def __init__(self, seed=None, dim=1):
        g = torch.Generator().manual_seed(seed if seed is not None else _seed())
        self.dim = dim
        self.a = (0.5 + torch.rand(dim, generator=g) * 4)         # curvature > 0
        self.c = (torch.rand(dim, generator=g) * 10 - 5)          # minimizer in [-5,5]
        self.d = (torch.rand(1, generator=g) * 4 - 2).item()
        self.start = (torch.rand(dim, generator=g) * 16 - 8)      # random far start

    def loss(self, w: torch.Tensor) -> torch.Tensor:
        return (self.a * (w - self.c) ** 2).sum() + self.d

    def describe(self):
        print(f"Minimize a {self.dim}-D quadratic with a HIDDEN minimizer.")
        print(f"  start from w0 = {self.start.tolist()}")
        print(f"  goal: reach the minimizer (||w - c|| small). Use .loss(w) and autograd.")

    def grade(self, w_final: torch.Tensor) -> bool:
        g = Grader("quadratic minimization")
        dist = (w_final.detach().reshape(self.dim) - self.c).norm().item()
        g.at_most(dist, 0.05, "distance to the true minimizer ||w - c||")
        return g.summary()


def quadratic_task(seed: int | None = None, dim: int = 1) -> _QuadraticTask:
    return _QuadraticTask(seed=seed, dim=dim)


# --------------------------------------------------------------------------------------
# Pure-tensor drills: the grader knows the right answer and checks your variable.
# --------------------------------------------------------------------------------------
def random_shape_target(seed: int | None = None):
    """Return (source_tensor, target_shape). Reshape source -> target_shape."""
    g = torch.Generator().manual_seed(seed if seed is not None else _seed())
    factns = [(2, 3, 4), (4, 6), (3, 8), (2, 12), (6, 4), (1, 24), (24, 1), (2, 2, 6)]
    target = factns[int(torch.randint(0, len(factns), (1,), generator=g).item())]
    src = torch.arange(24.0)
    return src, target


def random_poly(seed: int | None = None):
    """Return (coeffs, x0). You compute df/dx at x0 for f(x)=sum coeffs[i]*x^i; grader checks."""
    g = torch.Generator().manual_seed(seed if seed is not None else _seed())
    coeffs = (torch.randint(-4, 5, (4,), generator=g)).float().tolist()  # cubic
    x0 = (torch.rand(1, generator=g) * 6 - 3).item()
    return coeffs, round(x0, 3)


def grade_derivative(coeffs, x0, student_grad) -> bool:
    """Check a student's df/dx at x0 for f(x) = c0 + c1 x + c2 x^2 + c3 x^3."""
    g = Grader("derivative")
    true = coeffs[1] + 2 * coeffs[2] * x0 + 3 * coeffs[3] * x0 ** 2
    g.almost(student_grad, true, 1e-2, "df/dx at x0")
    return g.summary()


# --------------------------------------------------------------------------------------
# Image tasks: a RANDOM subset of FashionMNIST classes, relabeled 0..k-1. Different
# classes (and difficulty) each draw — great for repeated CNN / training-technique practice.
# --------------------------------------------------------------------------------------
_FASHION_NAMES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
                  "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]


class _ImageSubsetTask:
    def __init__(self, name, train_loader, test_loader, n_classes, threshold, chosen):
        self.name = name
        self._train_loader = train_loader
        self._test_loader = test_loader
        self.n_classes = n_classes
        self._threshold = threshold
        self.chosen_class_names = chosen

    def loaders(self):
        return self._train_loader, self._test_loader

    def describe(self):
        print(f"Task: {self.name}")
        print(f"  classes (relabeled 0..{self.n_classes - 1}): {self.chosen_class_names}")
        print(f"  build a model whose output is logits of shape (N, {self.n_classes}).")
        print(f"  goal: hidden test accuracy ≥ {self._threshold}")

    @torch.no_grad()
    def grade(self, model, device: str = "cpu") -> bool:
        g = Grader(self.name)
        model.eval()
        correct, total = 0, 0
        for xb, yb in self._test_loader:
            xb, yb = xb.to(device), yb.to(device)
            preds = model(xb).argmax(1)
            correct += (preds == yb).sum().item()
            total += yb.size(0)
        g.at_least(correct / total, self._threshold, "held-out test accuracy")
        return g.summary()


def fashion_subset_task(seed: int | None = None, k: int | None = None,
                        train_per_class: int = 800, threshold: float = 0.82,
                        batch_size: int = 64) -> _ImageSubsetTask:
    """Pick k random FashionMNIST classes, relabel 0..k-1, return train/test loaders + grader.

    Downloads FashionMNIST to ./data on first use. Each draw is a different set of classes
    (and thus a different difficulty), so you practice building & training a CNN repeatedly.
    """
    from torch.utils.data import DataLoader, TensorDataset
    from torchvision import datasets, transforms

    g = torch.Generator().manual_seed(seed if seed is not None else _seed())
    if k is None:
        k = int(torch.randint(3, 6, (1,), generator=g).item())
    chosen = torch.randperm(10, generator=g)[:k].tolist()
    names = [_FASHION_NAMES[c] for c in chosen]

    tf = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.286,), (0.353,))])
    train = datasets.FashionMNIST("data", train=True, download=True, transform=tf)
    test = datasets.FashionMNIST("data", train=False, download=True, transform=tf)

    def subset(ds, per_class):
        xs, ys = [], []
        for new_label, orig in enumerate(chosen):
            idx = (ds.targets == orig).nonzero().flatten()
            idx = idx[torch.randperm(idx.numel(), generator=g)[:per_class]]
            imgs = torch.stack([ds[i][0] for i in idx.tolist()])
            xs.append(imgs)
            ys.append(torch.full((imgs.size(0),), new_label))
        X = torch.cat(xs); y = torch.cat(ys).long()
        perm = torch.randperm(X.size(0), generator=g)
        return TensorDataset(X[perm], y[perm])

    train_ds = subset(train, train_per_class)
    test_ds = subset(test, 300)
    return _ImageSubsetTask(
        f"FashionMNIST subset ({k} classes)",
        DataLoader(train_ds, batch_size=batch_size, shuffle=True),
        DataLoader(test_ds, batch_size=256),
        k, threshold, names,
    )
