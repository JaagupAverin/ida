import time
from pathlib import Path
from typing import Annotated

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn, track

from woid import log
from woid.workspace import load_workspace

APP_NAME = "woid"
WORKSPACE_JSON_PATH = Path("woid.json")

app: typer.Typer = typer.Typer(name=APP_NAME, rich_markup_mode="rich")


@app.callback(invoke_without_command=True)
def woid(
    ctx: typer.Context,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Print out debug-level messages from woid.",
        ),
    ] = False,
) -> None:
    """A workspace management tool for multi-repository projects."""
    if verbose:
        log.dbg("Enabled Verbose output.")

    if ctx.invoked_subcommand:
        log.dbg(f"Running command `{ctx.invoked_subcommand}`.")

    _workspace = load_workspace(WORKSPACE_JSON_PATH)


class Panels:
    RepositoryManagement: str = "Repository management"


@app.command(rich_help_panel=Panels.RepositoryManagement, short_help="Initialize the project.")
def clone(
    url: Annotated[
        str,
        typer.Argument(
            help="Remote URL that contains the woid manifest.",
        ),
    ],
) -> None:
    """Initialize the workspace.

    Clones the given manifest repository and all projects.
    """
    log.inf(f"Cloning {url}")
    total = 0
    for _ in track(range(1000), description="Processing..."):
        time.sleep(0.01)
        total += 1
    log.inf(f"Processed {total} things.")


@app.command(rich_help_panel=Panels.RepositoryManagement)
def sync(
    rebase: Annotated[
        bool,
        typer.Option(
            "--rebase",
            "-r",
            help="Attempt to resolve conflicts using git --rebase",
        ),
    ] = False,
) -> None:
    """Initialize the workspace."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        _ = progress.add_task(description=f"Syncing {rebase}...", total=None)
        time.sleep(3)


if __name__ == "__main__":
    app()
