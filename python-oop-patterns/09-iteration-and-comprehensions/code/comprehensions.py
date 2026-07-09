"""A tour of comprehensions.

Run me: python 09-iteration-and-comprehensions/code/comprehensions.py
"""


def main() -> None:
    xs = [1, -2, 3, -4, 5]

    # list
    squares = [x * x for x in xs]
    print("squares (positives only) =", [x * x for x in xs if x > 0])

    # set
    print("abs values            =", {abs(x) for x in xs})

    # dict
    print("val: square           =", {x: x * x for x in xs if x > 0})

    # generator (lazy)
    total = sum(x * x for x in xs)
    print("sum of squares        =", total)

    # any / all
    print("any positive?         =", any(x > 0 for x in xs))
    print("all positive?         =", all(x > 0 for x in xs))

    # next with default
    first_big = next((x for x in xs if x > 10), None)
    print("first > 10            =", first_big)


if __name__ == "__main__":
    main()
