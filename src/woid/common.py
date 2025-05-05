from pathlib import Path

WS_JSON_PATH: Path = Path("woid.json")
PROJECTS_DIR: Path = Path("projects/")

_verbose: bool = False


def is_verbose() -> bool:
    return _verbose


def set_verbose(verbose: bool) -> None:
    global _verbose  # noqa: PLW0603
    _verbose = verbose
