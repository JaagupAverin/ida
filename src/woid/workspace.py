from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, override

from msgspec.json import decode as decode_json

from woid import log
from woid.common import PROJECTS_DIR, WS_JSON_PATH
from woid.help import ErrorStrings, Help
from git import Repo

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


    def dump(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
        }

class ProjectStatus(Enum):
    Uninitialized = "Uninitialized"
    Cloning = "Cloning"
    Initialized = "Initialized"

class ProjectTracking(Enum):
    Symlink = "Local directory symlink"
    DetachedAtCommit = "Detached at commit"
    AttachedToBranch = "Attached to a branch"

@dataclass
class Project:
    name: str
    host: Host
    absolute_local_path: Path
    absolute_host_path: str
    status: ProjectStatus
    tracking: ProjectTracking
    repo: Repo

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

        # TODO: Initialize and track host remote
        self.repo = Repo.init(path=self.absolute_local_path, mkdir=True, bare=True)

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "host_path": self.absolute_host_path,
            "local_path": str(self.absolute_local_path),
        }


@dataclass
class Version:
    major: int
    minor: int


@dataclass
class Workspace:
    _woid_version: Version
    root_dir: Path
    projects_dir: Path
    hosts: dict[str, Host]
    projects: dict[str, Project]

    def __init__(self, path: Path) -> None:
        try:
            text: str = path.read_text()
        except Exception as e:  # noqa: BLE001
            log.fatal(f"Failed to read '{WS_JSON_PATH}'.", path=path.absolute(), error=e)

        try:
            json: dict[str, Any] = decode_json(text)
        except Exception as e:  # noqa: BLE001
            log.fatal(f"Failed to decode '{WS_JSON_PATH}'.", path=path.absolute(), error=e, dump=text)

        self._woid_version = self._parse_workspace_version(json)
        self.root_dir = path.parent.absolute()
        self.projects_dir = self.root_dir / PROJECTS_DIR
        self.hosts = self._parse_workspace_hosts(json)
        self.projects = self._parse_workspace_projects(json)
        log.dbg(f"Parsed '{WS_JSON_PATH}'.", workspace=self.dump())


    def _parse_workspace_version(self, json: dict[str, Any]) -> Version:
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

    def _parse_workspace_hosts(self, json: dict[str, Any]) -> dict[str, Host]:
        res: dict[str, Host] = {}
        if hosts := json.get("hosts"):
            for host_name, host_json in hosts.items():
                res[host_name] = Host(name=host_name, json=host_json)
        else:
            log.fatal(
                ErrorStrings.INVALID_WORKSPACE_JSON,
                issue="Workspace does not define the required field 'hosts'.",
                erroneous_json=json,
            )
        return res


    def _parse_workspace_projects(self, json: dict[str, Any]) -> dict[str, Project]:
        res: dict[str, Project] = {}
        if projects := json.get("projects"):
            for project_name, project_json in projects.items():
                res[project_name] = Project(name=project_name, json=project_json, ws=self)
        else:
            log.fatal(
                ErrorStrings.INVALID_WORKSPACE_JSON,
                issue="Workspace does not define the required field 'projects'.",
                erroneous_json=json,
            )
        return res


    @override
    def __repr__(self) -> str:
        return f"Workspace({self.root_dir}, {len(self.hosts)} hosts, {len(self.projects)} projects)"

    def dump(self) -> dict[str, Any]:
        return {
            "woid-version": f"{self._woid_version.major}.{self._woid_version.minor}",
            "root-dir": str(self.root_dir),
            "projects-dir": str(self.projects_dir),
            "hosts": [h.dump() for h in self.hosts.values()],
            "projects": [p.dump() for p in self.projects.values()],
        }


def print_workspace_status(ws: Workspace) -> None:
    pass
