"""1-D gradient descent with full TensorBoard logging.

Minimizes L(w) = (w - 3)^2 from a far-away start, logging the loss, the parameter,
and the gradient at every step so you can watch all three converge together.

Run:
    python 02-gradient-descent-tensorboard/code/gd_1d.py --lr 0.1
    tensorboard --logdir runs        # SCALARS: loss, param/w, grad/w

Try --lr 0.01 (slow), 0.9 (oscillates), 1.05 (diverges) and compare the runs.
"""

import argparse

import torch
from torch.utils.tensorboard import SummaryWriter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lr", type=float, default=0.1, help="learning rate / step size")
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--w0", type=float, default=-8.0, help="starting parameter value")
    args = parser.parse_args()

    # One run folder per learning rate -> they appear as separate lines in TensorBoard.
    writer = SummaryWriter(log_dir=f"runs/gd1d_lr{args.lr}")

    w = torch.tensor(args.w0, requires_grad=True)
    target = 3.0

    print(f"lr={args.lr}  start w={args.w0}")
    for step in range(args.steps):
        loss = (w - target) ** 2
        loss.backward()                      # w.grad = 2*(w - 3)

        writer.add_scalar("loss", loss.item(), step)
        writer.add_scalar("param/w", w.item(), step)
        writer.add_scalar("grad/w", w.grad.item(), step)
        writer.add_scalar("lr", args.lr, step)

        with torch.no_grad():
            w -= args.lr * w.grad            # the descent step
        w.grad.zero_()

        if step % 10 == 0 or step == args.steps - 1:
            print(f"  step {step:2d}  loss={loss.item():10.4f}  w={w.item():+.4f}")

    writer.close()
    print(f"final w={w.item():.4f} (target {target}).  View: tensorboard --logdir runs")


if __name__ == "__main__":
    main()
