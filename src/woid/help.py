from dataclasses import dataclass
from functools import cache

from msgspec.json import decode
from rich import pretty
from rich.console import ConsoleRenderable, Group
from rich.highlighter import ReprHighlighter
from rich.panel import Panel
from rich.text import Text

from woid.common import WS_JSON_PATH, is_verbose


@dataclass
class Field:
    name: str
    help: str
    required: bool


@dataclass
class Example:
    name: str
    code: str


def _create_help(fields: list[Field], examples: list[Example]) -> ConsoleRenderable:
    renderables: list[ConsoleRenderable] = []
    try:
        for field in fields:
            arg_render = Text.from_markup(f"[u]{field.name}[/u]: {field.help}\n")
            renderables.append(arg_render)

        if is_verbose():
            for i, example in enumerate(examples):
                prettified_value = pretty.Pretty(
                    decode(example.code),
                    highlighter=ReprHighlighter(),
                    indent_guides=True,
                    expand_all=True,
                )
                title = f"Example #{i + 1}: {example.name}"
                example_panel = Panel(prettified_value, title=title, border_style="green", title_align="left")
                renderables.append(example_panel)
        else:
            renderables.append(Text.from_markup("Use [green]woid -v[/green] for examples."))
        return Group(*renderables)
    except Exception:  # noqa: BLE001
        return Group(Text("Failed to create help string (internal woid error).", style="red"))


class Help:
    class JsonFields:
        @cache
        @staticmethod
        def host_url() -> ConsoleRenderable:
            fields = [
                Field(
                    name="url",
                    help="https/git URL of a git server that hosts projects.",
                    required=True,
                )
            ]

            examples = [
                Example(
                    name="HTTPS host",
                    code="""
                        {
                            "hosts": {
                                "google": {
                                    "url": "https://github.com/google"
                                }
                            }
                        }""",
                )
            ]

            return _create_help(fields, examples)

        @cache
        @staticmethod
        def project_host() -> ConsoleRenderable:
            fields = [
                Field(
                    name="host",
                    help="Name of the host that has this project.",
                    required=True,
                )
            ]
            examples = [
                Example(
                    name="One host, two projects",
                    code="""
                        {
                            "hosts": {
                                "libs-provider": {
                                    "url": "https://bitbucket.org/libs-provider"
                                }
                            },
                            "projects": {
                                "lib-a": {
                                    "host": "libs-provider"
                                },
                                "lib-b": {
                                    "host": "libs-provider"
                                }
                            }
                        }
                        """,
                )
            ]
            return _create_help(fields, examples)


class ErrorStrings:
    INVALID_WORKSPACE_JSON: str = f"Failed to parse '{WS_JSON_PATH}'."
