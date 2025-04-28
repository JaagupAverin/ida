from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, override

from msgspec.json import decode as decode_json

from woid import log
from woid.help import ErrorStrings, HelpStrings
from woid.log import json_dumps
from woid.version import __version__

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Host:
    name: str
    url: str

    def __init__(self, name: str, json: dict[str, Any]) -> None:
        self.name = name
        if url := json.get("url"):
            self.url = str(url)
        else:
            log.fatal(
                ErrorStrings.INVALID_WORKSPACE_JSON,
                issue=f"Host '{self.name}' does not define the required field 'url'.",
                erroneus_json=json_dumps(self.name, json),
                help=HelpStrings.JsonFields.HOST_URL,
            )

    @override
    def __repr__(self) -> str:
        return f"Host({self.name}, {self.url})"


@dataclass
class Project:
    name: str
    host: Host
    absolute_local_path: Path
    absolute_host_path: str

    def __init__(self, name: str, json: dict[str, Any], ws: Workspace) -> None:
        self.name = name

        if host_name := json.get("host"):
            if host := ws.hosts.get(host_name):
                self.host = host
                self.absolute_host_path = host.url + "/" + str(host_name)
            else:
                log.fatal(
                    ErrorStrings.INVALID_WORKSPACE_JSON,
                    issue=(
                        f"Project '{self.name}' references the host '{host_name}', "
                        + "which has not been defined in workspace.json."
                    ),
                    valid_hosts=list(ws.hosts.keys()),
                    erroneus_json=json_dumps(self.name, json),
                    help=HelpStrings.JsonFields.PROJECT_HOST,
                )
        else:
            log.fatal(
                ErrorStrings.INVALID_WORKSPACE_JSON,
                issue=f"Project '{self.name}' does not define the required field 'host'.",
                erroneus_json=json_dumps(self.name, json),
                help=HelpStrings.JsonFields.PROJECT_HOST,
            )

        self.absolute_local_path = ws.root_dir / self.name

    @override
    def __repr__(self) -> str:
        return f"Project({self.name}, {self.absolute_local_path})"


@dataclass
class Version:
    major: int
    minor: int


@dataclass
class Workspace:
    _woid_version: Version
    name: str
    root_dir: Path
    hosts: dict[str, Host]
    projects: dict[str, Project]

    @override
    def __repr__(self) -> str:
        return f"Workspace({self.name}, {len(self.hosts)} hosts, {len(self.projects)} projects)"

    def dump(self) -> dict[str, Any]:
        return {
            "woid-version": f"{self._woid_version.major}.{self._woid_version.minor}",
            "name": self.name,
            "root-dir": str(self.root_dir),
            "hosts": self.hosts,
            "projects": self.projects,
        }


def load_workspace(path: Path) -> Workspace:
    try:
        text = path.read_text()
    except Exception as e:  # noqa: BLE001
        log.fatal("Failed to read workspace JSON.", path=path, error=e)

    try:
        json = decode_json(text)
    except Exception as e:  # noqa: BLE001
        log.fatal("Failed to parse workspace JSON.", path=path, error=e)

    if woid_version := json.get("woid-version"):
        woid_version = str(woid_version)
        try:
            version_major, version_minor = woid_version.split(".")
        except ValueError:
            log.fatal("Failed to parse workspace version; expected `MAJOR.MINOR` (e.g. `0.1`).", version=woid_version)
    else:
        log.inf("Workspace JSON is missing 'woid-version' field; assuming latest version.")
        version_major, version_minor = __version__.split(".")

    if name := json.get("name"):
        name = str(name)
    else:
        log.fatal("Workspace JSON is missing 'name' field.", workspace=path)

    ws = Workspace(
        _woid_version=Version(int(version_major), int(version_minor)),
        name=name,
        root_dir=path.parent,
        hosts={},
        projects={},
    )

    if hosts := json.get("hosts"):
        for host_name, host_json in hosts.items():
            ws.hosts[host_name] = Host(name=host_name, json=host_json)
    else:
        log.fatal("Workspace JSON is missing 'hosts' field.", workspace=path, erroneus_json=json_dumps("root", json))

    if projects := json.get("projects"):
        for project_name, project_json in projects.items():
            ws.projects[project_name] = Project(name=project_name, json=project_json, ws=ws)
    else:
        log.fatal("Workspace JSON is missing 'projects' field.", workspace=path)

    log.inf("Workspace JSON parsed.", workspace=ws.dump())
    return ws


# TODO: Continue improving error messages and formatting :)
