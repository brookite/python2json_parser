import argparse
import json
from pathlib import Path

from python.__init__ import Python2JSONParser
from c.__init__ import C2JSONParser


LANGUAGES = {"python": Python2JSONParser, "c": C2JSONParser}

argument_parser = argparse.ArgumentParser(
    description="Compile source code to JSON tree"
)
argument_parser.add_argument("lang", help="Programming language of given source code (one of: %s)" % (', '.join(LANGUAGES)))
argument_parser.add_argument("input", help="Path to input source code file")


def main():
    default_cmd_args = ['c', "examples/example8.c"]

    args = argument_parser.parse_args(default_cmd_args)
    
    with open(args.input, "rb") as fobj:
        data = fobj.read()
        
    if args.lang.lower() not in LANGUAGES:
        print("Unsupported programming language")
        return
    
    parser = LANGUAGES[args.lang.lower()](data)
    result = parser.parse_all()
    json_str = json.dumps(result, ensure_ascii=False, indent=True)
    print(json_str)

    out_p = Path(args.input)
    out_p = out_p.with_suffix('.json')
    with out_p.open('w') as f:
        f.write(json_str + '\n')


if __name__ == "__main__":
    main()
