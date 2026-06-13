"""Linear regression, the full PyTorch way, with TensorBoard instrumentation.

Generates noisy data from a known line y = TRUE_W*x + TRUE_B, then trains an
nn.Linear to recover the parameters. Logs train/val loss, the learned w & b, the
model graph, and a fitted-line figure each epoch (scrub it in the IMAGES tab).

Run:
    python 03-linear-regression/code/linreg.py
    tensorboard --logdir runs    # SCALARS: loss + params ; IMAGES: fit/line
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split
from torch.utils.tensorboard import SummaryWriter

TRUE_W, TRUE_B = 2.5, -1.0


def make_data(n: int = 400, seed: int = 0):
    torch.manual_seed(seed)
    x = torch.rand(n, 1) * 10 - 5            # x in [-5, 5)
    y = TRUE_W * x + TRUE_B + torch.randn(n, 1) * 1.5   # add noise
    return x, y


class LinReg(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(1, 1)
    def forward(self, x):
        return self.linear(x)


def fit_figure(model, x, y):
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(x.numpy(), y.numpy(), s=8, alpha=0.4, label="data")
    xs = torch.linspace(-5, 5, 50).reshape(-1, 1)
    with torch.no_grad():
        ax.plot(xs.numpy(), model(xs).numpy(), color="red", linewidth=2, label="model")
    ax.plot(xs.numpy(), (TRUE_W * xs + TRUE_B).numpy(), "--", color="green",
            linewidth=1, label="true line")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.legend(); ax.set_ylim(-18, 16)
    fig.tight_layout()
    return fig


def main() -> None:
    x, y = make_data()
    ds = TensorDataset(x, y)
    train_ds, val_ds = random_split(ds, [0.8, 0.2],
                                    generator=torch.Generator().manual_seed(0))
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64)

    model = LinReg()
    loss_fn = nn.MSELoss()
    opt = torch.optim.SGD(model.parameters(), lr=0.02)

    writer = SummaryWriter(log_dir="runs/linreg")
    writer.add_graph(model, x[:1])           # log the model structure

    epochs = 60
    for epoch in range(epochs):
        model.train()
        for xb, yb in train_loader:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            val_loss = sum(loss_fn(model(xb), yb).item() for xb, yb in val_loader) / len(val_loader)
            train_loss = sum(loss_fn(model(xb), yb).item() for xb, yb in train_loader) / len(train_loader)

        w = model.linear.weight.item()
        b = model.linear.bias.item()
        writer.add_scalar("loss/train", train_loss, epoch)
        writer.add_scalar("loss/val", val_loss, epoch)
        writer.add_scalar("params/w", w, epoch)
        writer.add_scalar("params/b", b, epoch)
        if epoch % 5 == 0 or epoch == epochs - 1:
            writer.add_figure("fit/line", fit_figure(model, x, y), epoch)
            print(f"epoch {epoch:2d}  train={train_loss:6.3f}  val={val_loss:6.3f}  "
                  f"w={w:+.3f}  b={b:+.3f}")

    writer.close()
    print(f"\nlearned w={w:.3f} (true {TRUE_W})  b={b:.3f} (true {TRUE_B})")
    print("View: tensorboard --logdir runs  -> IMAGES -> fit/line (scrub the slider)")


if __name__ == "__main__":
    main()
