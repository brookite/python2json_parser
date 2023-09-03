from jinja2 import FileSystemLoader, Environment
from abc import ABC, abstractmethod
import argparse
import json
import os


class Tab:
    def __init__(self, level: int):
        if level < 0:
            level = 0
        self._level = level
    
    def up(self):
        return Tab(self._level + 1)
    
    def down(self):
        return Tab(self._level - 1)

    def __bool__(self):
        return self._level != 0
    
    def __str__(self):
        return self._level * ("&nbsp;" * 4)


class AbstractEntityRenderer(ABC):
    def __init__(self, tree_node, ancestor):
        self._node: AbstractEntityRenderer = tree_node
        self._ancestor: "JSON2HtmlBuilder" = ancestor

    @abstractmethod
    def render_html(self, *args, **kwargs) -> dict:
        pass


class StatementRenderer(AbstractEntityRenderer):
    def render_html(self, *args, **kwargs) -> dict:
        stmt = self._node["name"]
        tabs = kwargs.get("tabs", "")
        template = self._ancestor.get_template(self._node["type"])
        return template.render({
            "id": self._node["id"],
            "tabs": tabs,
            "stmt": stmt
        })


class FunctionRenderer(AbstractEntityRenderer):
    def render_html(self, *args, **kwargs) -> dict:
        arguments = "(" + ", ".join(self._node["param_list"]) + ")"
        tabs = kwargs.get("tabs", "")
        template = self._ancestor.get_template(self._node["type"])
        body_html = self._ancestor.render_nodes(self._node["body"]["body"], tabs=tabs.up())
        return template.render({
            "id": self._node["id"],
            "func_name": self._node["name"],
            "arguments": arguments,
            "return_type": self._node.get("return_type"),
            "tabs": tabs,
            "function_body": body_html
        })


class JSON2HtmlBuilder:
    type2template = {
        "stmt": "stmt",
        "func": "function",
        "break": "keyword_statement",
        "return": "keyword_statement",
        "continue": "keyword_statement"
    }

    type2renderer = {
        "func": FunctionRenderer,
        "stmt": StatementRenderer,
        "break": StatementRenderer,
        "return": StatementRenderer,
        "continue": StatementRenderer,
    }

    def __init__(self):
        directory = os.path.dirname(__file__)
        file_loader = FileSystemLoader(os.path.join(directory, 'templates'))
        self.env = Environment(loader=file_loader)

    def get_template(self, node_type):
        return self.env.get_template(f"structures/{self.type2template[node_type]}.html")

    def get_renderer(self, node):
        if renderer := self.type2renderer.get(node["type"]):
            return renderer(node, self)
        
    def render_nodes(self, nodes, tabs=''):
        html = ''
        for element in nodes:
            if renderer := self.get_renderer(element):
                html += renderer.render_html(tabs=tabs)
        return html


    def build(self, object):
        functions = []
        tabs = Tab(0)
        for function in object["functions"]:
            if renderer := self.get_renderer(function):
                functions.append(renderer.render_html(tabs=tabs))
        global_html = self.render_nodes(object["global_code"]["body"], tabs=tabs)
        return self.env.get_template("document.html").render( 
            {
                "global_code": global_html,
                "functions": functions
            }
        )


def main():
    argument_parser = argparse.ArgumentParser(
        description="Compile JSON tree of Python code to HTML"
    )
    argument_parser.add_argument("input", help="Input .py file")
    args = argument_parser.parse_args()
    with open(args.input, "rb") as fobj:
        data = fobj.read()
    object = json.loads(data)
    builder = JSON2HtmlBuilder()
    print(builder.build(object))


if __name__ == "__main__":
    main()