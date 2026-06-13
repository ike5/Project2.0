"""Compare SGD vs SGD+Momentum vs Adam on the SAME elongated bowl.

Each optimizer gets its own run and its own descent-path figure, so in TensorBoard
you can overlay their loss curves and scrub their trajectories side by side. The
elongated valley makes plain SGD zig-zag, momentum smooth it out, and Adam adapt.

Run:
    python 02-gradient-descent-tensorboard/code/optimizer_compare.py
    tensorboard --logdir runs   # SCALARS: overlay 'loss'; IMAGES: each path
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from torch.utils.tensorboard import SummaryWriter

A, B = 4.0, 0.4
C1, C2 = 3.0, -2.0


def loss_fn(w: torch.Tensor) -> torch.Tensor:
    return 0.5 * (A * (w[0] - C1) ** 2 + B * (w[1] - C2) ** 2)


def surface_grid():
    w1 = torch.linspace(-8, 8, 120)
    w2 = torch.linspace(-9, 7, 120)
    W1, W2 = torch.meshgrid(w1, w2, indexing="xy")
    Z = 0.5 * (A * (W1 - C1) ** 2 + B * (W2 - C2) ** 2)
    return W1.numpy(), W2.numpy(), Z.numpy()


def render(W1, W2, Z, path, title):
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.contour(W1, W2, Z, levels=30, linewidths=0.6)
    ax.plot([p[0] for p in path], [p[1] for p in path],
            "o-", color="red", markersize=3, linewidth=1.2)
    ax.scatter([C1], [C2], marker="*", s=200, color="gold", edgecolor="black", zorder=5)
    ax.set_title(title); ax.set_xlabel("w1"); ax.set_ylabel("w2")
    fig.tight_layout()
    return fig


def make_optimizer(name: str, w: torch.Tensor):
    # lrs tuned per optimizer so each is in a sensible regime on this bowl.
    if name == "sgd":
        return torch.optim.SGD([w], lr=0.08)               # stable but slow on the shallow axis
    if name == "momentum":
        return torch.optim.SGD([w], lr=0.06, momentum=0.9)  # accelerates the slow axis
    if name == "adam":
        return torch.optim.Adam([w], lr=0.5)                # adapts per-parameter step size
    raise ValueError(name)


def run(name: str, steps: int = 80) -> float:
    writer = SummaryWriter(log_dir=f"runs/optim_{name}")
    W1, W2, Z = surface_grid()
    w = torch.tensor([-7.0, 6.0], requires_grad=True)
    opt = make_optimizer(name, w)
    path = [(w[0].item(), w[1].item())]

    for step in range(steps):
        opt.zero_grad()
        loss = loss_fn(w)
        loss.backward()
        opt.step()
        path.append((w[0].item(), w[1].item()))
        writer.add_scalar("loss", loss.item(), step)
        writer.add_scalar("grad/norm", w.grad.norm().item(), step)
        if step % 3 == 0 or step == steps - 1:
            fig = render(W1, W2, Z, path, f"{name}  (step {step})")
            writer.add_figure("descent/path", fig, step)
            plt.close(fig)

    writer.close()
    return loss.item()


def main() -> None:
    print("optimizer   final_loss")
    print("-" * 26)
    for name in ["sgd", "momentum", "adam"]:
        final = run(name)
        print(f"{name:<11} {final:.6f}")
    print("\nCompare in TensorBoard: tensorboard --logdir runs")
    print("  SCALARS -> overlay the three 'loss' curves")
    print("  IMAGES  -> scrub each 'descent/path' (note SGD's zig-zag vs momentum's smoothing)")


if __name__ == "__main__":
    main()
