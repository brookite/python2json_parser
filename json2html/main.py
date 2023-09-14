import argparse
from builder import JSON2HtmlBuilder
import json
import os

argument_parser = argparse.ArgumentParser(
    description="Compile JSON tree of code to HTML"
)
argument_parser.add_argument("lang", help="Programming language for target HTML")
argument_parser.add_argument("input", help="Algorithm JSON tree file")
argument_parser.add_argument(
    "--disable-buttons",
    help="Disables action buttons in HTML",
    action="store_true",
    default=False,
)


def main():
    args = argument_parser.parse_args()
    with open(args.input, "rb") as fobj:
        data = fobj.read()
    obj = json.loads(data)
    builder = JSON2HtmlBuilder(args.lang)
    directory = os.path.dirname(__file__)
    if not os.path.isdir(os.path.join(directory, "templates", args.lang)):
        print("Unsupported programming language")
        return
    html = builder.build(obj, with_buttons=not args.disable_buttons)
    print(html)


if __name__ == "__main__":
    main()
