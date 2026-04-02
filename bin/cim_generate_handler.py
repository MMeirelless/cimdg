"""
CIM Data Generator — REST handler for batch generation.

Endpoints:
    GET  /services/cimdg/generate  — List available models
    POST /services/cimdg/generate  — Trigger batch generation
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


class GenerateHandler(PersistentServerConnectionApplication):
    """Handle generation requests — list models and trigger batch generation."""

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

    def _handle_get(self, args):
        """List available CIM data models."""
        models = GeneratorFactory.list_models()
        return {
            "status": 200,
            "payload": json.dumps({
                "models": models,
                "count": len(models),
            }),
        }

    def _handle_post(self, args):
        """Trigger batch generation via search command."""
        payload = args.get("payload", "{}")
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)

        model = data.get("model")
        count = int(data.get("count", 100))
        index = data.get("index", "synthetic_cim")
        timerange = data.get("timerange", "-1h")

        if not model:
            return {
                "status": 400,
                "payload": json.dumps({"error": "model parameter is required"}),
            }

        if model.lower() not in [m.lower() for m in GeneratorFactory.list_models()]:
            return {
                "status": 400,
                "payload": json.dumps({
                    "error": "Unknown model: %s" % model,
                    "supported": GeneratorFactory.list_models(),
                }),
            }

        count = min(count, 100000)

        session_key = args["session"]["authtoken"]
        search_query = (
            '| cimgenerate model="%s" count=%d timerange="%s" '
            '| collect index=%s sourcetype=synthetic:%s'
            % (model, count, timerange, index, model)
        )

        try:
            response, content = rest.simpleRequest(
                "/services/search/jobs",
                sessionKey=session_key,
                postargs={
                    "search": search_query,
                    "exec_mode": "normal",
                    "output_mode": "json",
                },
                method="POST",
            )

            if isinstance(content, bytes):
                content = content.decode("utf-8")

            job_info = json.loads(content)
            sid = job_info.get("sid", "")

            return {
                "status": 200,
                "payload": json.dumps({
                    "success": True,
                    "message": (
                        "Dispatched generation of %d %s events into index=%s "
                        "(job: %s)" % (count, model, index, sid)
                    ),
                    "sid": sid,
                    "search": search_query,
                }),
            }
        except Exception as e:
            return {
                "status": 500,
                "payload": json.dumps({
                    "error": "Failed to dispatch search: %s" % str(e),
                }),
            }
