"""
CIM Data Generator — Modular Input for continuous event streaming.

Each input stanza specifies a CIM data model, events per interval,
and target index. Events are generated as CIM-compliant JSON.
"""

import json
import os
import sys
import time

# Add bin/ to path for splunklib and generators
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from splunklib.modularinput import Script, Scheme, Argument, Event, EventWriter

from generators.base import GeneratorFactory
# Import all generators to register them
from generators import authentication, network_traffic, web, endpoint
from generators import malware, intrusion_detection, dns


MAX_EPS = 1000


class CIMGeneratorInput(Script):
    """Modular input that continuously streams CIM-compliant synthetic events."""

    def get_scheme(self):
        scheme = Scheme("CIM Data Generator")
        scheme.description = (
            "Generates CIM-compliant synthetic events for testing Splunk "
            "searches, dashboards, and correlation rules."
        )
        scheme.use_external_validation = False
        scheme.use_single_instance = False

        model_arg = Argument("model")
        model_arg.title = "CIM Data Model"
        model_arg.description = (
            "The CIM data model to generate. "
            "Supported: authentication, network_traffic, web, endpoint, "
            "malware, intrusion_detection, dns"
        )
        model_arg.data_type = Argument.data_type_string
        model_arg.required_on_create = True
        scheme.add_argument(model_arg)

        eps_arg = Argument("events_per_interval")
        eps_arg.title = "Events per Interval"
        eps_arg.description = "Number of events to generate each interval (max 1000)."
        eps_arg.data_type = Argument.data_type_number
        eps_arg.required_on_create = False
        scheme.add_argument(eps_arg)

        # Note: "index" is a reserved Splunk argument handled internally.
        # It is set in inputs.conf stanzas but must NOT be defined in the scheme.

        return scheme

    def stream_events(self, inputs, ew):
        """Generate and stream events for each active input stanza."""
        for stanza_name, stanza_params in inputs.inputs.items():
            model = stanza_params.get("model", "authentication")
            events_per_interval = int(stanza_params.get("events_per_interval", 10))
            index = stanza_params.get("index", "synthetic_cim")

            # Rate limiting
            events_per_interval = min(events_per_interval, MAX_EPS)

            try:
                generator = GeneratorFactory.create(model)
            except ValueError as e:
                ew.log(EventWriter.ERROR, str(e))
                continue

            sourcetype = generator.get_sourcetype()
            now = time.time()

            ew.log(
                EventWriter.INFO,
                "CIM Generator: Generating %d %s events for index=%s"
                % (events_per_interval, model, index)
            )

            events = generator.generate_batch(
                count=events_per_interval,
                base_time=now,
                timerange_seconds=60,  # Events within the last minute
            )

            for event_data in events:
                event = Event()
                event.stanza = stanza_name
                event.data = generator.format_event(event_data)
                event.index = index
                event.sourcetype = sourcetype
                event.time = event_data.get("_time", now)
                ew.write_event(event)


if __name__ == "__main__":
    sys.exit(CIMGeneratorInput().run(sys.argv))
