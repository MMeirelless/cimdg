"""
CIM Data Generator  -  REST handler for batch generation.

Endpoints:
    GET  /services/cimdg/generate   -  List available models
    POST /services/cimdg/generate   -  Trigger batch generation
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from splunk.persistconn.application import PersistentServerConnectionApplication
import splunk.rest as rest

import generators  # noqa: F401  -  auto-discovers and registers all generators
from generators.base import GeneratorFactory


class GenerateHandler(PersistentServerConnectionApplication):
    """Handle generation requests  -  list models and trigger batch generation."""

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
        """Trigger batch generation or run a playbook."""
        payload = args.get("payload", "{}")
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)

        playbook_name = data.get("playbook")
        if playbook_name:
            return self._handle_playbook(args, data)

        return self._handle_model_generate(args, data)

    def _handle_model_generate(self, args, data):
        """Generate events for a single CIM model via search job."""
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
            '| collect index=%s sourcetype=cimdg:synthetic:%s'
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

    def _handle_playbook(self, args, data):
        """Run an attack playbook, writing events directly with correct sourcetypes."""
        from playbooks.base import PlaybookFactory
        from playbooks import brute_force, lateral_movement, data_exfiltration  # noqa

        playbook_name = data.get("playbook")
        index = data.get("index", "synthetic_cim")
        session_key = args["session"]["authtoken"]

        try:
            pb = PlaybookFactory.create(playbook_name)
        except ValueError as e:
            return {
                "status": 400,
                "payload": json.dumps({
                    "error": str(e),
                    "available": PlaybookFactory.list_playbooks(),
                }),
            }

        try:
            results = pb.execute(base_time=time.time())

            # Write each event via /services/receivers/simple with correct sourcetype
            events_written = 0
            sourcetypes_used = set()
            for item in results:
                sourcetype = item["sourcetype"]
                event_json = json.dumps(item["event"], separators=(",", ":"))
                sourcetypes_used.add(sourcetype)

                import urllib.parse
                qs = urllib.parse.urlencode({
                    "index": index,
                    "sourcetype": sourcetype,
                    "source": "cimdg:playbook:%s" % playbook_name,
                    "host": "cimdg",
                })
                rest.simpleRequest(
                    "/services/receivers/simple?%s" % qs,
                    sessionKey=session_key,
                    postargs={"_raw": event_json},
                    method="POST",
                )
                events_written += 1

            return {
                "status": 200,
                "payload": json.dumps({
                    "success": True,
                    "message": (
                        "Playbook '%s' completed: %d events across %d sourcetypes "
                        "indexed into %s."
                        % (playbook_name, events_written,
                           len(sourcetypes_used), index)
                    ),
                    "events": events_written,
                    "sourcetypes": sorted(sourcetypes_used),
                }),
            }
        except Exception as e:
            return {
                "status": 500,
                "payload": json.dumps({
                    "error": "Playbook failed: %s" % str(e),
                }),
            }
