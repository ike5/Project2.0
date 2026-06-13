"""Sweep several learning rates on the same 1-D problem, one run each.

Writes runs/sweep_lr<lr> for each value so TensorBoard overlays the loss curves.
You'll see: tiny lr crawls, good lr dives, large lr oscillates, too-large diverges.

Run:
    python 02-gradient-descent-tensorboard/code/lr_sweep.py
    tensorboard --logdir runs        # SCALARS -> compare 'loss' across runs
"""

import torch
from torch.utils.tensorboard import SummaryWriter


def run(lr: float, steps: int = 60, w0: float = -8.0) -> float:
    writer = SummaryWriter(log_dir=f"runs/sweep_lr{lr}")
    w = torch.tensor(w0, requires_grad=True)
    for step in range(steps):
        loss = (w - 3.0) ** 2
        loss.backward()
        writer.add_scalar("loss", loss.item(), step)
        writer.add_scalar("param/w", w.item(), step)
        with torch.no_grad():
            w -= lr * w.grad
        w.grad.zero_()
        if not torch.isfinite(loss):         # diverged
            break
    writer.close()
    return loss.item()


def main() -> None:
    learning_rates = [0.01, 0.1, 0.5, 0.9, 1.05]
    print("lr      final_loss   behavior")
    print("-" * 40)
    notes = {
        0.01: "slow crawl",
        0.1: "smooth, fast",
        0.5: "fast, slight overshoot",
        0.9: "oscillates, still converges",
        1.05: "DIVERGES (loss -> inf)",
    }
    for lr in learning_rates:
        final = run(lr)
        shown = "inf" if not torch.isfinite(torch.tensor(final)) else f"{final:.4f}"
        print(f"{lr:<7} {shown:<12} {notes[lr]}")
    print("\nOpen TensorBoard and overlay the 'loss' curves: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
