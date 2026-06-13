"""Why feature scaling matters: the SAME model trains far faster on standardized inputs.

We build a regression where x lives on a large scale (~thousands). Unscaled, the loss
surface is ill-conditioned and SGD crawls (or needs a tiny lr to avoid diverging).
Standardized to mean 0 / std 1, the same lr converges quickly. Compare the two runs'
loss curves in TensorBoard.

Run:
    python 03-linear-regression/code/feature_scaling.py
    tensorboard --logdir runs    # overlay loss for runs scaling_raw vs scaling_standardized
"""

import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter


def make_data(n: int = 500, seed: int = 0):
    torch.manual_seed(seed)
    x = torch.rand(n, 1) * 4000 + 1000       # x in [1000, 5000): a large, offset scale
    y = 0.05 * x - 30 + torch.randn(n, 1) * 5
    return x, y


def train(tag: str, x: torch.Tensor, y: torch.Tensor, lr: float, epochs: int = 100) -> float:
    writer = SummaryWriter(log_dir=f"runs/scaling_{tag}")
    model = nn.Linear(1, 1)
    loss_fn = nn.MSELoss()
    opt = torch.optim.SGD(model.parameters(), lr=lr)
    for epoch in range(epochs):
        opt.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        opt.step()
        writer.add_scalar("loss", loss.item(), epoch)
        if not torch.isfinite(loss):
            break
    writer.close()
    return loss.item()


def main() -> None:
    x, y = make_data()

    # Standardize x (and we'll standardize y too so the lr comparison is apples-to-apples).
    x_std = (x - x.mean()) / x.std()
    y_std = (y - y.mean()) / y.std()

    # Unscaled needs a microscopic lr or it diverges; even then it barely moves.
    raw_final = train("raw", x, y, lr=1e-8)
    std_final = train("standardized", x_std, y_std, lr=0.1)

    print(f"raw (lr=1e-8)          final loss: {raw_final:.4f}  (still huge / crawling)")
    print(f"standardized (lr=0.1)  final loss: {std_final:.6f}  (converged)")
    print("\nLesson: standardize features so the loss surface is a round bowl, not a"
          " narrow ravine. Overlay the two 'loss' curves: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
