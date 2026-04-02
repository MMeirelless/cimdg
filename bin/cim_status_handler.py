"""
CIM Data Generator — REST handler for generation status.

Endpoints:
    GET /services/cimdg/status — Report active generators and status
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from splunk.persistconn.application import PersistentServerConnectionApplication
import splunk.rest as rest

from generators.base import GeneratorFactory
from generators import authentication, network_traffic, web, endpoint
from generators import malware, intrusion_detection, dns


class StatusHandler(PersistentServerConnectionApplication):
    """Handle status requests — report active generators."""

    def __init__(self, command_line, command_arg):
        PersistentServerConnectionApplication.__init__(self)

    def handle(self, in_string):
        try:
            args = json.loads(in_string)
            method = args.get("method", "GET")

            if method != "GET":
                return {
                    "status": 405,
                    "payload": json.dumps({"error": "Method not allowed"}),
                }

            return self._handle_get(args)
        except Exception as e:
            return {
                "status": 500,
                "payload": json.dumps({"error": str(e)}),
            }

    def _handle_get(self, args):
        """Get status of active modular inputs."""
        session_key = args["session"]["authtoken"]

        try:
            response, content = rest.simpleRequest(
                "/services/data/inputs/cim_synthetic_data",
                sessionKey=session_key,
                getargs={"output_mode": "json", "count": 0},
                method="GET",
            )

            if isinstance(content, bytes):
                content = content.decode("utf-8")
            input_data = json.loads(content)

            inputs = []
            for entry in input_data.get("entry", []):
                inputs.append({
                    "name": entry.get("name", ""),
                    "model": entry.get("content", {}).get("model", ""),
                    "disabled": entry.get("content", {}).get("disabled", "1"),
                    "index": entry.get("content", {}).get("index", "synthetic_cim"),
                    "events_per_interval": entry.get("content", {}).get(
                        "events_per_interval", "10"
                    ),
                    "interval": entry.get("content", {}).get("interval", "60"),
                })

            active = [i for i in inputs if i["disabled"] == "0"]

            return {
                "status": 200,
                "payload": json.dumps({
                    "inputs": inputs,
                    "active_count": len(active),
                    "total_count": len(inputs),
                    "supported_models": GeneratorFactory.list_models(),
                }),
            }
        except Exception as e:
            return {
                "status": 200,
                "payload": json.dumps({
                    "inputs": [],
                    "active_count": 0,
                    "total_count": 0,
                    "supported_models": GeneratorFactory.list_models(),
                    "note": "Could not fetch input status: %s" % str(e),
                }),
            }
