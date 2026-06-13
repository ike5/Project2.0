"""Write a simple scalar curve to TensorBoard to confirm the logging pipeline.

Run:
    python 00-setup/code/hello_tensorboard.py
    tensorboard --logdir runs        # open http://localhost:6006 -> SCALARS

You should see 'demo/sine' (a sine wave) and 'demo/linear' (a straight line).
"""

import math

from torch.utils.tensorboard import SummaryWriter


def main() -> None:
    writer = SummaryWriter(log_dir="runs/hello")

    for step in range(200):
        writer.add_scalar("demo/sine", math.sin(step / 10.0), step)
        writer.add_scalar("demo/linear", step / 200.0, step)

    writer.close()
    print("Wrote 200 steps to runs/hello.")
    print("Now run:  tensorboard --logdir runs")
    print("Open the URL it prints and look at the SCALARS tab.")


if __name__ == "__main__":
    main()
