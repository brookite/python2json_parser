from abc import ABC, abstractmethod


class AbstractCodeParser(ABC):
    def __init__(self, code):
        pass

    @abstractmethod
    def parse_all(self):
        pass

    @abstractmethod
    def parse_node(self, node):
        pass


class AbstractEntityParser(ABC):
    def __init__(self, node, parser):
        self._node = node
        self._parser = parser

    @abstractmethod
    def parse(self, *args, **kwargs) -> dict:
        pass
