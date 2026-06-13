"""Reference solution for Challenge 01. Run:
    python 01-tensors-autograd/solutions/challenge_solution.py
"""

import torch


def task1_shape_surgery() -> None:
    print("\n[1] Shape surgery")
    x = torch.arange(24.0)
    for shape in [(2, 3, 4), (4, 6), (24, 1), (1, 2, 12)]:
        out = x.reshape(*shape)
        print(f"  -> {tuple(out.shape)}")
        assert out.numel() == 24


def task2_standardize() -> None:
    print("\n[2] Column standardization via broadcasting")
    torch.manual_seed(0)
    X = torch.randn(100, 5) * 3 + 7          # non-zero mean, non-unit std
    mean = X.mean(dim=0, keepdim=True)       # (1, 5)
    std = X.std(dim=0, keepdim=True)         # (1, 5)
    Z = (X - mean) / std                     # broadcasts over rows
    print("  col means ~", [round(m, 4) for m in Z.mean(dim=0).tolist()])
    print("  col stds  ~", [round(s, 4) for s in Z.std(dim=0).tolist()])
    assert torch.allclose(Z.mean(dim=0), torch.zeros(5), atol=1e-5)
    assert torch.allclose(Z.std(dim=0), torch.ones(5), atol=1e-2)


def task3_one_param() -> None:
    print("\n[3] f(w) = 3w^2 + 5w - 2 at w=4")
    w = torch.tensor(4.0, requires_grad=True)
    f = 3 * w ** 2 + 5 * w - 2
    f.backward()
    hand = 6 * 4 + 5                          # df/dw = 6w + 5
    print(f"  autograd={w.grad.item():.4f}  hand={hand:.4f}")
    assert abs(w.grad.item() - hand) < 1e-5


def task4_two_params() -> None:
    print("\n[4] loss = (a*b - 6)^2 at a=1, b=2")
    a = torch.tensor(1.0, requires_grad=True)
    b = torch.tensor(2.0, requires_grad=True)
    loss = (a * b - 6) ** 2
    loss.backward()
    # d/da = 2(ab-6)*b ; d/db = 2(ab-6)*a
    ga_hand = 2 * (1 * 2 - 6) * 2
    gb_hand = 2 * (1 * 2 - 6) * 1
    print(f"  a.grad={a.grad.item():.1f} (hand {ga_hand})  "
          f"b.grad={b.grad.item():.1f} (hand {gb_hand})")
    assert abs(a.grad.item() - ga_hand) < 1e-5
    assert abs(b.grad.item() - gb_hand) < 1e-5


def task5_minimize() -> None:
    print("\n[5] minimize (w-3)^2 + 2 from w=-5")
    w = torch.tensor(-5.0, requires_grad=True)
    lr = 0.1
    for _ in range(60):
        loss = (w - 3) ** 2 + 2
        loss.backward()
        with torch.no_grad():
            w -= lr * w.grad
        w.grad.zero_()
    print(f"  final w={w.item():.4f} (≈3)  final loss={loss.item():.4f} (≈2)")
    assert abs(w.item() - 3) < 1e-2
    # For (w-3)^2, update is w <- w - lr*2*(w-3) = w*(1-2lr) + 6lr.
    # Stable if |1-2lr| < 1  -> 0 < lr < 1. Oscillates (no divergence) if 0.5 < lr < 1.
    print("  diverges at lr >= 1.0 ; oscillates-but-converges for 0.5 < lr < 1.0")


def task6_no_grad() -> None:
    print("\n[6] why updates go under no_grad()")
    w = torch.tensor(1.0, requires_grad=True)
    loss = (w - 5) ** 2
    loss.backward()
    try:
        w -= 0.1 * w.grad            # in-place on a leaf requiring grad -> error
        print("  (no error on this version, but the op would be tracked)")
    except RuntimeError as e:
        print(f"  without no_grad: RuntimeError -> {str(e)[:60]}...")
    with torch.no_grad():
        w -= 0.1 * w.grad            # correct: bookkeeping, not differentiated
    print(f"  with no_grad: updated cleanly, w={w.item():.3f}")


def main() -> None:
    task1_shape_surgery()
    task2_standardize()
    task3_one_param()
    task4_two_params()
    task5_minimize()
    task6_no_grad()
    print("\nAll checks passed ✅")


if __name__ == "__main__":
    main()
