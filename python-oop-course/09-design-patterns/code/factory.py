"""Factory: a function that returns the right kind of parser for a filename.

Run:
    python 09-design-patterns/code/factory.py
"""


class Parser:
    def parse(self, text: str): raise NotImplementedError


class JSONParser(Parser):
    def parse(self, text: str):
        import json
        return json.loads(text)


class CSVParser(Parser):
    def parse(self, text: str):
        import csv
        from io import StringIO
        return list(csv.reader(StringIO(text)))


def parser_for(filename: str) -> Parser:
    if filename.endswith(".json"):
        return JSONParser()
    if filename.endswith(".csv"):
        return CSVParser()
    raise ValueError(f"unknown format: {filename}")


def main() -> None:
    print(parser_for("a.json").parse('{"a": 1, "b": 2}'))
    print(parser_for("a.csv").parse("a,b\n1,2\n3,4"))
    try:
        parser_for("a.xml")
    except ValueError as e:
        print("blocked:", e)


if __name__ == "__main__":
    main()
