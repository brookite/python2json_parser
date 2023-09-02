from jinja2 import Template, FileSystemLoader, Environment
from abc import ABC, abstractmethod


class AbstractEntityRenderer(ABC):
    def __init__(self, tree_node, ancestor):
        self._node: AbstractEntityRenderer = tree_node
        self._ancestor: "JSON2HtmlBuilder" = ancestor

    @abstractmethod
    def render_html(self, *args, **kwargs) -> dict:
        pass


class StatementRenderer(AbstractEntityRenderer):
    def render_html(self, *args, **kwargs) -> dict:
        stmt = self._node.name
        template = self._ancestor.get_template(self._node.type)
        return template.render({
            "id": self._node["id"],
            "stmt": stmt
        })


class JSON2HtmlBuilder:
    type2template_name = {
        "stmt": "stmt"
    }

    def __init__(self):
        file_loader = FileSystemLoader('templates')
        self.env = Environment(loader=file_loader)

    def get_template(self, node_type):
        return self.env.get_template(f"{self.type2template[node_type]}.html")

    def build(self):
        pass
