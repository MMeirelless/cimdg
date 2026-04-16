"""
CIM Data Generator  -  REST handler for generation status.

Endpoints:
    GET  /services/cimdg/status  -  Report active generators and status
    POST /services/cimdg/status  -  Enable/disable a modular input
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from splunk.persistconn.application import PersistentServerConnectionApplication
import splunk.rest as rest

import generators  # noqa: F401  -  auto-discovers and registers all generators
from generators.base import GeneratorFactory

SCHEME = "cim_synthetic_data"

MODEL_CATEGORIES = {
    "authentication": "Security",
    "network_traffic": "Security",
    "web": "Security",
    "endpoint": "Security",
    "endpoint_filesystem": "Security",
    "endpoint_registry": "Security",
    "endpoint_services": "Security",
    "endpoint_ports": "Security",
    "malware": "Security",
    "intrusion_detection": "Security",
    "dns": "Security",
    "vulnerabilities": "Security",
    "alerts": "Security",
    "dlp": "Security",
    "email": "Security",
    "network_sessions": "Security",
    "change": "Operations",
    "certificates": "Infrastructure",
    "updates": "Operations",
    "databases": "Infrastructure",
    "performance": "Infrastructure",
    "jvm": "Infrastructure",
    "inventory": "Infrastructure",
    "ticket_management": "Operations",
    "interprocess_messaging": "Infrastructure",
    "event_signatures": "Operations",
    "splunk_audit": "Operations",
    "data_access": "Security",
}


def _strip_scheme(name):
    """Normalize input name  -  always return the short name without scheme prefix."""
    if "://" in str(name):
        return str(name).split("://", 1)[1]
    return str(name)


class StatusHandler(PersistentServerConnectionApplication):
    """Handle status requests  -  report and toggle active generators."""

    def __init__(self, command_line, command_arg):
        PersistentServerConnectionApplication.__init__(self)

    def handle(self, in_string):
        try:
            args = json.loads(in_string)
            method = args.get("method", "GET")

            if method == "GET":
                return self._handle_get(args)
            elif method == "POST":
                return self._handle_post(args)
            else:
                return {
                    "status": 405,
                    "payload": json.dumps({"error": "Method not allowed"}),
                }
        except Exception as e:
            return {
                "status": 500,
                "payload": json.dumps({"error": str(e)}),
            }

    def _handle_post(self, args):
        """Enable/disable a modular input, or update its parameters."""
        payload = args.get("payload", "{}")
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)

        action = data.get("action")
        input_name = data.get("input_name")

        if not input_name:
            return {
                "status": 400,
                "payload": json.dumps({"error": "input_name is required"}),
            }

        if action == "update":
            return self._handle_update(args, data)

        if action not in ("enable", "disable"):
            return {
                "status": 400,
                "payload": json.dumps({
                    "error": "action must be 'enable', 'disable', or 'update'",
                }),
            }

        return self._handle_toggle(args, data)

    def _handle_toggle(self, args, data):
        """Enable or disable a modular input via /enable or /disable sub-endpoint."""
        action = data["action"]
        input_name = data["input_name"]
        session_key = args["session"]["authtoken"]
        short_name = _strip_scheme(input_name)

        import urllib.parse
        encoded_name = urllib.parse.quote(short_name, safe="")
        endpoint = "/services/data/inputs/%s/%s/%s" % (SCHEME, encoded_name, action)

        try:
            response, content = rest.simpleRequest(
                endpoint,
                sessionKey=session_key,
                method="POST",
            )

            if isinstance(content, bytes):
                content = content.decode("utf-8")

            status_code = response.get("status", "500") if hasattr(response, "get") else getattr(response, "status", "500")

            if str(status_code) not in ("200", "201"):
                return {
                    "status": int(status_code),
                    "payload": json.dumps({
                        "error": "Splunk returned HTTP %s for %s" % (status_code, endpoint),
                        "detail": content[:500],
                        "endpoint": endpoint,
                    }),
                }

            return {
                "status": 200,
                "payload": json.dumps({
                    "success": True,
                    "message": "Input '%s' %sd. It will take effect within 60 seconds."
                               % (short_name, action),
                }),
            }
        except Exception as e:
            return {
                "status": 500,
                "payload": json.dumps({
                    "error": "Failed to %s input '%s': %s" % (action, short_name, str(e)),
                    "endpoint": endpoint,
                }),
            }

    def _handle_update(self, args, data):
        """Update modular input parameters (interval, events_per_interval)."""
        input_name = data["input_name"]
        session_key = args["session"]["authtoken"]
        short_name = _strip_scheme(input_name)

        import urllib.parse
        encoded_name = urllib.parse.quote(short_name, safe="")
        endpoint = "/servicesNS/nobody/cimdg/data/inputs/%s/%s" % (SCHEME, encoded_name)

        # Build update args from allowed parameters
        update_args = {}
        if "interval" in data:
            update_args["interval"] = str(data["interval"])
        if "events_per_interval" in data:
            update_args["events_per_interval"] = str(data["events_per_interval"])
        if "index" in data:
            update_args["index"] = str(data["index"])

        if not update_args:
            return {
                "status": 400,
                "payload": json.dumps({
                    "error": "No parameters to update.",
                }),
            }

        try:
            response, content = rest.simpleRequest(
                endpoint,
                sessionKey=session_key,
                postargs=update_args,
                method="POST",
            )

            if isinstance(content, bytes):
                content = content.decode("utf-8")

            status_code = response.get("status", "500") if hasattr(response, "get") else getattr(response, "status", "500")

            if str(status_code) not in ("200", "201"):
                return {
                    "status": int(status_code),
                    "payload": json.dumps({
                        "error": "Splunk returned HTTP %s for %s" % (status_code, endpoint),
                        "detail": content[:500],
                        "endpoint": endpoint,
                    }),
                }

            return {
                "status": 200,
                "payload": json.dumps({
                    "success": True,
                    "message": "Input '%s' updated: %s" % (
                        short_name,
                        ", ".join("%s=%s" % (k, v) for k, v in update_args.items())
                    ),
                }),
            }
        except Exception as e:
            return {
                "status": 500,
                "payload": json.dumps({
                    "error": "Failed to update input '%s': %s" % (short_name, str(e)),
                    "endpoint": endpoint,
                }),
            }

    def _handle_get(self, args):
        """Get status of active modular inputs."""
        session_key = args["session"]["authtoken"]

        try:
            response, content = rest.simpleRequest(
                "/services/data/inputs/%s" % SCHEME,
                sessionKey=session_key,
                getargs={"output_mode": "json", "count": 0},
                method="GET",
            )

            if isinstance(content, bytes):
                content = content.decode("utf-8")
            input_data = json.loads(content)

            inputs = []
            for entry in input_data.get("entry", []):
                # Normalize name  -  always return short name without scheme prefix
                raw_name = entry.get("name", "")
                short_name = _strip_scheme(raw_name)

                model = entry.get("content", {}).get("model", "")
                inputs.append({
                    "name": short_name,
                    "model": model,
                    "category": MODEL_CATEGORIES.get(model, "Other"),
                    "disabled": entry.get("content", {}).get("disabled", "1"),
                    "index": entry.get("content", {}).get("index", "synthetic_cim"),
                    "events_per_interval": entry.get("content", {}).get(
                        "events_per_interval", "10"
                    ),
                    "interval": entry.get("content", {}).get("interval", "60"),
                })

            active = [i for i in inputs if str(i["disabled"]) in ("0", "false", "False")]

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
