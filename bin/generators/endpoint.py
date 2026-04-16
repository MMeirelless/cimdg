"""Endpoint (Processes) CIM data model generator."""

import random

from generators.base import BaseGenerator, register_generator
from generators.correlation import SessionManager


# Realistic parent-child process relationships
PARENT_CHILD_MAP = {
    "services.exe": ["svchost.exe", "splunkd", "mysqld", "httpd", "nginx"],
    "explorer.exe": ["chrome.exe", "cmd.exe", "powershell.exe"],
    "svchost.exe": ["conhost.exe", "cmd.exe"],
    "cmd.exe": ["powershell.exe", "python3", "node", "java"],
    "init": ["cron", "systemd", "bash", "nginx", "httpd"],
    "systemd": ["splunkd", "postgres", "mysqld", "nginx", "cron"],
    "bash": ["python3", "node", "java", "cron"],
    "cron": ["bash", "python3"],
}

PROCESS_PATHS = {
    "svchost.exe": "C:\\Windows\\System32\\svchost.exe",
    "cmd.exe": "C:\\Windows\\System32\\cmd.exe",
    "powershell.exe": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "explorer.exe": "C:\\Windows\\explorer.exe",
    "chrome.exe": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "conhost.exe": "C:\\Windows\\System32\\conhost.exe",
    "python3": "/usr/bin/python3",
    "java": "/usr/bin/java",
    "splunkd": "/opt/splunk/bin/splunkd",
    "nginx": "/usr/sbin/nginx",
    "httpd": "/usr/sbin/httpd",
    "bash": "/bin/bash",
    "node": "/usr/bin/node",
    "postgres": "/usr/lib/postgresql/14/bin/postgres",
    "mysqld": "/usr/sbin/mysqld",
    "cron": "/usr/sbin/cron",
    "systemd": "/lib/systemd/systemd",
}


@register_generator("endpoint")
class EndpointGenerator(BaseGenerator):
    """
    Generates CIM-compliant Endpoint Processes events.

    Special behaviors:
    - Realistic parent-child process relationships
    - Process path consistency with process name
    - OS-consistent process selection
    """

    def __init__(self):
        super().__init__("endpoint")

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)

        # Pick a parent, then select a valid child
        parent = random.choice(list(PARENT_CHILD_MAP.keys()))
        children = PARENT_CHILD_MAP[parent]
        child = random.choice(children)

        event["parent_process"] = parent
        event["parent_process_name"] = parent
        event["process"] = child
        event["process_name"] = child

        # Set correct paths
        if child in PROCESS_PATHS:
            event["process_path"] = PROCESS_PATHS[child]
        if parent in PROCESS_PATHS:
            event["parent_process_path"] = PROCESS_PATHS[parent]

        # Ensure parent PID < child PID
        parent_pid = random.randint(100, 5000)
        child_pid = random.randint(parent_pid + 1, 65535)
        event["parent_process_id"] = parent_pid
        event["process_id"] = child_pid

        # Cross-model correlation: 15% chance to use active session
        if random.random() < 0.15:
            try:
                session = SessionManager().get_session()
                if session:
                    event["session_id"] = session["session_id"]
                    event["user"] = session["user"]
                    SessionManager().mark_model(session["session_id"], "endpoint")
            except Exception:
                pass

        return event
