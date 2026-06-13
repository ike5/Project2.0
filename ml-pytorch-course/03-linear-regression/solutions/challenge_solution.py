"""Reference solution for Challenge 03 — multiple linear regression with scaling,
weight recovery, an optimizer study, and residual histograms.

We standardize BOTH the features X and the target y. Standardizing the target as well
keeps gradients well-scaled, so every optimizer behaves at normal learning rates (with
huge raw targets, Adam in particular needs an awkwardly large lr). We then de-standardize
the learned weights back to the original feature scale to compare with the true values.

Run:
    python 03-linear-regression/solutions/challenge_solution.py
    tensorboard --logdir runs
"""

import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter

TRUE_W = torch.tensor([[1.5], [-2.0], [0.5]])   # (3,1)
TRUE_B = 4.0


def make_data(n: int = 800, seed: int = 0):
    torch.manual_seed(seed)
    x1 = torch.rand(n, 1)                 # [0,1]
    x2 = torch.rand(n, 1) * 100           # [0,100]
    x3 = torch.rand(n, 1) * 20 - 10       # [-10,10]
    X = torch.cat([x1, x2, x3], dim=1)    # (n,3) — wildly different scales
    y = X @ TRUE_W + TRUE_B + torch.randn(n, 1) * 0.5
    return X, y


def train(tag, X, y, lr, opt_name="sgd", epochs=300, log_resid=False):
    writer = SummaryWriter(log_dir=f"runs/chal03_{tag}")
    n = X.shape[0]
    idx = torch.randperm(n, generator=torch.Generator().manual_seed(0))
    tr, va = idx[: int(0.8 * n)], idx[int(0.8 * n):]

    model = nn.Linear(X.shape[1], 1)
    loss_fn = nn.MSELoss()
    opt = (torch.optim.Adam if opt_name == "adam" else torch.optim.SGD)(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model(X[tr]), y[tr])
        loss.backward()
        opt.step()
        model.eval()
        with torch.no_grad():
            val = loss_fn(model(X[va]), y[va]).item()
            writer.add_scalar("loss/train", loss.item(), epoch)
            writer.add_scalar("loss/val", val, epoch)
            if log_resid and (epoch % 15 == 0):
                writer.add_histogram("residuals", (model(X[va]) - y[va]).flatten(), epoch)
        if not torch.isfinite(loss):
            break
    writer.close()
    return model, loss.item()


def main() -> None:
    X, y = make_data()
    mx, sx = X.mean(0, keepdim=True), X.std(0, keepdim=True)
    my, sy = y.mean(), y.std()
    Xs, ys = (X - mx) / sx, (y - my) / sy

    print("== Tasks 1-4: standardized vs raw features (same lr=0.05) ==")
    model_s, ls = train("standardized", Xs, ys, lr=0.05, log_resid=True)
    _, lraw = train("raw", X, y, lr=0.05)   # unscaled X & y -> diverges at same lr
    print(f"  standardized final train loss: {ls:.6f}")
    print(f"  raw          final train loss: {lraw:.4f}  (diverges/huge at same lr)")

    # Recover original-scale weights from the fully standardized model.
    #   ys = Xs·w_s + b_s,  ys=(y-my)/sy,  Xs=(X-mx)/sx
    #   => w_orig = w_s · sy / sx ,  b_orig = my + sy·b_s − Σ w_orig·mx
    w_s = model_s.weight.detach().flatten()
    b_s = model_s.bias.item()
    w_orig = w_s * sy / sx.flatten()
    b_orig = my + sy * b_s - (w_orig * mx.flatten()).sum()
    print("\n== Task 3: recovered weights (original scale) ==")
    print("  learned:", [round(v, 3) for v in w_orig.tolist()], f"bias={b_orig.item():.3f}")
    print("  true   :", TRUE_W.flatten().tolist(), f"bias={TRUE_B}")

    print("\n== Task 5: optimizer / lr study (fully standardized) ==")
    for tag, opt_name, lr in [("sgd_0.05", "sgd", 0.05),
                              ("sgd_0.2", "sgd", 0.2),
                              ("adam_0.1", "adam", 0.1)]:
        _, final = train(tag, Xs, ys, lr=lr, opt_name=opt_name)
        print(f"  {tag:10s} final train loss: {final:.6f}")
    print("  All converge here; overlay loss/val — SGD(0.2) and Adam(0.1) reach the floor"
          " in the fewest epochs.")
    print("\nView: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
