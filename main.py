import builder
import argparse
import json
import os

argument_parser = argparse.ArgumentParser(
    description="Compile Python source code to JSON tree"
)
argument_parser.add_argument("input", help="Input .py file")


def main():
    args = argument_parser.parse_args()
    with open(args.input, "rb") as fobj:
        data = fobj.read()
    parser = builder.Python2JSONParser(data)
    result = parser.parse_all()
    print(json.dumps(result, ensure_ascii=False, indent=True))


if __name__ == "__main__":
    main()
