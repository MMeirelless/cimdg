"""Network Sessions CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("network_sessions")
class NetworkSessionsGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("network_sessions")

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)
        # Ensure src fields are consistent
        event["src"] = event.get("src_ip", event.get("src"))
        event["dest"] = event.get("dest_ip", event.get("dest"))
        return event
