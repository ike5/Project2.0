"""2-D gradient descent visualized as a path crawling across a loss surface.

The loss is a tilted, elongated bowl in two parameters (w1, w2). We log:
  - the scalar loss and each parameter over steps (SCALARS tab)
  - a contour map of the surface with the descent path drawn on it (IMAGES tab),
    re-rendered every few steps so the step-slider scrubs the ball into the valley.

Run:
    python 02-gradient-descent-tensorboard/code/gd_surface.py --lr 0.08
    tensorboard --logdir runs        # IMAGES -> descent/path ; SCALARS -> loss

The elongation makes plain GD zig-zag — great motivation for momentum (next script).
"""

import argparse

import matplotlib

matplotlib.use("Agg")  # headless backend: render figures without a display
import matplotlib.pyplot as plt
import torch
from torch.utils.tensorboard import SummaryWriter

# An ill-conditioned quadratic bowl: steep in w1, shallow in w2. The mismatch makes
# plain gradient descent ZIG-ZAG across the narrow axis while crawling down the long one.
#   L(w) = 0.5 * (a*(w1 - c1)^2 + b*(w2 - c2)^2)
A, B = 20.0, 1.0         # curvatures: very steep in w1, shallow in w2 (condition number 20)
C1, C2 = 3.0, -2.0       # the true minimum (w1*, w2*)


def loss_fn(w: torch.Tensor) -> torch.Tensor:
    return 0.5 * (A * (w[0] - C1) ** 2 + B * (w[1] - C2) ** 2)


def surface_grid():
    w1 = torch.linspace(-8, 8, 120)
    w2 = torch.linspace(-9, 7, 120)
    W1, W2 = torch.meshgrid(w1, w2, indexing="xy")
    Z = 0.5 * (A * (W1 - C1) ** 2 + B * (W2 - C2) ** 2)
    return W1.numpy(), W2.numpy(), Z.numpy()


def render_path(W1, W2, Z, path):
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.contour(W1, W2, Z, levels=30, linewidths=0.6)
    px = [p[0] for p in path]
    py = [p[1] for p in path]
    ax.plot(px, py, "o-", color="red", markersize=3, linewidth=1.2, label="descent path")
    ax.scatter([C1], [C2], marker="*", s=200, color="gold",
               edgecolor="black", zorder=5, label="minimum")
    ax.scatter([px[0]], [py[0]], color="blue", zorder=5, label="start")
    ax.set_xlabel("w1"); ax.set_ylabel("w2")
    ax.set_title(f"Gradient descent path ({len(path)} steps)")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    return fig


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lr", type=float, default=0.09,
                        help="0.09 zig-zags toward the min; ~0.03 is smooth-but-slow; >0.1 diverges")
    parser.add_argument("--steps", type=int, default=50)
    args = parser.parse_args()

    writer = SummaryWriter(log_dir=f"runs/surface_lr{args.lr}")
    W1, W2, Z = surface_grid()

    w = torch.tensor([-7.0, 6.0], requires_grad=True)   # start far from the minimum
    path = [(w[0].item(), w[1].item())]

    for step in range(args.steps):
        loss = loss_fn(w)
        loss.backward()

        writer.add_scalar("loss", loss.item(), step)
        writer.add_scalar("param/w1", w[0].item(), step)
        writer.add_scalar("param/w2", w[1].item(), step)
        writer.add_scalar("grad/norm", w.grad.norm().item(), step)

        with torch.no_grad():
            w -= args.lr * w.grad
        w.grad.zero_()
        path.append((w[0].item(), w[1].item()))

        # Re-render the path every few steps; the IMAGES step-slider animates it.
        if step % 2 == 0 or step == args.steps - 1:
            fig = render_path(W1, W2, Z, path)
            writer.add_figure("descent/path", fig, step)
            plt.close(fig)

    writer.close()
    print(f"final w = ({w[0].item():.3f}, {w[1].item():.3f})  target = ({C1}, {C2})")
    print("View the trajectory: tensorboard --logdir runs  -> IMAGES -> descent/path")


if __name__ == "__main__":
    main()
