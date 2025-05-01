from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, override

from msgspec.json import decode as decode_json

from woid import log
from woid.common import WS_JSON_PATH
from woid.help import ErrorStrings, Help

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class Host:
    name: str
    url: str

    def __init__(self, name: str, json: dict[str, Any]) -> None:
        self.name = name
        if url := json.pop("url", None):
            self.url = str(url)
        else:
            log.fatal(
                ErrorStrings.INVALID_WORKSPACE_JSON,
                issue=f"Host '{self.name}' does not define the required field 'url'.",
                erroneous_json={self.name: json},
                help=Help.JsonFields.host_url(),
            )

        if len(json) != 0:
            log.wrn(f"Host '{self.name}' has extraneous fields: {list(json.keys())}")

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

        if host_name := json.pop("host", None):
            if host := ws.hosts.get(host_name):
                self.host = host
                self.absolute_host_path = host.url + "/" + str(host_name)
            else:
                log.fatal(
                    ErrorStrings.INVALID_WORKSPACE_JSON,
                    issue=(
                        f"Project '{self.name}' references the host '{host_name}', "
                        + f"which has not been defined in '{WS_JSON_PATH}'."
                    ),
                    valid_hosts=list(ws.hosts.keys()),
                    erroneous_json={self.name: json},
                    help=Help.JsonFields.project_host(),
                )
        else:
            log.fatal(
                ErrorStrings.INVALID_WORKSPACE_JSON,
                issue=f"Project '{self.name}' does not define the required field 'host'.",
                erroneous_json={self.name: json},
                help=Help.JsonFields.project_host(),
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
    root_dir: Path
    hosts: dict[str, Host]
    projects: dict[str, Project]

    @override
    def __repr__(self) -> str:
        return f"Workspace({self.root_dir}, {len(self.hosts)} hosts, {len(self.projects)} projects)"

    def dump(self) -> dict[str, Any]:
        return {
            "woid-version": f"{self._woid_version.major}.{self._woid_version.minor}",
            "root-dir": str(self.root_dir),
            "hosts": self.hosts,
            "projects": self.projects,
        }


def _parse_workspace_version(json: dict[str, Any]) -> Version:
    if woid_version := json.get("version"):
        woid_version = str(woid_version)
        try:
            version_major, version_minor = woid_version.split(".")
        except ValueError:
            log.fatal(
                ErrorStrings.INVALID_WORKSPACE_JSON,
                issue="Workspace version does not follow the format <MAJOR>.<MINOR> (e.g. '0.1').",
                erroneous_value=woid_version,
            )
    else:
        log.fatal(
            ErrorStrings.INVALID_WORKSPACE_JSON,
            issue="Workspace does not define the required field 'version'.",
            erroneous_json=json,
        )
    return Version(int(version_major), int(version_minor))


def _parse_workspace_hosts(json: dict[str, Any], ws: Workspace) -> None:
    if hosts := json.get("hosts"):
        for host_name, host_json in hosts.items():
            ws.hosts[host_name] = Host(name=host_name, json=host_json)
    else:
        log.fatal(
            ErrorStrings.INVALID_WORKSPACE_JSON,
            issue="Workspace does not define the required field 'hosts'.",
            erroneous_json=json,
        )


def _parse_workspace_projects(json: dict[str, Any], ws: Workspace) -> None:
    if projects := json.get("projects"):
        for project_name, project_json in projects.items():
            ws.projects[project_name] = Project(name=project_name, json=project_json, ws=ws)
    else:
        log.fatal(
            ErrorStrings.INVALID_WORKSPACE_JSON,
            issue="Workspace does not define the required field 'projects'.",
            erroneous_json=json,
        )


def load_workspace(path: Path) -> Workspace:
    try:
        text: str = path.read_text()
    except Exception as e:  # noqa: BLE001
        log.fatal(f"Failed to read '{WS_JSON_PATH}'.", path=path.absolute(), error=e)

    try:
        json: dict[str, Any] = decode_json(text)
    except Exception as e:  # noqa: BLE001
        log.fatal(f"Failed to decode '{WS_JSON_PATH}'.", path=path.absolute(), error=e, dump=text)

    version: Version = _parse_workspace_version(json)
    ws: Workspace = Workspace(
        _woid_version=version,
        root_dir=path.parent,
        hosts={},
        projects={},
    )
    _parse_workspace_hosts(json, ws)
    _parse_workspace_projects(json, ws)
    log.inf(f"Parsed '{WS_JSON_PATH}'.", workspace=ws.dump())
    return ws
