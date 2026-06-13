"""Autograd: let PyTorch compute derivatives, and check them against hand math.

Run:
    python 01-tensors-autograd/code/autograd_basics.py

Shows: a scalar derivative, a gradient vector, gradient accumulation (and why you
must zero it), and a tiny by-hand gradient-descent loop on a vector parameter.
"""

import torch


def section(title: str) -> None:
    print("\n" + "-" * 56)
    print(title)
    print("-" * 56)


def main() -> None:
    section("1. Scalar derivative: y = x^3 + 2x")
    x = torch.tensor(2.0, requires_grad=True)
    y = x ** 3 + 2 * x
    y.backward()
    print(f"autograd dy/dx at x=2 : {x.grad.item():.1f}")
    print(f"hand     3x^2 + 2     : {3 * 2 ** 2 + 2:.1f}   (should match)")

    section("2. Gradient vector: loss = sum(w_i^2)")
    w = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
    loss = (w ** 2).sum()
    loss.backward()
    print("autograd grad :", w.grad.tolist())
    print("hand   2*w    :", (2 * w).detach().tolist(), "  (should match)")

    section("3. Gradients ACCUMULATE — you must zero them")
    p = torch.tensor(1.0, requires_grad=True)
    for i in range(3):
        loss = p * 2          # d/dp = 2 each time
        loss.backward()
        print(f"after backward #{i + 1}, p.grad = {p.grad.item():.0f}  (adds up!)")
    p.grad.zero_()
    print("after zero_(), p.grad =", p.grad.item())

    section("4. By-hand gradient descent on a vector")
    w = torch.zeros(3, requires_grad=True)
    target = torch.tensor([1.0, 2.0, 3.0])
    lr = 0.3
    for step in range(50):
        loss = ((w - target) ** 2).mean()
        loss.backward()
        with torch.no_grad():          # updating params is not part of the graph
            w -= lr * w.grad
        w.grad.zero_()                 # clear for the next step
        if step % 10 == 0 or step == 49:
            print(f"step {step:2d}  loss={loss.item():.5f}  w={w.detach().tolist()}")
    print("converged to ~", [round(v, 3) for v in w.detach().tolist()], "(target [1,2,3])")


if __name__ == "__main__":
    main()
