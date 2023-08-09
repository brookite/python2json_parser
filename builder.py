from tree_sitter import Language, Parser, Node
from abc import ABC, abstractmethod

Language.build_library("build/treesitter.so", ["tree-sitter-python/"])
PY_LANGUAGE = Language("build/treesitter.so", "python")

parser = Parser()
parser.set_language(PY_LANGUAGE)


class AbstractEntityParser(ABC):
    def __init__(self, node: Node, parser: "Python2JSONParser"):
        self._node: Node = node
        self._parser: "Python2JSONParser" = parser

    @abstractmethod
    def parse(self, *args, **kwargs) -> dict:
        pass


class SequenceParser(AbstractEntityParser):
    def parse(self, seq_name, *args, **kwargs) -> dict:
        result = []
        for node in self._node.children:
            if entity_node := self._parser.parse_node(node):
                result.append(entity_node)
        return {
            "id": self._parser.get_new_id(),
            "type": "sequence",
            "name": seq_name,
            "body": result,
        }


class StatementParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> dict:
        if self._node.type == "break_statement":
            type = "break"
        elif self._node.type == "continue_statement":
            type = "continue"
        elif self._node.type == "return_statement":
            type = "return"
        else:
            type = "stmt"

        return {
            "id": self._parser.get_new_id(),
            "type": type,
            "name": self._node.text.decode("utf-8"),
        }


class ExpressionParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> dict:
        return {
            "id": self._parser.get_new_id(),
            "type": "expr",
            "name": self._node.text.decode("utf-8"),
        }


class FunctionParser(AbstractEntityParser):
    def parse(self) -> dict:
        print(self._node.sexp())
        obj = {
            "id": self._parser.get_new_id(),
            "type": "func",
            "name": self._node.child_by_field_name("name").text.decode("utf-8"),
            "param_list": [],
        }
        obj["is_entry"] = obj["name"] == "main"
        params = self._node.child_by_field_name("parameters")
        for param in params.named_children:
            obj["param_list"].append(param.text.decode("utf-8"))
        if return_type := self._node.child_by_field_name("return_type"):
            obj["return_type"] = return_type.text.decode("utf-8")
        seq_name = obj["name"] + "-body"
        obj["body"] = SequenceParser(
            self._node.child_by_field_name("body"), self._parser
        ).parse(seq_name)
        return obj


class Python2JSONParser:
    TYPE_PARSER = {
        "function_definition": FunctionParser,
        "expression_statement": StatementParser,
        "break_statement": StatementParser,
        "return_statement": StatementParser,
        "continue_statement": StatementParser,
    }

    def __init__(self, code: bytes):
        self._tree = parser.parse(code)
        self._result = []
        self._id_counter = 0

    def parse_node(self, node: Node):
        entity_parser = self.TYPE_PARSER.get(node.type)
        if entity_parser:
            return entity_parser(node, self).parse()
        return None

    def parse_all(self):
        for node in self._tree.root_node.children:
            if result := self.parse_node(node):
                self._result.append(result)
        return self._result

    def get_new_id(self):
        self._id_counter += 1
        return self._id_counter
