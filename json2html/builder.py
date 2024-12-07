from jinja2 import FileSystemLoader, Environment
import os
from utils import Tab, html_quote_escape
from interfaces import AbstractEntityRenderer


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
                # "condition": self._node["branches"][0]["cond"]["name"],
                "condition": self._ancestor.render_node(self._node["branches"][0]["cond"],
                    tabs=tabs,
                    with_buttons=with_buttons,
                ),
                "body": self._ancestor.render_nodes(
                    self._node["branches"][0]["body"],
                    tabs=tabs.up(),
                    with_buttons=with_buttons,
                ),
                "expr_id": self._node["branches"][0]["cond"]["id"],
                "expr_act_type_play": self.ACT_TYPE_EXPR_PLAY,
                "expr_phase_label_play": self.PHASE_EXPR_LABEL_PLAY,
                "expr_act_name": self.ACT_NAME_EXPR_TEMPLATE.format(
                    html_quote_escape(self._node["branches"][0]["cond"]["name"])
                ),
                "act_type_play": self.ACT_TYPE_PLAY,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "act_play_name": self.ACT_NAME_BRANCH_TEMPLATE.format(
                    html_quote_escape(self._node["branches"][0]["cond"]["name"])
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
                            html_quote_escape(branch["cond"]["name"])
                        ),
                        "act_type_play": self.ACT_TYPE_PLAY,
                        "phase_label_play": self.PHASE_LABEL_PLAY,
                        "act_play_name": self.ACT_NAME_BRANCH_TEMPLATE.format(
                            html_quote_escape(branch["cond"]["name"])
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
                    html_quote_escape(self._node.get("name", ""))
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
            if "start" in self._node:
                start = self._node.get("start")
                stop = self._node.get("stop")
                step = self._node.get("step")
                extend = {
                    "start": start,
                    "stop": stop,
                    "step": step,
                }
            else:
                extend = {
                    "init": self._node["init"],
                    "cond": self._node["cond"],
                    "update": self._node["update"],
                }
        else:
            extend = {"container": self._node["container"]}
        extend["variable"] = self._node.get("variable", "")
        return template.render(
            {
                "with_buttons": kwargs.get("with_buttons", True),
                "id": self._node["id"],
                "seq_id": self._node["body"]["id"],
                "tabs": tabs,
                "act_type_play": self.ACT_TYPE_PLAY,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "phase_label_stop": self.PHASE_LABEL_STOP,
                "act_name": self.ACT_NAME_TEMPLATE.format(
                    html_quote_escape(self._node.get("name", ""))
                ),
                "act_iter_name": self.ACT_ITER_NAME_TEMPLATE.format(
                    html_quote_escape(self._node.get("name", ""))
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
                "phase_label_stop": self.PHASE_LABEL_STOP,
                "act_name": self.ACT_NAME_TEMPLATE.format(
                    html_quote_escape(self._node.get("name", ""))
                ),
                "act_iter_name": self.ACT_ITER_NAME_TEMPLATE.format(
                    html_quote_escape(self._node.get("name", ""))
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
                    html_quote_escape(self._node["cond"]["name"])
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
        "stmt_with_calls": "действие `{}`",
        "func_call": "вызов функции `{}` с аргументами `{}`",
    }

    def _build_func_args(self, func_args, func_call_template, with_buttons=True):
        result = []
        for arg in func_args:
            if arg["type"] == "func_call":
                start = arg["position"][0]
                end = arg["position"][1]
                args_list = self._node["name"][start + len(arg["func_name"]) : end]
                result.append(
                    func_call_template.render(
                        {
                            "with_buttons": with_buttons,
                            "id": arg["id"],
                            "act_type_stepinto": self.ACT_TYPE,
                            "phase_label_stepinto": self.PHASE_LABEL_PLAY,
                            "phase_label_stepout": self.PHASE_LABEL_STOP,
                            "act_name": self.ACT_NAME_TEMPLATE["func_call"].format(
                                arg["func_name"], html_quote_escape(args_list)
                            ),
                            "function_name": arg["func_name"],
                            "arguments": self._build_func_args(
                                arg["func_args"], func_call_template, with_buttons
                            ),
                        }
                    )
                )
            else:
                result.append(arg["name"])
        return ", ".join(result)

    def form_stmt(self, with_buttons):
        stmt = self._node["name"]
        new_stmt = ""
        func_calls = self._node["func_calls"]
        func_calls.sort(key=lambda x: x["position"][0])
        func_call_template = self._ancestor.get_template("func_call")
        prev_end = 0
        for i, func_call in enumerate(func_calls):
            start = func_call["position"][0]
            end = func_call["position"][1]
            args_list = stmt[start + len(func_call["func_name"]) : end]
            text = func_call_template.render(
                {
                    "with_buttons": with_buttons,
                    "id": func_call["id"],
                    "act_type_stepinto": self.ACT_TYPE,
                    "phase_label_stepinto": self.PHASE_LABEL_PLAY,
                    "phase_label_stepout": self.PHASE_LABEL_STOP,
                    "act_name": self.ACT_NAME_TEMPLATE["func_call"].format(
                        func_call["func_name"], html_quote_escape(args_list)
                    ),
                    "function_name": func_call["func_name"],
                    "arguments": self._build_func_args(
                        func_call["func_args"], func_call_template, with_buttons
                    ),
                }
            )
            if i + 1 < len(func_calls):
                next_start = func_calls[i + 1]["position"][0]
                next_end = func_calls[i + 1]["position"][1]
                new_stmt += stmt[prev_end:start] + text + stmt[end:next_start]
                prev_end = next_start
            else:
                new_stmt += stmt[prev_end:start] + text + stmt[end : len(stmt)]
        if not new_stmt:
            new_stmt = stmt
        return new_stmt

    def render_html(self, *args, **kwargs) -> str:
        tabs = kwargs.get("tabs", "")
        template = self._ancestor.get_template(self._node["type"])

        return template.render(
            {
                "stmt_with_calls": bool(len(self._node["func_calls"])),
                "with_buttons": kwargs.get("with_buttons", True),
                "id": self._node["id"],
                "tabs": tabs,
                "stmt": self.form_stmt(with_buttons=kwargs.get("with_buttons", True)),
                "act_type_play": self.ACT_TYPE,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "act_name": self.ACT_NAME_TEMPLATE.get(self._node["type"]).format(
                    html_quote_escape(self._node["name"])
                ),
                "name": self._node["name"],
                "phase_label_stop": self.PHASE_LABEL_STOP,
            }
        )


class ExpressionRenderer(StatementRenderer):
    PHASE_LABEL_PLAY = "Вычислится"
    PHASE_LABEL_STOP = "Завершится"
    ACT_TYPE = "performed"
    ACT_NAME_TEMPLATE = {
        "expr": "условие `{}`",
        # "break": "остановка цикла",
        # "return": "возврат",
        # "continue": "переход к следующей итерации цикла",
        # "stmt": "действие `{}`",
        # "stmt_with_calls": "действие `{}`",
        "func_call": "вызов функции `{}` с аргументами `{}`",
    }


class FunctionRenderer(AbstractEntityRenderer):
    PHASE_LABEL_PLAY = "Выполнится"
    PHASE_LABEL_STOP = "Завершится"
    ACT_TYPE = "started"
    ACT_NAME = "выполнение тела функции {}"

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
                "seq_id": self._node["body"]["id"],
                "act_type_play": self.ACT_TYPE,
                "phase_label_play": self.PHASE_LABEL_PLAY,
                "phase_label_stop": self.PHASE_LABEL_STOP,
                "act_iter_name": self.ACT_NAME.format(self._node["name"]),
            }
        )


class JSON2HtmlBuilder:
    type2template = {
        "expr": "expr",
        "stmt": "stmt",
        "stmt_with_calls": "stmt",
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
        "stmt_with_calls": StatementRenderer,
        "expr": ExpressionRenderer,
        "stmt": StatementRenderer,
        "break": StatementRenderer,
        "return": StatementRenderer,
        "continue": StatementRenderer,
        "for_loop": ForLoopRenderer,
        "foreach_loop": ForLoopRenderer,
        "while_loop": WhileLoopRenderer,
    }

    def __init__(self, lang):
        directory = os.path.dirname(__file__)
        self.lang = lang
        file_loader = FileSystemLoader(os.path.join(directory, "templates"))
        self.env = Environment(loader=file_loader, trim_blocks=True)

    def get_template(self, node_type):
        ###
        print('get_template:', node_type)
        ###
        return self.env.get_template(
            f"{self.lang}/{self.type2template[node_type]}.html"
        )

    def get_renderer(self, node) -> AbstractEntityRenderer:
        ###
        print('get_renderer:', node["type"])
        ###
        if renderer := self.type2renderer.get(node["type"]):
            return renderer(node, self)

    def render_node(self, node, tabs=Tab(0), with_buttons=True) -> str:
        html = ""
        if renderer := self.get_renderer(node):
            html = renderer.render_html(tabs=tabs, with_buttons=with_buttons)
        return html

    def render_nodes(self, nodes, tabs=Tab(0), with_buttons=True) -> str:
        html = ""
        for element in nodes:
            if renderer := self.get_renderer(element):
                html += renderer.render_html(tabs=tabs, with_buttons=with_buttons)
        return html

    def build(self, obj: dict, with_buttons=True) -> str:
        functions = []
        # tabs = Tab(0)
        tabs = Tab(0)
        for function in obj["functions"]:
            if renderer := self.get_renderer(function):
                functions.append(
                    renderer.render_html(tabs=tabs, with_buttons=with_buttons)
                )
        global_html = self.render_nodes(
            obj["global_code"]["body"], tabs=tabs, with_buttons=with_buttons
        )
        ###
        # print(functions)
        ###
        return self.env.get_template("document.html").render(
            {"global_code": global_html, "functions": functions}
        )
