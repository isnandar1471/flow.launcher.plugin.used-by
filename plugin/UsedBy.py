# -*- coding: utf-8 -*-

from dataclasses import dataclass
from datetime import datetime
from os.path import exists
from pathlib import Path
from platform import system
from psutil import process_iter, Process, NoSuchProcess
from re import search
from subprocess import Popen
from typing import TypedDict, List

import pyperclip
from flowlauncher import FlowLauncher


# Define TypedDict for the data structure provided
class JsonRPCAction(TypedDict):
    method: str
    parameters: List[str]


class ContextData(TypedDict):
    pid: int
    create_time: float
    match_path: str


class FlowReturn(TypedDict):
    Title: str
    SubTitle: str
    IcoPath: str
    JsonRPCAction: None | JsonRPCAction
    ContextData: None | ContextData  # https://github.com/Flow-Launcher/docs/issues/49#issuecomment-1198576877


@dataclass
class SettingTemplate(TypedDict):
    pass


# Define the main class for the FlowLauncher plugin
class UsedBy(FlowLauncher):

    def query(self, param: str = "") -> List[FlowReturn]:
        # settings = SettingTemplate(**self.rpc_request["settings"])

        attrs = ["open_files", "pid", "create_time", "name", "cwd", "exe"]

        param = param.strip()

        # Initialize flags for regex, case insensitive, and check folder
        is_use_regex: bool = False
        is_use_case_insensitive: bool = False
        is_check_folder: bool = False

        if param.lower()[:3] in [":r "]:
            is_use_regex = True
            param = param[3:].strip()

        if param.lower()[:3] in [":i "]:
            is_use_case_insensitive = True
            param = param[3:].strip()

        if param.lower()[:3] in [":f "]:
            is_check_folder = True
            param = param[3:].strip()

        if param.lower()[:4] in [":ir ", ":ri "]:
            is_use_regex = True
            is_use_case_insensitive = True
            param = param[4:].strip()

        if param.lower()[:4] in [":if ", ":fi "]:
            is_use_regex = True
            is_check_folder = True
            param = param[4:].strip()

        if param.lower()[:4] in [":fr ", ":rf "]:
            is_use_regex = True
            is_check_folder = True
            param = param[4:].strip()

        if param.lower()[:5] in [":fir ", ":rif ", ":ifr ", ":rfi ", ":fri ", ":irf "]:
            is_use_regex = True
            is_use_case_insensitive = True
            is_check_folder = True
            param = param[5:].strip()

        # If the parameter is empty or just contains special characters, return an empty flow return
        if param.lower() in ["", ":", ":r", ":i", ":f", ":ir", ":ri", ":if", ":fi", ":fr", ":rf", ":fir", ":rif",
                             ":ifr", ":rfi", ":fri", ":irf"]:
            empty_flow_return: FlowReturn = {
                "Title": "Type a file / folder path to see the list of programs using it",
                "SubTitle": "Example: /path/to/file OR :ifr /path/to/file ",
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": None,
                "ContextData": None,
            }
            return [empty_flow_return]

        # List to store processes that match the criteria
        processes: List[dict] = []
        # Iterate through all processes and check their open files and current working directory
        for proc in process_iter(attrs=attrs, ad_value=None):

            open_files: list | None = proc.info["open_files"]
            if open_files is not None:
                for f in open_files:
                    new_proc_info: dict = proc.info.copy()
                    new_proc_info["match_path"]: str = f.path

                    # For cross-platform compatibility, standardize the path
                    current_path: str = Path(f.path).as_posix()

                    param_to_check: str = param
                    if is_use_case_insensitive:
                        param_to_check = param.lower()
                        current_path = current_path.lower()

                    if is_use_regex:
                        if search(param_to_check, current_path):
                            processes.append(new_proc_info)
                            break
                    else:
                        param_to_check = Path(param_to_check).as_posix()
                        if current_path == param_to_check:
                            processes.append(new_proc_info)
                            break

            if is_check_folder:
                cwd: str | None = proc.info["cwd"]
                if cwd is not None:
                    new_proc_info: dict = proc.info.copy()
                    new_proc_info["match_path"]: str = cwd

                    # For cross-platform compatibility, standardize the path
                    current_path: str = Path(cwd).as_posix()

                    param_to_check: str = param
                    if is_use_case_insensitive:
                        param_to_check = param.lower()
                        current_path = current_path.lower()

                    if is_use_regex:
                        if search(param_to_check, current_path):
                            processes.append(new_proc_info)
                            break
                    else:
                        param_to_check = Path(param_to_check).as_posix()
                        if current_path == param_to_check:
                            processes.append(new_proc_info)
                            break

        if len(processes) == 0:
            other_descs: List[str] = []
            if is_use_case_insensitive:
                other_descs.append("case insensitive")
            if is_use_regex:
                other_descs.append("regex")
            if is_check_folder:
                other_descs.append("folder check")

            flow_return: FlowReturn = {
                "Title": f"There are no processes using '{param}' " + (
                    ("with " + self._join_with_last_separator(items=other_descs, sep=", ", last_sep="and "))
                    if len(other_descs) > 0 else ""
                ),
                "SubTitle": "",
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": None,
                "ContextData": None,
            }
            return [flow_return]

        # Prepare the flow returns for each process found
        flow_returns: List[FlowReturn] = []
        for proc in processes:
            local_zone = datetime.now().astimezone().tzinfo
            dt = datetime.fromtimestamp(proc["create_time"], tz=local_zone)

            title: str = f"{proc["name"]} ({proc["pid"]})"
            sub_title: str = f"PATH: {proc["match_path"]} | CWD: {proc["cwd"]} | EXE: {proc["exe"]} | TIME: {dt.strftime("%Y-%m-%dT%H:%M:%S%z")}"

            flow_return: FlowReturn = {
                "Title": title,
                "SubTitle": sub_title,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "open_cwd",
                    "parameters": [proc["cwd"]]
                },
                "ContextData": {
                    "pid": proc["pid"],
                    "create_time": proc["create_time"],
                    "match_path": proc["match_path"],
                },
            }
            flow_returns.append(flow_return)

        return flow_returns

    def context_menu(self, data: None | ContextData = None) -> List[FlowReturn]:
        if data is None:
            return []

        pid: int = data["pid"]
        create_time: float = data["create_time"]

        proc: Process
        try:
            proc = Process(pid)
            if proc.create_time() != create_time:
                raise NoSuchProcess("Create Time doesnt match")
        except NoSuchProcess as e:
            return [{
                "Title": f"Process with PID {pid} not found",
                "SubTitle": e.msg,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": None,
                "ContextData": None,
            }]

        name: str = proc.name()
        cwd: str = proc.cwd()
        exe: str = proc.exe()
        match_path: str = data["match_path"]

        local_zone = datetime.now().astimezone().tzinfo
        dt = datetime.fromtimestamp(create_time, tz=local_zone)

        flow_returns: List[FlowReturn] = [
            {
                "Title": "Open CWD",
                "SubTitle": cwd,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "copy",
                    "parameters": [cwd],
                },
                "ContextData": None,
            },
            {
                "Title": "Copy Match Path",
                "SubTitle": match_path,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "copy",
                    "parameters": [match_path]
                },
                "ContextData": None,
            },
            {
                "Title": "Copy Name",
                "SubTitle": name,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "copy",
                    "parameters": [name],
                },
                "ContextData": None,
            },
            {
                "Title": "Copy PID",
                "SubTitle": f"{pid}",
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "copy",
                    "parameters": [f"{pid}"],
                },
                "ContextData": None,
            },
            {
                "Title": "Copy CWD",
                "SubTitle": cwd,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "copy",
                    "parameters": [cwd],
                },
                "ContextData": None,
            },
            {
                "Title": "Copy Exe",
                "SubTitle": exe,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "copy",
                    "parameters": [exe],
                },
                "ContextData": None,
            },
            {
                "Title": "Copy Create Time",
                "SubTitle": dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "copy",
                    "parameters": [dt.strftime("%Y-%m-%dT%H:%M:%S%z")],
                },
                "ContextData": None,
            },
            {
                "Title": "Terminate Process",
                "SubTitle": name,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "terminate_process",
                    "parameters": [pid, create_time],
                },
                "ContextData": None,
            },
            {
                "Title": "Kill Process",
                "SubTitle": name,
                "IcoPath": "assets/logo.png",
                "JsonRPCAction": {
                    "method": "kill_process",
                    "parameters": [pid, create_time],
                },
                "ContextData": None,
            }
        ]

        return flow_returns

    def copy(self, data):
        pyperclip.copy(data)

    def open_cwd(self, cwd_path: str):
        if not exists(cwd_path):
            self.debug(f"Path does not exist: {cwd_path}")
            return

        os_name = system()

        match os_name:
            case "Windows":
                return Popen(f'explorer "{cwd_path}"')
            case "Linux":
                return Popen(["xdg-open", cwd_path])
            case "Darwin":
                return Popen(["open", cwd_path])
            case _:
                self.debug(f"Unsupported OS: {os_name}")

    def terminate_process(self, pid: int, create_time: float):
        try:
            proc = Process(pid)
            if proc.create_time() != create_time:
                raise NoSuchProcess("create_time doesnt match")

            proc.terminate()
        except NoSuchProcess:
            self.debug(f"Process with PID {pid} not found or already terminated.")

    def kill_process(self, pid: int, create_time: int):
        try:
            proc = Process(pid)
            if proc.create_time() != create_time:
                raise NoSuchProcess("create_time doesnt match")

            proc.kill()
        except NoSuchProcess:
            self.debug(f"Process with PID {pid} not found or already terminated.")

    def _join_with_last_separator(self, items: List[str], sep: str, last_sep: str) -> str:
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return items[0] + last_sep + items[1]
        else:
            return sep.join(items[:-1]) + sep + last_sep + items[-1]


if __name__ == "__main__":
    UsedBy()
