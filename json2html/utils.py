class Tab:
    """Immutable HTML indentiation consisting of 4*level non-breaking spaces (&nbsp;)."""

    def __init__(self, level: int, whitespaces=4):
        if level < 0:
            level = 0
        if whitespaces <= 0:
            whitespaces = 1
        self._whitespaces = whitespaces
        self._level = level

    def up(self):
        return Tab(self._level + 1, self._whitespaces)

    def down(self):
        return Tab(self._level - 1, self._whitespaces)

    def set_level(self, level: int):
        self._level = level

    def set_whitespaces(self, whitespaces: int):
        self._whitespaces = whitespaces

    def __bool__(self):
        return self._level != 0

    def __str__(self):
        return self._level * ('<span class="left-border"></span>%s' % ("&nbsp;" * self._whitespaces))


def html_quote_escape(string):
    return string.replace('"', "&quot;").replace("'", "&#39;")
