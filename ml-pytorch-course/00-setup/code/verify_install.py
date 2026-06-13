"""Verify the course environment: versions, compute device, and a live autograd check.

Run:
    python 00-setup/code/verify_install.py

Expected: version lines, a "Using device: ..." line, and "autograd OK".
"""

import torch


def pick_device() -> str:
    """Return the best available device, preferring GPU but always working on CPU."""
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> None:
    print("=" * 48)
    print("PyTorch environment check")
    print("=" * 48)
    print(f"torch        : {torch.__version__}")

    # torchvision / tensorboard are optional to *import* here but required for the course.
    try:
        import torchvision

        print(f"torchvision  : {torchvision.__version__}")
    except Exception as e:  # pragma: no cover - informational
        print(f"torchvision  : NOT INSTALLED ({e})")

    try:
        import tensorboard

        print(f"tensorboard  : {tensorboard.__version__}")
    except Exception as e:  # pragma: no cover - informational
        print(f"tensorboard  : NOT INSTALLED ({e})")

    device = pick_device()
    print(f"\nUsing device : {device}")
    print(f"cuda avail   : {torch.cuda.is_available()}")
    mps = getattr(torch.backends, "mps", None)
    print(f"mps  avail   : {bool(mps) and torch.backends.mps.is_available()}")

    # A tiny end-to-end autograd check on the chosen device.
    w = torch.tensor(0.0, requires_grad=True, device=device)
    loss = (w - 3.0) ** 2          # minimized at w = 3; d/dw = 2*(w-3) = -6 at w=0
    loss.backward()
    grad = w.grad.item()
    assert abs(grad - (-6.0)) < 1e-5, f"unexpected gradient {grad}"
    print(f"\nautograd check: d/dw (w-3)^2 at w=0  ->  {grad:+.1f}  (expected -6.0)")
    print("autograd OK ✅")
    print("\nEnvironment looks good. On to Module 01!")


if __name__ == "__main__":
    main()
