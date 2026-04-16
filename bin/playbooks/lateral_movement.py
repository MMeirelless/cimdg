"""Lateral Movement playbook.

Timeline:
1. Authentication success on Host A (0s)
2. Process execution (PsExec) on Host A (10s)
3. Network traffic from Host A to Host B (SMB/445) (15s)
4. Authentication success on Host B (20s)
5. Process execution on Host B (30s)
6. Repeat for Host C (40-60s)
"""

import random

from playbooks.base import BasePlaybook, register_playbook
from generators.base import EntityPool


@register_playbook("lateral_movement")
class LateralMovementPlaybook(BasePlaybook):

    name = "lateral_movement"
    description = "Lateral movement across multiple hosts via SMB/PsExec"

    def build_timeline(self):
        pool = EntityPool()
        attacker_user = pool.random_username()
        hosts = [pool.random_hostname() for _ in range(3)]
        host_ips = [pool.random_internal_ip() for _ in range(3)]

        self.timeline = []

        for hop, (host, host_ip) in enumerate(zip(hosts, host_ips)):
            base_offset = hop * 20

            # Auth on this host
            self.timeline.append((base_offset, "authentication", {
                "action": "success",
                "user": attacker_user,
                "src": host_ips[hop - 1] if hop > 0 else pool.random_internal_ip(),
                "dest": host,
                "signature": "An account was successfully logged on",
                "signature_id": "4624",
                "authentication_method": "kerberos" if hop > 0 else "password",
            }))

            # Process execution (PsExec pattern)
            self.timeline.append((base_offset + 5, "endpoint", {
                "user": attacker_user,
                "dest": host,
                "process": "PSEXESVC.exe" if hop > 0 else "cmd.exe",
                "process_name": "PSEXESVC.exe" if hop > 0 else "cmd.exe",
                "parent_process": "services.exe",
                "parent_process_name": "services.exe",
            }))

            # Network traffic to next host (if not last)
            if hop < len(hosts) - 1:
                next_ip = host_ips[hop + 1]
                self.timeline.append((base_offset + 10, "network_traffic", {
                    "src": host_ip,
                    "src_ip": host_ip,
                    "dest": next_ip,
                    "dest_ip": next_ip,
                    "dest_port": 445,
                    "transport": "tcp",
                    "app": "smb",
                    "action": "allowed",
                }))

        self.timeline.sort(key=lambda x: x[0])
