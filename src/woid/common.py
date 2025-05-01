from pathlib import Path

WS_JSON_PATH: Path = Path("woid.json")

_verbose: bool = False


def get_verbose() -> bool:
    return _verbose


def set_verbose(verbose: bool) -> None:
    global _verbose  # noqa: PLW0603
    _verbose = verbose
