from jinja2 import FileSystemLoader, Environment
from abc import ABC, abstractmethod
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
        self._node: dict = tree_node
        self._ancestor: "JSON2HtmlBuilder" = ancestor

    @abstractmethod
    def render_html(self, *args, **kwargs) -> str:
        pass


class AlternativeRenderer(AbstractEntityRenderer):
    PHASE_LABEL_PLAY = "Начнётся"
    PHASE_LABEL_STOP = "Закончится"
    PHASE_EXPR_LABEL_PLAY = "Выполнится"

    ACT_TYPE_PLAY = "started"
    ACT_TYPE_EXPR_PLAY = "performed"

    ACT_NAME_PLAY_TEMPLATE = "развилка `{}`"
    ACT_NAME_BRANCH_TEMPLATE = "ветка с условием `{}`"
    ACT_NAME_EXPR_TEMPLATE = "условие `{}`"
    ACT_NAME_ELSE_TEMPLATE = "ветка `иначе`"

    def render_html(self, *args, **kwargs) -> str:
        with_buttons = kwargs.get("with_buttons", True)
        tabs = kwargs.get("tabs", "")
        template = self._ancestor.get_template(self._node["type"])
        branches = {
            "if": {
                "id": self._node["branches"][0]["id"],
                "condition": self._node["branches"][0]["cond"]["name"],
                "body": self._ancestor.render_nodes(
                    self._node["branches"][0]["body"],
                    tabs=tabs.up(),
                    with_buttons=with_buttons,
                ),
                "expr_id": self._node["branches"][0]["cond"]["id"],
                "expr_act_type_play": self.ACT_TYPE_EXPR_PLAY,
                "expr_phase_label_play": self.PHASE_EXPR_LABEL_PLAY,
                "expr_act_name": self.ACT_NAME_EXPR_TEMPLATE.format(
                    self._node["branches"][0]["cond"]["name"]
                ),
                "act_type_play": self.ACT_TYPE_PLAY,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "act_play_name": self.ACT_NAME_BRANCH_TEMPLATE.format(
                    self._node["branches"][0]["cond"]["name"]
                ),
                "name": self._node.get("name", ""),
                "phase_label_stop": self.PHASE_LABEL_STOP,
            },
            "alternatives": [],
        }
        for branch in self._node["branches"][1:]:
            if branch["type"] == "else":
                branches["else"] = {
                    "body": self._ancestor.render_nodes(
                        branch["body"], tabs=tabs.up(), with_buttons=with_buttons
                    ),
                    "act_type_play": self.ACT_TYPE_PLAY,
                    "phase_label_play": self.PHASE_LABEL_PLAY,
                    "act_play_name": self.ACT_NAME_ELSE_TEMPLATE,
                    "phase_label_stop": self.PHASE_LABEL_STOP,
                }
            else:
                branches["alternatives"].append(
                    {
                        "id": branch["id"],
                        "condition": branch["cond"]["name"],
                        "body": self._ancestor.render_nodes(
                            branch["body"], tabs=tabs.up(), with_buttons=with_buttons
                        ),
                        "expr_id": branch["cond"]["id"],
                        "expr_act_type_play": self.ACT_TYPE_EXPR_PLAY,
                        "expr_phase_label_play": self.PHASE_EXPR_LABEL_PLAY,
                        "expr_act_name": self.ACT_NAME_EXPR_TEMPLATE.format(
                            branch["cond"]["name"]
                        ),
                        "act_type_play": self.ACT_TYPE_PLAY,
                        "phase_label_play": self.PHASE_LABEL_PLAY,
                        "act_play_name": self.ACT_NAME_BRANCH_TEMPLATE.format(
                            branch["cond"]["name"]
                        ),
                        "phase_label_stop": self.PHASE_LABEL_STOP,
                    }
                )
        return template.render(
            {
                "with_buttons": kwargs.get("with_buttons", True),
                "id": self._node["id"],
                "tabs": tabs,
                "branch": branches,
                "act_type_play": self.ACT_TYPE_PLAY,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "act_play_name": self.ACT_NAME_PLAY_TEMPLATE.format(
                    self._node.get("name", "")
                ),
                "name": self._node.get("name"),
                "phase_label_stop": self.PHASE_LABEL_STOP,
            }
        )


