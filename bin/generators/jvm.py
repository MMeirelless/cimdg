"""JVM CIM data model generator."""

import random

from generators.base import BaseGenerator, register_generator


@register_generator("jvm")
class JVMGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("jvm")

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)
        # Ensure heap_used < heap_max
        heap_max = event.get("heap_max", 8192)
        event["heap_used"] = min(event.get("heap_used", 1000), int(heap_max * 0.95))
        return event
