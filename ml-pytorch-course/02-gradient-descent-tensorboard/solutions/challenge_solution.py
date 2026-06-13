"""Reference solution for Challenge 02 — descent on a curved (Rosenbrock-ish) valley
with full TensorBoard logging, an lr comparison, and an optimizer showdown.

Run:
    python 02-gradient-descent-tensorboard/solutions/challenge_solution.py
    tensorboard --logdir runs
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from torch.utils.tensorboard import SummaryWriter

# Rosenbrock-ish curved valley; global minimum at (1, 1) with loss 0.
def loss_fn(w: torch.Tensor) -> torch.Tensor:
    return (1 - w[0]) ** 2 + 10 * (w[1] - w[0] ** 2) ** 2


def surface_grid():
    w1 = torch.linspace(-2, 2, 200)
    w2 = torch.linspace(-1, 3, 200)
    W1, W2 = torch.meshgrid(w1, w2, indexing="xy")
    Z = (1 - W1) ** 2 + 10 * (W2 - W1 ** 2) ** 2
    return W1.numpy(), W2.numpy(), Z.numpy()


def render(W1, W2, Z, path, title):
    fig, ax = plt.subplots(figsize=(6, 5))
    # log-spaced levels: the valley spans several orders of magnitude
    ax.contour(W1, W2, Z, levels=torch.logspace(-1, 3, 30).tolist(), linewidths=0.5)
    ax.plot([p[0] for p in path], [p[1] for p in path],
            "o-", color="red", markersize=2, linewidth=1.0)
    ax.scatter([1], [1], marker="*", s=200, color="gold", edgecolor="black", zorder=5)
    ax.set_title(title); ax.set_xlabel("w1"); ax.set_ylabel("w2")
    fig.tight_layout()
    return fig


def descend(name, optimizer_factory, lr, steps=400, log_figure=True):
    writer = SummaryWriter(log_dir=f"runs/chal02_{name}")
    W1, W2, Z = surface_grid()
    w = torch.tensor([-1.5, 2.0], requires_grad=True)
    opt = optimizer_factory([w], lr)
    path = [(w[0].item(), w[1].item())]
    steps_to_thresh = None

    for step in range(steps):
        opt.zero_grad()
        loss = loss_fn(w)
        loss.backward()
        opt.step()
        path.append((w[0].item(), w[1].item()))
        writer.add_scalar("loss", loss.item(), step)
        writer.add_scalar("param/w1", w[0].item(), step)
        writer.add_scalar("param/w2", w[1].item(), step)
        writer.add_scalar("grad/norm", w.grad.norm().item(), step)
        if steps_to_thresh is None and loss.item() < 0.1:
            steps_to_thresh = step
        if log_figure and (step % 20 == 0 or step == steps - 1):
            fig = render(W1, W2, Z, path, f"{name} (step {step})")
            writer.add_figure("descent/path", fig, step)
            plt.close(fig)

    writer.close()
    return loss.item(), steps_to_thresh


def main() -> None:
    print("== Task 2: learning-rate comparison (plain SGD) ==")
    for tag, lr in [("lr_small", 0.0005), ("lr_good", 0.002), ("lr_big", 0.01)]:
        final, _ = descend(tag, torch.optim.SGD, lr, log_figure=(tag == "lr_good"))
        print(f"  {tag:9s} lr={lr:<7} final_loss={final:.4f}")
    print("  small: crawls; good: steady descent down the valley; big: bounces/diverges.")

    print("\n== Task 4: optimizer showdown ==")
    configs = [
        ("sgd", torch.optim.SGD, 0.002),
        ("momentum", lambda p, lr: torch.optim.SGD(p, lr=lr, momentum=0.9), 0.002),
        ("adam", torch.optim.Adam, 0.05),
    ]
    print("  optimizer   final_loss   steps_to_loss<0.1")
    for name, fac, lr in configs:
        final, n = descend(name, fac, lr)
        print(f"  {name:<11} {final:<12.5f} {n}")
    print("  Adam/momentum navigate the curved valley far faster than plain SGD.")

    print("\n== Task 5: hand-update == optim.SGD (identical paths) ==")
    a = torch.tensor([-1.5, 2.0], requires_grad=True)
    b = torch.tensor([-1.5, 2.0], requires_grad=True)
    opt = torch.optim.SGD([b], lr=0.002)
    same = True
    for _ in range(50):
        la = loss_fn(a); la.backward()
        with torch.no_grad():
            a -= 0.002 * a.grad
        a.grad.zero_()
        opt.zero_grad(); lb = loss_fn(b); lb.backward(); opt.step()
        if not torch.allclose(a, b, atol=1e-6):
            same = False
            break
    print(f"  trajectories identical: {same}")

    print("\nView everything: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
