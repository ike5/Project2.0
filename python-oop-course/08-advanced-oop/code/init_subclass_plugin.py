"""A tiny plugin registry built with __init_subclass__.

Run:
    python 08-advanced-oop/code/init_subclass_plugin.py
"""


class Plugin:
    registry: dict = {}

    def __init_subclass__(cls, *, name, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry[name] = cls

    def run(self, payload):                     # default implementation
        return f"{type(self).__name__}: {payload}"


@Plugin.register(name="upper")
class UpperPlugin(Plugin):
    def run(self, payload): return payload.upper()


@Plugin.register(name="reverse")
class ReversePlugin(Plugin):
    def run(self, payload): return payload[::-1]


def main() -> None:
    print("registered:", list(Plugin.registry))
    for name in ("upper", "reverse"):
        print(name, "->", Plugin.registry[name]().run("hello"))


if __name__ == "__main__":
    main()