class ForLoopRenderer(AbstractEntityRenderer):
    PHASE_LABEL_PLAY = "Начнётся"
    PHASE_LABEL_STOP = "Закончится"
    ACT_TYPE_PLAY = "started"
    ACT_NAME_TEMPLATE = "цикл `{}`"
    ACT_ITER_NAME_TEMPLATE = "итерация цикла `{}`"

    def render_html(self, *args, **kwargs) -> str:
        with_buttons = kwargs.get("with_buttons", True)
        tabs = kwargs.get("tabs", "")
        template = self._ancestor.get_template(self._node["type"])
        if self._node["type"] == "for_loop":
            start = int(self._node["init"].split("=")[1])
            stop = int(self._node["cond"].split("<")[1])
            step = int(self._node["update"].split("+=")[1])
            extend = {
                "start": start,
                "stop": stop,
                "step": step,
            }
        else:
            extend = {"container": self._node["container"]}
        extend["variable"] = self._node["variable"]
        return template.render(
            {
                "with_buttons": kwargs.get("with_buttons", True),
                "id": self._node["id"],
                "seq_id": self._node["body"]["id"],
                "tabs": tabs,
                "act_type_play": self.ACT_TYPE_PLAY,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "act_name": self.ACT_NAME_TEMPLATE.format(self._node.get("name", "")),
                "act_iter_name": self.ACT_ITER_NAME_TEMPLATE.format(
                    self._node.get("name", "")
                ),
                "name": self._node.get("name", ""),
                "loop_body": self._ancestor.render_nodes(
                    self._node["body"]["body"],
                    tabs=tabs.up(),
                    with_buttons=with_buttons,
                ),
                **extend,
            }
        )


class WhileLoopRenderer(AbstractEntityRenderer):
    PHASE_LABEL_PLAY = "Начнётся"
    PHASE_LABEL_STOP = "Закончится"
    ACT_TYPE_PLAY = "started"
    ACT_NAME_TEMPLATE = "цикл `{}`"
    ACT_ITER_NAME_TEMPLATE = "итерация цикла `{}`"
    ACT_NAME_EXPR_TEMPLATE = "условие `{}`"
    ACT_TYPE_EXPR_PLAY = "performed"
    PHASE_EXPR_LABEL_PLAY = "Выполнится"

    def render_html(self, *args, **kwargs) -> str:
        tabs = kwargs.get("tabs", "")
        with_buttons = kwargs.get("with_buttons", True)
        template = self._ancestor.get_template(self._node["type"])
        return template.render(
            {
                "with_buttons": kwargs.get("with_buttons", True),
                "id": self._node["id"],
                "seq_id": self._node["body"]["id"],
                "tabs": tabs,
                "act_type_play": self.ACT_TYPE_PLAY,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "act_name": self.ACT_NAME_TEMPLATE.format(self._node.get("name", "")),
                "act_iter_name": self.ACT_ITER_NAME_TEMPLATE.format(
                    self._node.get("name", "")
                ),
                "name": self._node.get("name", ""),
                "loop_body": self._ancestor.render_nodes(
                    self._node["body"]["body"],
                    tabs=tabs.up(),
                    with_buttons=with_buttons,
                ),
                "condition": self._node["cond"]["name"],
                "expr_id": self._node["cond"]["id"],
                "expr_act_type_play": self.ACT_TYPE_EXPR_PLAY,
                "expr_phase_label_play": self.PHASE_EXPR_LABEL_PLAY,
                "expr_act_name": self.ACT_NAME_EXPR_TEMPLATE.format(
                    self._node["cond"]["name"]
                ),
            }
        )


