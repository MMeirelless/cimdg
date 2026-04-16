"""Data Exfiltration playbook.

Timeline:
1. Authentication from internal user (0s)
2. Multiple filesystem reads  -  data staging (60s)
3. DNS queries to suspicious domains  -  C2 channel (120s)
4. Large outbound network transfer (180s)
5. DLP alert (240s)
6. Web upload to external service (300s)
"""

import random

from playbooks.base import BasePlaybook, register_playbook
from generators.base import EntityPool


@register_playbook("data_exfiltration")
class DataExfiltrationPlaybook(BasePlaybook):

    name = "data_exfiltration"
    description = "Data exfiltration via DNS tunneling and web upload"

    def build_timeline(self):
        pool = EntityPool()
        insider = pool.random_username()
        insider_ip = pool.random_internal_ip()
        insider_host = pool.random_hostname()

        self.timeline = []

        # Phase 1: Authentication (0s)
        self.timeline.append((0, "authentication", {
            "action": "success",
            "user": insider,
            "src": insider_ip,
            "dest": insider_host,
            "signature": "An account was successfully logged on",
            "signature_id": "4624",
        }))

        # Phase 2: Filesystem reads  -  staging data (30-90s)
        sensitive_files = [
            "/data/customer_records.db",
            "/data/financial_reports/q4_2026.xlsx",
            "/data/hr/employee_ssn.csv",
            "/data/engineering/source_code.tar.gz",
            "/data/contracts/vendor_agreements.pdf",
        ]
        for i, fname in enumerate(sensitive_files):
            self.timeline.append((30 + i * 12, "endpoint_filesystem", {
                "action": "read",
                "user": insider,
                "dest": insider_host,
                "file_path": fname,
                "file_name": fname.split("/")[-1],
            }))

        # Phase 3: DNS queries to suspicious domains (120-150s)
        suspicious_domains = ["xkqpwm.xyz", "data-sync-cdn.top", "api-metrics.cc"]
        for i, domain in enumerate(suspicious_domains):
            self.timeline.append((120 + i * 10, "dns", {
                "src": insider_ip,
                "query": domain,
                "message_type": "Query",
                "query_type": "TXT",
            }))

        # Phase 4: Large outbound transfer (180s)
        self.timeline.append((180, "network_traffic", {
            "src": insider_ip,
            "src_ip": insider_ip,
            "dest": pool.random_external_ip(),
            "action": "allowed",
            "direction": "outbound",
            "bytes_out": random.randint(50000000, 200000000),
            "bytes_in": random.randint(1000, 5000),
            "dest_port": 443,
            "transport": "tcp",
        }))

        # Phase 5: DLP alert (240s)
        self.timeline.append((240, "dlp", {
            "action": "allowed",
            "user": insider,
            "dlp_type": "PII",
            "file_name": "customer_records.db",
            "severity": "critical",
            "policy": "PII Detection",
        }))

        # Phase 6: Web upload (300s)
        self.timeline.append((300, "web", {
            "src": insider_ip,
            "user": insider,
            "http_method": "POST",
            "url": "https://file-share-external.com/upload",
            "dest": "file-share-external.com",
            "bytes_out": random.randint(50000000, 200000000),
            "status": "200",
            "action": "allowed",
        }))

        self.timeline.sort(key=lambda x: x[0])
