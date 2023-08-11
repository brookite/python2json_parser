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
        if self._node.children:
            if (call_func := self._node.children[0]).type == "call":
                return FunctionCallParser(call_func, self._parser).parse()

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


class FunctionCallParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> dict:
        result = {
            "id": self._parser.get_new_id(),
            "type": "func_call",
            "func_name": self._node.child_by_field_name("function").text.decode(
                "utf-8"
            ),
            "func_args": [],
        }
        # TODO: func_id
        args = self._node.child_by_field_name("arguments").named_children
        for arg in args:
            result["func_args"].append(arg.text.decode("utf-8"))
        return result


class ConditionParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> dict:
        result = {
            "id": self._parser.get_new_id(),
            "type": "alternative",
            "branches": [{"id": self._parser.get_new_id(), "type": "if", "body": []}],
        }

        comment_node = self._node.children[3]
        if comment_node.type == "comment":
            result["branches"][0]["name"] = comment_node.text.decode("utf-8")[
                1:
            ].strip()

        alternatives = self._node.children_by_field_name("alternative")
        for alternative in alternatives:
            result["branches"].append(self._parse_branches(alternative))
        # TODO: cond_values_hint
        condition = self._node.child_by_field_name("condition")
        result["branches"][0]["cond"] = ExpressionParser(
            condition, self._parser
        ).parse()
        body = self._node.child_by_field_name("consequence")
        for child in body.children:
            if tree_node := self._parser.parse_node(child):
                result["branches"][0]["body"].append(tree_node)
        return result

    def _parse_branches(self, node) -> dict:
        result = {"id": self._parser.get_new_id(), "body": []}
        body = None
        if node.type == "elif_clause":
            result["type"] = "else-if"

            comment_node = node.children[3]
            if comment_node.type == "comment":
                result["name"] = comment_node.text.decode("utf-8")[1:].strip()

            body = node.child_by_field_name("consequence")
            condition = node.child_by_field_name("condition")
            result["cond"] = ExpressionParser(condition, self._parser).parse()
        elif node.type == "else_clause":
            result["type"] = "else"
            body = node.child_by_field_name("body")
        for child in body.children:
            if tree_node := self._parser.parse_node(child):
                result["body"].append(tree_node)
        return result


class ExpressionParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> dict:
        return {
            "id": self._parser.get_new_id(),
            "type": "expr",
            "name": self._node.text.decode("utf-8"),
        }


class FunctionParser(AbstractEntityParser):
    def parse(self) -> dict:
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


class WhileLoopParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> dict:
        result = {
            "id": self._parser.get_new_id(),
            "type": "while_loop",
            "cond": ExpressionParser(
                self._node.child_by_field_name("condition"), self._parser
            ).parse(),
            "body": [],
        }

        comment_node = self._node.children[3]
        if comment_node.type == "comment":
            result["name"] = comment_node.text.decode("utf-8")[1:].strip()

        # TODO: cond_values_hint
        body = self._node.child_by_field_name("body")
        for child in body.children:
            if tree_node := self._parser.parse_node(child):
                result["body"].append(tree_node)
        return result


class ForLoopParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> dict:
        result = {
            "id": self._parser.get_new_id(),
            "variable": self._node.child_by_field_name("left").text.decode("utf-8"),
            "body": [],
        }
        container = self._node.child_by_field_name("right")
        if container.type == "call":
            func_name = container.child_by_field_name("function").text.decode("utf-8")
            if func_name == "range":
                result.update(self._parse_for_loop(container, result["variable"]))
            else:
                result.update(self._parse_foreach_loop(container, result["variable"]))
        else:
            result.update(self._parse_foreach_loop(container, result["variable"]))

        comment_node = self._node.named_children[2]
        if comment_node.type == "comment":
            result["name"] = comment_node.text.decode("utf-8")[1:].strip()

        body = self._node.child_by_field_name("body")
        for child in body.children:
            if tree_node := self._parser.parse_node(child):
                result["body"].append(tree_node)

        return result

    def _parse_for_loop(self, cond_node, variable_name) -> dict:
        result = {"type": "for_loop"}

        arguments = cond_node.child_by_field_name("arguments")
        start = 0
        stop = None
        step = 1
        if len(arguments.named_children) == 1:
            stop = arguments.named_children[0].text.decode("utf-8")
        elif len(arguments.named_children) == 2:
            start = arguments.named_children[0].text.decode("utf-8")
            stop = arguments.named_children[1].text.decode("utf-8")
        else:
            start = arguments.named_children[0].text.decode("utf-8")
            stop = arguments.named_children[1].text.decode("utf-8")
            step = arguments.named_children[2].text.decode("utf-8")

        result["init"] = f"{variable_name}={start}"
        result["cond"] = f"{variable_name}<{stop}"
        result["update"] = f"{variable_name}+={step}"
        return result

    def _parse_foreach_loop(self, container_node, variable_name) -> dict:
        container = container_node.text.decode("utf-8")
        return {
            "container": container,
            "type": "foreach_loop",
            "init": f"{variable_name}={container}.first()",
            "cond": f"{variable_name}!={container}.last()",
            "update": f"{variable_name}=next({container}, {variable_name})",
        }


class Python2JSONParser:
    TYPE_PARSER = {
        "function_definition": FunctionParser,
        "expression_statement": StatementParser,
        "break_statement": StatementParser,
        "return_statement": StatementParser,
        "continue_statement": StatementParser,
        "if_statement": ConditionParser,
        "while_statement": WhileLoopParser,
        "for_statement": ForLoopParser,
    }

    def __init__(self, code: bytes):
        self._tree = parser.parse(code)
        # print(self._tree.root_node.sexp())
        self._result = {
            "functions": [],
            "global_code": {"body": [], "name": "algorithm", "type": "algorithm"},
        }
        self._id_counter = 0

    def parse_node(self, node: Node):
        entity_parser = self.TYPE_PARSER.get(node.type)
        if entity_parser:
            return entity_parser(node, self).parse()

    def parse_all(self):
        for node in self._tree.root_node.children:
            if result := self.parse_node(node):
                if result["type"] == "func":
                    self._result["functions"].append(result)
                else:
                    self._result["global_code"]["body"].append(result)
        return self._result

    def get_new_id(self):
        self._id_counter += 1
        return self._id_counter
