"""Authentication CIM data model generator."""

import random
import time

from generators.base import BaseGenerator, register_generator, generate_timestamp


@register_generator("authentication")
class AuthenticationGenerator(BaseGenerator):
    """
    Generates CIM-compliant Authentication events.

    Special behaviors:
    - Brute-force burst patterns (20 failures from single src in 60s)
    - Service account patterns (near-100% success)
    - Correlated src_user/user fields
    """

    def __init__(self):
        super().__init__("authentication")
        self._burst_state = {"active": False, "src": None, "target": None, "remaining": 0}

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)

        # Service account pattern: near-100% success
        if event.get("user_type") == "service":
            svc = self.pool.random_service_account()
            event["user"] = svc
            event["src_user"] = svc
            event["action"] = "success"
            event["authentication_method"] = "kerberos"
            event["signature"] = "An account was successfully logged on"
            event["signature_id"] = "4624"
            event.pop("reason", None)

        # Brute-force burst: 2% chance to start a burst
        if not self._burst_state["active"] and random.random() < 0.02:
            self._burst_state = {
                "active": True,
                "src": self.pool.random_external_ip(),
                "target": self.pool.random_username(),
                "remaining": random.randint(10, 25),
            }

        if self._burst_state["active"]:
            event["action"] = "failure"
            event["src"] = self._burst_state["src"]
            event["user"] = self._burst_state["target"]
            event["reason"] = "invalid_password"
            event["signature"] = "An account failed to log on"
            event["signature_id"] = "4625"
            self._burst_state["remaining"] -= 1
            if self._burst_state["remaining"] <= 0:
                self._burst_state["active"] = False

        # Ensure signature/signature_id consistency with action
        action = event.get("action")
        if action == "success":
            event["signature"] = "An account was successfully logged on"
            event["signature_id"] = "4624"
            event.pop("reason", None)

            # Cross-model correlation: 30% of successful auths create a session
            if random.random() < 0.30:
                try:
                    from generators.correlation import SessionManager
                    sm = SessionManager()
                    sid = sm.create_session(event["user"], event["src"])
                    event["session_id"] = sid
                    sm.mark_model(sid, "authentication")
                except Exception:
                    pass

        # Keep src_user consistent with user
        if "src_user" not in event or event.get("user_type") != "service":
            event["src_user"] = event["user"]

        return event
