from tree_sitter import Language, Parser, Node
from typing import Dict, Optional, Tuple, List
from interfaces import AbstractEntityParser, AbstractCodeParser
import os.path

directory = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
Language.build_library(
    os.path.join(directory, "build", "treesitter_c.so"),
    [os.path.join(directory, "tree-sitter-c")],
)
LANGUAGE = Language(os.path.join(directory, "build", "treesitter_c.so"), "c")

parser = Parser()
parser.set_language(LANGUAGE)


class SequenceParser(AbstractEntityParser):
    def parse(self, seq_name, *args, **kwargs) -> Optional[dict]:
        result = []
        for node in self._node.children:
            if entity_node := self._parser.parse_node(node):
                if isinstance(entity_node, list):
                    for item in entity_node:
                        result.append(item)
                else:
                    result.append(entity_node)

        return {
            "id": self._parser.get_new_id(),
            "type": "sequence",
            "name": seq_name,
            "body": result,
        }


class AbstractExpressionParser(AbstractEntityParser):
    def find_function_calls(self, parent_node) -> Dict:
        children = [parent_node]
        result = []
        while len(children):
            node = children.pop(0)
            if node.type == "call_expression":
                name = node.child_by_field_name("function").text.decode("utf-8")
                args = self.parse_func_args(node.child_by_field_name("arguments"))
                if function := self._parser.find_function(name)[1]:
                    result.append(
                        FunctionCallParser(node, self._parser).parse(
                            function, args, self._node.text.decode("utf-8")
                        )
                    )
                if node == parent_node:
                    children.extend(node.children)
            else:
                children.extend(node.children)
        return result

    def parse_func_args(self, args) -> List[Dict]:
        children = [args]
        result = []
        while len(children):
            node = children.pop(0)
            if node.type == "call_expression":
                result.append(self.find_function_calls(node)[0])
            else:
                if node.type != "argument_list":
                    result.append(
                        {"type": "argument", "name": node.text.decode("utf-8")}
                    )
                children.extend(node.named_children)
        return result


class StatementParser(AbstractExpressionParser):
    def parse(self, *args, **kwargs) -> Optional[dict]:
        print(self._node.sexp())
        function_calls = self.find_function_calls(self._node)

        if self._node.type == "break_statement":
            type = "break"
        elif self._node.type == "continue_statement":
            type = "continue"
        elif self._node.type == "return_statement":
            type = "return"
        elif len(function_calls):
            type = "stmt_with_calls"
        else:
            type = "stmt"

        return {
            "id": self._parser.get_new_id(),
            "type": type,
            "name": self._node.text.decode("utf-8"),
            "func_calls": function_calls,
        }


class FunctionCallParser(AbstractEntityParser):
    def parse(self, function, arguments, call_expr, *args, **kwargs) -> Optional[dict]:
        result = {
            "id": self._parser.get_new_id(),
            "type": "func_call",
            "func_name": self._node.child_by_field_name("function").text.decode(
                "utf-8"
            ),
            "func_id": function["id"],
            "func_args": arguments,
        }
        result["position"] = [
            self._node.start_point[1] - len(result["func_name"]),
            self._node.end_point[1],
        ]
        if result["position"][0] < 0:
            result["position"][0] = 0
        return result


class ConditionParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> Optional[dict]:
        result = {
            "id": self._parser.get_new_id(),
            "type": "alternative",
            "branches": [{"id": self._parser.get_new_id(), "type": "if", "body": []}],
        }

        alternative = self._node.child_by_field_name("alternative")
        self._parse_branches(alternative, result["branches"])
        condition = self._node.child_by_field_name("condition")
        result["branches"][0]["cond"] = ExpressionParser(
            condition, self._parser
        ).parse()
        body = self._node.child_by_field_name("consequence")
        comment_node = body.named_children[1]
        if comment_node.type == "comment":
            result["name"] = (
                comment_node.text.decode("utf-8")[1:].replace("/ ", "").strip()
            )
        for child in body.children:
            if tree_node := self._parser.parse_node(child):
                result["branches"][0]["body"].append(tree_node)
        return result

    def _parse_branches(self, node, branches) -> Optional[dict]:
        result = {"id": self._parser.get_new_id(), "body": []}
        body = None
        node = node.named_children[0]
        next = None

        if node.type == "if_statement":
            result["type"] = "else-if"
            body = node.child_by_field_name("consequence")
            condition = node.child_by_field_name("condition")
            result["cond"] = ExpressionParser(condition, self._parser).parse()
            next = node.child_by_field_name("alternative")
        else:
            result["type"] = "else"
            if len(node.named_children):
                body = node.named_children[0]
            else:
                return
        for child in body.named_children:
            if tree_node := self._parser.parse_node(child):
                result["body"].append(tree_node)
        branches.append(result)
        if next:
            self._parse_branches(next, branches)


