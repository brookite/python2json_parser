class Tab:
    """Immutable HTML indentiation consisting of 4*level non-breaking spaces (&nbsp;)."""

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


def html_quote_escape(string):
    return string.replace('"', "&quot;").replace("'", "&#39;")
