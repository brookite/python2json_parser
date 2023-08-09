import builder


with open("examples/example1.py", "rb") as fobj:
    data = fobj.read()

parser = builder.Python2JSONParser(data)
print(parser.parse_all())
