"""An adapter that gives the built-in `print` a .log(msg) interface.

Run me: python 08-adapter-pattern/code/print_adapter.py
"""


class PrintAdapter:
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix

    def log(self, msg: str) -> None:
        print(self.prefix + msg)


def main() -> None:
    a = PrintAdapter()
    b = PrintAdapter("[log] ")
    a.log("Hello, world!")
    b.log("Hello, world!")


if __name__ == "__main__":
    main()
