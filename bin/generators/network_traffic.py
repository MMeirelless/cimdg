"""Network Traffic CIM data model generator."""

import random

from generators.base import BaseGenerator, register_generator
from generators.correlation import SessionManager


# Protocol-port mapping for realistic correlations
PORT_PROTOCOL_MAP = {
    443: "tcp", 80: "tcp", 22: "tcp", 25: "tcp", 110: "tcp",
    993: "tcp", 8080: "tcp", 8443: "tcp", 3389: "tcp",
    53: "udp", 123: "udp", 161: "udp", 514: "udp",
}

PORT_APP_MAP = {
    443: "ssl", 80: "http", 22: "ssh", 53: "dns",
    25: "smtp", 8080: "http", 8443: "ssl", 3389: "rdp",
}


@register_generator("network_traffic")
class NetworkTrafficGenerator(BaseGenerator):
    """
    Generates CIM-compliant Network Traffic events.

    Special behaviors:
    - Port-to-protocol and port-to-app correlation
    - Bytes/packets consistency (bytes > packets * ~40)
    - Bidirectional bytes calculation
    """

    def __init__(self):
        super().__init__("network_traffic")

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)

        dest_port = event.get("dest_port", 443)

        # Correlate transport with port
        if dest_port in PORT_PROTOCOL_MAP:
            event["transport"] = PORT_PROTOCOL_MAP[dest_port]

        # Correlate app with port
        if dest_port in PORT_APP_MAP:
            event["app"] = PORT_APP_MAP[dest_port]

        # Ensure bytes consistency
        bytes_in = event.get("bytes_in", 0)
        bytes_out = event.get("bytes_out", 0)
        event["bytes"] = bytes_in + bytes_out

        # Ensure packets consistency (avg ~500-1500 bytes per packet)
        avg_pkt_size = random.randint(500, 1500)
        if bytes_in > 0:
            event["packets_in"] = max(1, int(bytes_in / avg_pkt_size))
        if bytes_out > 0:
            event["packets_out"] = max(1, int(bytes_out / avg_pkt_size))
        event["packets"] = event.get("packets_in", 0) + event.get("packets_out", 0)

        # Make src/dest IPs consistent with named fields
        event["src"] = event.get("src_ip", event.get("src"))
        event["dest"] = event.get("dest_ip", event.get("dest"))

        # Cross-model correlation: 20% chance to use active session
        if random.random() < 0.20:
            try:
                session = SessionManager().get_session()
                if session:
                    event["session_id"] = session["session_id"]
                    event["src"] = session["src"]
                    event["src_ip"] = session["src"]
                    SessionManager().mark_model(session["session_id"], "network_traffic")
            except Exception:
                pass

        return event
