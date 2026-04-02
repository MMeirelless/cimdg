"""Web CIM data model generator."""

import random

from generators.base import BaseGenerator, register_generator


@register_generator("web")
class WebGenerator(BaseGenerator):
    """
    Generates CIM-compliant Web (Proxy) events.

    Special behaviors:
    - URL/domain/path consistency
    - Status code correlations with action
    - Bytes correlation with content type
    """

    def __init__(self):
        super().__init__("web")

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)

        # Make URL components consistent
        domain = event.get("url_domain", event.get("dest", "example.com"))
        path = event.get("uri_path", "/")
        event["dest"] = domain
        event["url_domain"] = domain
        event["url"] = f"https://{domain}{path}"
        event["uri_path"] = path

        # Correlate status with action
        status = int(event.get("status", 200))
        if status >= 400:
            if status in (401, 403):
                event["action"] = "blocked"
            elif status >= 500:
                # Server errors are still "allowed" from proxy perspective
                event["action"] = "allowed"

        # Blocked actions get 403
        if event.get("action") == "blocked" and status < 400:
            event["status"] = "403"

        # Bytes correlation with content type
        content_type = event.get("http_content_type", "text/html")
        if "image" in content_type:
            event["bytes_out"] = random.randint(10000, 500000)
        elif "json" in content_type:
            event["bytes_out"] = random.randint(100, 50000)

        event["bytes_in"] = event.get("bytes_in", 0)
        event["bytes_out"] = event.get("bytes_out", 0)
        event["bytes"] = event["bytes_in"] + event["bytes_out"]

        return event