class ExpressionParser(AbstractExpressionParser):
    def parse(self, *args, **kwargs) -> Optional[dict]:
        return {
            "id": self._parser.get_new_id(),
            "type": "expr",
            "name": self._node.text.decode("utf-8")[1:-1],
            "func_calls": self.find_function_calls(self._node),
        }


class FunctionParser(AbstractEntityParser):
    def parse(self) -> Optional[dict]:
        declarator = self._node.child_by_field_name("declarator")
        name = declarator.child_by_field_name("declarator").text.decode("utf-8")
        obj = {
            "id": self._parser.get_new_id(),
            "type": "func",
            "name": name,
            "param_list": [],
        }
        obj["is_entry"] = obj["name"] == "main"
        params = declarator.child_by_field_name("parameters")
        for param in params.named_children:
            obj["param_list"].append(param.text.decode("utf-8"))
        if return_type := self._node.child_by_field_name("type"):
            obj["return_type"] = return_type.text.decode("utf-8")
        seq_name = obj["name"] + "-body"
        obj["body"] = SequenceParser(
            self._node.child_by_field_name("body"), self._parser
        ).parse(seq_name)
        return obj


class WhileLoopParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> Optional[dict]:
        result = {
            "id": self._parser.get_new_id(),
            "type": "while_loop",
            "cond": ExpressionParser(
                self._node.child_by_field_name("condition"), self._parser
            ).parse(),
            "body": {},
        }

        body = self._node.child_by_field_name("body")
        comment_node = body.named_children[0]
        if comment_node.type == "comment":
            result["name"] = (
                comment_node.text.decode("utf-8")[1:].replace("/ ", "").strip()
            )
        name = result.get("name", str(result["id"])) + "_loop_body"
        result["body"] = SequenceParser(body, self._parser).parse(name)

        return result


class ForLoopParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> Optional[dict]:
        initializer = self._node.child_by_field_name("initializer")
        condition = self._node.child_by_field_name("condition")
        update = self._node.child_by_field_name("update")
        variable = (
            initializer.child_by_field_name("declarator")
            .child_by_field_name("declarator")
            .text.decode("utf-8")
        )
        result = {
            "id": self._parser.get_new_id(),
            "variable": variable,
            "body": {},
            "init": initializer.text.decode("utf-8"),
            "cond": condition.text.decode("utf-8"),
            "update": update.text.decode("utf-8"),
        }

        body = self._node.child_by_field_name("body")
        comment_node = body.named_children[0]
        if comment_node.type == "comment":
            result["name"] = (
                comment_node.text.decode("utf-8")[1:].replace("/ ", "").strip()
            )
        name = result.get("name", str(result["id"])) + "_loop_body"
        result["body"] = SequenceParser(body, self._parser).parse(name)

        return result


class CompoundStatementParser(AbstractEntityParser):
    def parse(self, *args, **kwargs) -> Optional[List[dict]]:
        children = self._node.named_children
        return [self._parser.parse_node(child) for child in children]


class C2JSONParser(AbstractCodeParser):
    TYPE_PARSER = {
        "function_definition": FunctionParser,
        "expression_statement": StatementParser,
        "break_statement": StatementParser,
        "return_statement": StatementParser,
        "continue_statement": StatementParser,
        "if_statement": ConditionParser,
        "while_statement": WhileLoopParser,
        "for_statement": ForLoopParser,
        "declaration": StatementParser,
        "compound_statement": CompoundStatementParser,
    }

    def __init__(self, code: bytes):
        self._tree = parser.parse(code)
        # print(self._tree.root_node.sexp())
        self._id_counter = 0
        self._result = {
            "id": self.get_new_id(),
            "functions": [],
            "global_code": {"body": [], "name": "global_code", "type": "sequence"},
            "name": "algorithm",
            "type": "algorithm",
        }

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

    def find_function(self, name: str) -> Tuple[int, Optional[dict]]:
        for i, function in enumerate(self._result["functions"]):
            if function["name"] == name:
                return i, function
        return -1, None

    def get_new_id(self):
        self._id_counter += 1
        return self._id_counter
