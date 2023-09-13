import argparse
from builder import PythonJSON2HtmlBuilder
import json

argument_parser = argparse.ArgumentParser(
    description="Compile JSON tree of Python code to HTML"
)
argument_parser.add_argument("input", help="Input .py file")


def main():
    args = argument_parser.parse_args()
    with open(args.input, "rb") as fobj:
        data = fobj.read()
    obj = json.loads(data)
    builder = PythonJSON2HtmlBuilder()
    html = builder.build(obj)
    print(html)


if __name__ == "__main__":
    main()