class StatementRenderer(AbstractEntityRenderer):
    PHASE_LABEL_PLAY = "Выполнится"
    PHASE_LABEL_STOP = "Завершится"
    ACT_TYPE = "performed"
    ACT_NAME_TEMPLATE = {
        "break": "остановка цикла",
        "return": "возврат",
        "continue": "переход к следующей итерации цикла",
        "stmt": "действие `{}`",
        "func_call": "вызов функции `{}` с аргументами `{}`",
    }

    def render_html(self, *args, **kwargs) -> str:
        stmt = self._node["name"]
        tabs = kwargs.get("tabs", "")
        template = self._ancestor.get_template(self._node["type"])
        func_calls = self._node["func_calls"]
        func_calls.sort(key=lambda x: x["position"][0])
        new_stmt = ""
        func_call_template = self._ancestor.get_template("func_call")
        prev_end = 0
        for i, func_call in enumerate(func_calls):
            start = func_call["position"][0]
            end = func_call["position"][1]
            text = func_call_template.render(
                {
                    "with_buttons": kwargs.get("with_buttons", True),
                    "id": func_call["id"],
                    "act_type_stepinto": self.ACT_TYPE,
                    "phase_label_stepinto": self.PHASE_LABEL_PLAY,
                    "phase_label_stepout": self.PHASE_LABEL_STOP,
                    "act_name": self.ACT_NAME_TEMPLATE["func_call"].format(
                        func_call["func_name"], ",".join(func_call["func_args"])
                    ),
                    "function_name": func_call["func_name"],
                    "arguments": ", ".join(func_call["func_args"]),
                }
            )
            if i + 1 < len(func_calls):
                next_start = func_calls[i + 1]["position"][0]
                next_end = func_calls[i + 1]["position"][1]
                new_stmt += stmt[:start] + text + stmt[end:next_start]
                prev_end = end
            else:
                new_stmt += stmt[prev_end:start] + text + stmt[end : len(stmt)]
        if not new_stmt:
            new_stmt = stmt

        return template.render(
            {
                "with_buttons": kwargs.get("with_buttons", True),
                "id": self._node["id"],
                "tabs": tabs,
                "stmt": new_stmt,
                "act_type_play": self.ACT_TYPE,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "act_name": self.ACT_NAME_TEMPLATE.get(self._node["type"]).format(
                    self._node["name"]
                ),
                "name": self._node["name"],
            }
        )


class FunctionRenderer(AbstractEntityRenderer):
    def render_html(self, *args, **kwargs) -> str:
        with_buttons = kwargs.get("with_buttons", True)
        arguments = "(" + ", ".join(self._node["param_list"]) + ")"
        tabs = kwargs.get("tabs", "")
        template = self._ancestor.get_template(self._node["type"])
        body_html = self._ancestor.render_nodes(
            self._node["body"]["body"], tabs=tabs.up(), with_buttons=with_buttons
        )
        return template.render(
            {
                "with_buttons": kwargs.get("with_buttons", True),
                "id": self._node["id"],
                "func_name": self._node["name"],
                "arguments": arguments,
                "return_type": self._node.get("return_type"),
                "tabs": tabs,
                "function_body": body_html,
                "func_return_type": self._node["return_type"],
            }
        )


class PythonJSON2HtmlBuilder:
    type2template = {
        "stmt": "stmt",
        "func": "function",
        "break": "keyword_statement",
        "return": "keyword_statement",
        "continue": "keyword_statement",
        "alternative": "alternative",
        "for_loop": "for_loop",
        "foreach_loop": "foreach_loop",
        "while_loop": "while_loop",
        "func_call": "function_call",
    }

    type2renderer = {
        "alternative": AlternativeRenderer,
        "func": FunctionRenderer,
        "stmt": StatementRenderer,
        "break": StatementRenderer,
        "return": StatementRenderer,
        "continue": StatementRenderer,
        "for_loop": ForLoopRenderer,
        "foreach_loop": ForLoopRenderer,
        "while_loop": WhileLoopRenderer,
    }

    def __init__(self):
        directory = os.path.dirname(__file__)
        file_loader = FileSystemLoader(os.path.join(directory, "templates"))
        self.env = Environment(loader=file_loader)

    def get_template(self, node_type):
        return self.env.get_template(f"python/{self.type2template[node_type]}.html")

    def get_renderer(self, node) -> AbstractEntityRenderer:
        if renderer := self.type2renderer.get(node["type"]):
            return renderer(node, self)

    def render_nodes(self, nodes, tabs=Tab(0), with_buttons=True) -> str:
        html = ""
        for element in nodes:
            if renderer := self.get_renderer(element):
                html += renderer.render_html(tabs=tabs, with_buttons=with_buttons)
        return html

    def build(self, object, with_buttons=True) -> str:
        functions = []
        tabs = Tab(0)
        for function in object["functions"]:
            if renderer := self.get_renderer(function):
                functions.append(
                    renderer.render_html(tabs=tabs, with_buttons=with_buttons)
                )
        global_html = self.render_nodes(
            object["global_code"]["body"], tabs=tabs, with_buttons=with_buttons
        )
        return self.env.get_template("document.html").render(
            {"global_code": global_html, "functions": functions}
        )
