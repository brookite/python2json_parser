from abc import ABC, abstractmethod


class AbstractEntityRenderer(ABC):
    def __init__(self, tree_node, ancestor):
        self._node: dict = tree_node
        self._ancestor: "JSON2HtmlBuilder" = ancestor

    @abstractmethod
    def render_html(self, *args, **kwargs) -> str:
        pass
