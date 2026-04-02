"""Intrusion Detection CIM data model generator."""

import random

from generators.base import BaseGenerator, register_generator


# Signature-severity correlation
SIGNATURE_SEVERITY = {
    "CVE-2021-44228 Log4j RCE Attempt": "critical",
    "ET EXPLOIT Apache Struts RCE": "critical",
    "SQL Injection Attempt": "high",
    "Cross-Site Scripting (XSS) Attempt": "high",
    "SSH Brute Force Attempt": "medium",
    "RDP Brute Force Attempt": "medium",
    "ET MALWARE CnC Beacon Activity": "high",
    "Directory Traversal Attempt": "medium",
    "ET SCAN Nmap Scripting Engine User-Agent": "low",
    "Port Scan Detected": "low",
    "DNS Tunneling Detected": "high",
    "ET POLICY Outbound SMB Connection": "low",
}

# Category-signature correlation
CATEGORY_SIGNATURES = {
    "exploit": [
        "CVE-2021-44228 Log4j RCE Attempt",
        "ET EXPLOIT Apache Struts RCE",
    ],
    "web-application-attack": [
        "SQL Injection Attempt",
        "Cross-Site Scripting (XSS) Attempt",
        "Directory Traversal Attempt",
    ],
    "brute-force": [
        "SSH Brute Force Attempt",
        "RDP Brute Force Attempt",
    ],
    "reconnaissance": [
        "ET SCAN Nmap Scripting Engine User-Agent",
        "Port Scan Detected",
    ],
    "malware-cnc": [
        "ET MALWARE CnC Beacon Activity",
        "DNS Tunneling Detected",
    ],
}


@register_generator("intrusion_detection")
class IntrusionDetectionGenerator(BaseGenerator):
    """
    Generates CIM-compliant Intrusion Detection events.

    Special behaviors:
    - Signature/severity correlation
    - Category/signature consistency
    - Critical events are more likely blocked
    """

    def __init__(self):
        super().__init__("intrusion_detection")

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)

        # Ensure category-signature consistency
        category = event.get("category", "exploit")
        if category in CATEGORY_SIGNATURES:
            event["signature"] = random.choice(CATEGORY_SIGNATURES[category])

        # Correlate severity with signature
        signature = event.get("signature", "")
        if signature in SIGNATURE_SEVERITY:
            event["severity"] = SIGNATURE_SEVERITY[signature]

        # Critical/high severity events are more likely blocked
        severity = event.get("severity", "medium")
        if severity in ("critical", "high"):
            if random.random() < 0.85:
                event["action"] = "blocked"

        return event
