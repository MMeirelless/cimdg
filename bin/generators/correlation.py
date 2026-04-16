"""
Cross-model session correlation engine.

Maintains a pool of active sessions that span Authentication -> Network Traffic
-> Web -> Endpoint events with shared session_id, user, and src values.

Only effective when multiple generators run simultaneously via modular inputs.
The batch command (| cimgenerate) is single-model and does not produce
correlated data  -  this is a documented limitation.
"""

import random
import time
import uuid


class SessionManager:
    """Singleton that manages active cross-model sessions."""

    _instance = None
    MAX_SESSIONS = 1000
    MAX_AGE_SECONDS = 3600

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sessions = {}

    def create_session(self, user, src):
        """Create a new session and return its ID."""
        self._expire_sessions()

        if len(self._sessions) >= self.MAX_SESSIONS:
            oldest_key = min(self._sessions, key=lambda k: self._sessions[k]["start_time"])
            del self._sessions[oldest_key]

        session_id = uuid.uuid4().hex
        self._sessions[session_id] = {
            "user": user,
            "src": src,
            "start_time": time.time(),
            "models_seen": set(),
        }
        return session_id

    def get_session(self):
        """Get a random active session, or None if none exist."""
        self._expire_sessions()
        if not self._sessions:
            return None
        session_id = random.choice(list(self._sessions.keys()))
        session = self._sessions[session_id]
        return {
            "session_id": session_id,
            "user": session["user"],
            "src": session["src"],
        }

    def mark_model(self, session_id, model_name):
        """Record that a model has used this session."""
        if session_id in self._sessions:
            self._sessions[session_id]["models_seen"].add(model_name)

    def _expire_sessions(self):
        """Remove sessions older than MAX_AGE_SECONDS."""
        cutoff = time.time() - self.MAX_AGE_SECONDS
        expired = [sid for sid, s in self._sessions.items() if s["start_time"] < cutoff]
        for sid in expired:
            del self._sessions[sid]

    @property
    def active_count(self):
        self._expire_sessions()
        return len(self._sessions)
