"""Performance CIM data model generator."""

import random

from generators.base import BaseGenerator, register_generator


@register_generator("performance")
class PerformanceGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("performance")

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)

        # 5% of hosts in "stressed" state
        if random.random() < 0.05:
            event["cpu_load_percent"] = round(random.uniform(90, 100), 1)
            mem_total = event.get("mem", 16384)
            event["mem_used"] = int(mem_total * random.uniform(0.85, 0.98))
            event["mem_free"] = mem_total - event["mem_used"]
            event["storage_used_percent"] = round(random.uniform(85, 98), 1)
        else:
            mem_total = event.get("mem", 16384)
            event["mem_used"] = int(mem_total * random.uniform(0.3, 0.7))
            event["mem_free"] = mem_total - event["mem_used"]

        return event
