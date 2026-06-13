"""Tensor fundamentals: shapes, reshaping, broadcasting, reductions, matmul.

Run:
    python 01-tensors-autograd/code/tensor_basics.py

Each section prints what it does and the resulting shape so you can connect
operations to the shapes they produce.
"""

import torch


def section(title: str) -> None:
    print("\n" + "-" * 56)
    print(title)
    print("-" * 56)


def main() -> None:
    torch.manual_seed(0)

    section("1. Ranks: scalar / vector / matrix / batch")
    s = torch.tensor(3.14)
    v = torch.tensor([1.0, 2.0, 3.0])
    M = torch.arange(6.0).reshape(2, 3)
    batch = torch.randn(32, 3, 28, 28)  # (N, C, H, W)
    for name, t in [("scalar", s), ("vector", v), ("matrix", M), ("img batch", batch)]:
        print(f"{name:10s} shape={tuple(t.shape)}  ndim={t.ndim}  dtype={t.dtype}")

    section("2. Reshaping (no data copied)")
    x = torch.arange(12.0)
    print("x            ", tuple(x.shape))
    print("reshape(3,4) ", tuple(x.reshape(3, 4).shape))
    print("reshape(3,-1)", tuple(x.reshape(3, -1).shape), "  (-1 = infer)")
    print("unsqueeze(0) ", tuple(x.unsqueeze(0).shape))
    print("flatten(1) of (2,3,4):", tuple(torch.randn(2, 3, 4).flatten(1).shape))

    section("3. Broadcasting")
    A = torch.ones(4, 3)
    row = torch.tensor([10.0, 20.0, 30.0])     # (3,) -> (1,3)
    col = torch.tensor([[1.0], [2.0], [3.0], [4.0]])  # (4,1)
    print("A + row -> ", tuple((A + row).shape), "(adds row to every row)")
    print("A + col -> ", tuple((A + col).shape), "(adds per-row scalar)")
    print((A + row)[0].tolist(), "<- first row of A+row")

    section("4. Reductions")
    g = torch.arange(12.0).reshape(3, 4)
    print("g.sum()        =", g.sum().item())
    print("g.sum(dim=0)   =", g.sum(dim=0).tolist(), "(collapse rows -> (4,))")
    print("g.mean(dim=1)  =", g.mean(dim=1).tolist(), "(collapse cols -> (3,))")
    print("g.argmax(dim=1)=", g.argmax(dim=1).tolist(), "(index of max per row)")

    section("5. Matrix multiply (@)")
    P = torch.randn(2, 3)
    Q = torch.randn(3, 4)
    print("P(2,3) @ Q(3,4) ->", tuple((P @ Q).shape))
    print("dot of two (3,) vectors:", torch.tensor([1.0, 2, 3]).dot(torch.tensor([4.0, 5, 6])).item())

    print("\nDone. Try predicting each shape before reading it.")


if __name__ == "__main__":
    main()
