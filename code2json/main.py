import argparse
import json
from code2json.python.__init__ import Python2JSONParser


LANGUAGES = {"python": Python2JSONParser}

argument_parser = argparse.ArgumentParser(
    description="Compile source code to JSON tree"
)
argument_parser.add_argument("lang", help="Programming language of given source code")
argument_parser.add_argument("input", help="Input source code file")


def main():
    args = argument_parser.parse_args()
    with open(args.input, "rb") as fobj:
        data = fobj.read()
    if args.lang.lower() not in LANGUAGES:
        print("Unsupported programming language")
        return
    parser = LANGUAGES[args.lang.lower()](data)
    result = parser.parse_all()
    print(json.dumps(result, ensure_ascii=False, indent=True))


if __name__ == "__main__":
    main()
