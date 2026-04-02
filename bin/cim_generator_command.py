"""
CIM Data Generator — Custom Search Command.

Usage:
    | cimgenerate model="Authentication" count=100 timerange="-24h"
    | collect index=synthetic_cim

Generates CIM-compliant synthetic events as search results.
"""

import os
import sys
import time

# Add bin/ to path for splunklib and generators
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from splunklib.searchcommands import (
    dispatch,
    GeneratingCommand,
    Configuration,
    Option,
    validators,
)

from generators.base import GeneratorFactory
# Import all generators to register them
from generators import authentication, network_traffic, web, endpoint
from generators import malware, intrusion_detection, dns


# Timerange string to seconds
TIMERANGE_MAP = {
    "-5m": 300,
    "-15m": 900,
    "-30m": 1800,
    "-1h": 3600,
    "-4h": 14400,
    "-8h": 28800,
    "-24h": 86400,
    "-7d": 604800,
    "-30d": 2592000,
}


def parse_timerange(timerange_str):
    """Convert a timerange string like '-24h' to seconds."""
    if timerange_str in TIMERANGE_MAP:
        return TIMERANGE_MAP[timerange_str]

    # Try parsing numeric suffix
    tr = timerange_str.lstrip("-")
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    for suffix, mult in multipliers.items():
        if tr.endswith(suffix):
            try:
                return int(tr[:-1]) * mult
            except ValueError:
                pass

    return 3600  # Default 1 hour


@Configuration(type="events")
class CIMGenerateCommand(GeneratingCommand):
    """Generates CIM-compliant synthetic events."""

    model = Option(
        doc="CIM data model to generate (e.g., Authentication, network_traffic)",
        require=True,
    )

    count = Option(
        doc="Number of events to generate (default: 100, max: 100000)",
        require=False,
        default=100,
        validate=validators.Integer(minimum=1, maximum=100000),
    )

    timerange = Option(
        doc="Time range for generated events (e.g., -1h, -24h, -7d). Default: -1h",
        require=False,
        default="-1h",
    )

    def generate(self):
        model_name = self.model.lower().strip()

        try:
            generator = GeneratorFactory.create(model_name)
        except ValueError as e:
            self.error_exit(
                e, "Supported models: %s" % ", ".join(GeneratorFactory.SUPPORTED_MODELS)
            )
            return

        count = int(self.count)
        timerange_seconds = parse_timerange(self.timerange)
        now = time.time()
        sourcetype = generator.get_sourcetype()

        events = generator.generate_batch(
            count=count,
            base_time=now,
            timerange_seconds=timerange_seconds,
        )

        for event_data in events:
            result = dict(event_data)
            result["_raw"] = generator.format_event(event_data)
            result["sourcetype"] = sourcetype
            result["source"] = "cimgenerate"
            result["host"] = "cimdg"
            yield result


if __name__ == "__main__":
    dispatch(CIMGenerateCommand, sys.argv, sys.stdin, sys.stdout, __name__)
