"""Brute Force Attack playbook.

Timeline:
1. 20-50 authentication failures from single external IP (0-120s)
2. Authentication success  -  attacker guessed password (125s)
3. Network connection from attacker IP (130s)
4. Web access from attacker IP (135s)
5. Process execution by compromised user (140s)
"""

import random

from playbooks.base import BasePlaybook, register_playbook
from generators.base import EntityPool


@register_playbook("brute_force")
class BruteForcePlaybook(BasePlaybook):

    name = "brute_force"
    description = "Brute force authentication attack with lateral access"

    def build_timeline(self):
        pool = EntityPool()
        attacker_ip = pool.random_external_ip()
        target_user = pool.random_username()
        target_host = pool.random_hostname()

        self.timeline = []

        # Phase 1: Auth failures (0-120s)
        num_failures = random.randint(20, 50)
        for i in range(num_failures):
            offset = random.uniform(0, 120)
            self.timeline.append((offset, "authentication", {
                "action": "failure",
                "src": attacker_ip,
                "user": target_user,
                "dest": target_host,
                "reason": "invalid_password",
                "signature": "An account failed to log on",
                "signature_id": "4625",
            }))

        # Phase 2: Successful auth (125s)
        self.timeline.append((125, "authentication", {
            "action": "success",
            "src": attacker_ip,
            "user": target_user,
            "dest": target_host,
            "signature": "An account was successfully logged on",
            "signature_id": "4624",
        }))

        # Phase 3: Network connection (130s)
        self.timeline.append((130, "network_traffic", {
            "src": attacker_ip,
            "src_ip": attacker_ip,
            "dest": target_host,
            "action": "allowed",
            "direction": "inbound",
        }))

        # Phase 4: Web access (135s)
        self.timeline.append((135, "web", {
            "src": attacker_ip,
            "user": target_user,
            "action": "allowed",
        }))

        # Phase 5: Process execution (140s)
        self.timeline.append((140, "endpoint", {
            "user": target_user,
            "dest": target_host,
            "process": "powershell.exe",
            "process_name": "powershell.exe",
            "process_path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "parent_process": "cmd.exe",
            "parent_process_name": "cmd.exe",
        }))

        # Sort by offset
        self.timeline.sort(key=lambda x: x[0])
