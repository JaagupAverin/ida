import logging
import sys
from functools import cache
from json import dumps
from typing import Any, NoReturn

import structlog
from rich.console import Console
from rich.table import Table, box
from rich.theme import Theme

_custom_log_themes = Theme(
    {
        "warning": "yellow",
        "error": "red",
        "critical": "red",
        "info": "white",
        "debug": "white",
        "code": "dim white",
    }
)


def _console_printer(
    _logger: structlog.types.WrappedLogger,
    _method_name: str,
    event_dict: structlog.types.EventDict,
) -> str:
    console = Console(theme=_custom_log_themes)
    console.begin_capture()
    level: str = event_dict["level"]
    match level:
        case "warning":
            lvl = "WARNING: "
        case "error":
            lvl = "ERROR: "
        case _:
            lvl = ""

    # Print out the primary event message; derive color from error level:
    fmt: str = f"[{level}][{event_dict['timestamp']}] {lvl}{event_dict['event']}[/]"
    console.print(fmt)

    # These values are already printed above, no need to duplicate them:
    for key in ["level", "timestamp", "event"]:
        if key in event_dict:
            event_dict.pop(key)

    # Format event dictionary into a Rich Table:
    if event_dict:
        table = Table(box=box.MINIMAL, show_header=False, show_lines=True)
        table.add_column("name", justify="right", style=level, width=11, overflow="fold")
        table.add_column("value", style="white", width=80)
        for key, value in event_dict.items():
            prettified_value = str(value).strip()
            table.add_row(key.replace("_", " "), prettified_value)
        console.print(table)

    return console.end_capture()


@cache
def get_logger() -> structlog.types.FilteringBoundLogger:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
            _console_printer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    return structlog.get_logger()


def dbg(msg: str, **kwargs: Any) -> None:  # noqa: ANN401
    get_logger().debug(msg, **kwargs)


def inf(msg: str, **kwargs: Any) -> None:  # noqa: ANN401
    get_logger().info(msg, **kwargs)


def wrn(msg: str, **kwargs: Any) -> None:  # noqa: ANN401
    get_logger().warning(msg, **kwargs)


def err(msg: str, **kwargs: Any) -> None:  # noqa: ANN401
    get_logger().error(msg, **kwargs)


def fatal(msg: str, **kwargs: Any) -> NoReturn:  # noqa: ANN401
    err(msg, **kwargs)
    sys.exit(-1)


def json_dumps(key: str, value: dict[str, Any]) -> str:
    """This is like the regular json.dumps(), except it does not wrap the final document in curly brackets."""
    return f'"{key}": ' + dumps(value, indent=2, default=lambda o: str(o))
