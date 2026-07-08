"""Adapter: translate one interface into another.

Run:
    python 09-design-patterns/code/adapter.py
"""


class CelsiusWeather:
    def temperature_c(self) -> float: return 25.0


class USWeatherAdapter:
    """Adapts a Celsius source to the Fahrenheit interface."""

    def __init__(self, source) -> None:
        self.source = source

    def temperature_f(self) -> float:
        return self.source.temperature_c() * 9 / 5 + 32


def main() -> None:
    src = CelsiusWeather()
    adapted = USWeatherAdapter(src)
    print(f"25 C in F = {adapted.temperature_f()}")    # 77.0


if __name__ == "__main__":
    main()
