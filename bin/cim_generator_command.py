"""
CIM Data Generator  -  Custom Search Command.

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

import generators  # noqa: F401  -  auto-discovers and registers all generators
from generators.base import GeneratorFactory


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
        require=False,
    )

    playbook = Option(
        doc="Attack playbook to execute (e.g., brute_force, lateral_movement, data_exfiltration)",
        require=False,
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

    pool_size = Option(
        doc="Number of entities per pool (IPs, users, hosts). Default: 50",
        require=False,
        default=50,
        validate=validators.Integer(minimum=5, maximum=500),
    )

    external_ratio = Option(
        doc="Percentage of external IPs in src traffic (0-100). Default: 20",
        require=False,
        default=20,
        validate=validators.Integer(minimum=0, maximum=100),
    )

    def generate(self):
        # Apply pool overrides if non-default
        pool_size = int(self.pool_size)
        external_ratio = int(self.external_ratio)
        if pool_size != 50 or external_ratio != 20:
            from generators.base import EntityPool
            pool = EntityPool()
            pool.external_ratio = external_ratio / 100.0

        # Playbook mode: generate a multi-model attack scenario
        if self.playbook:
            from playbooks.base import PlaybookFactory
            from playbooks import brute_force, lateral_movement, data_exfiltration  # noqa

            try:
                pb = PlaybookFactory.create(self.playbook)
            except ValueError as e:
                self.error_exit(e, str(e))
                return

            import json
            results = pb.execute(base_time=time.time())
            for item in results:
                event_data = item["event"]
                result = dict(event_data)
                result["_raw"] = json.dumps(event_data, separators=(",", ":"))
                result["sourcetype"] = item["sourcetype"]
                result["source"] = "cimgenerate:playbook:%s" % self.playbook
                result["host"] = "cimdg"
                yield result
            return

        # Standard model mode
        if not self.model:
            self.error_exit(
                Exception("Either 'model' or 'playbook' parameter is required."),
                "Specify model=<name> or playbook=<name>"
            )
            return

        model_name = self.model.lower().strip()

        try:
            generator = GeneratorFactory.create(model_name)
        except ValueError as e:
            self.error_exit(
                e, "Supported models: %s" % ", ".join(GeneratorFactory.list_models())
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
