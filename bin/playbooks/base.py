"""
Base playbook for multi-model correlated attack scenarios.

A playbook defines a timeline of events across multiple CIM models
that together represent a realistic attack or security scenario.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import generators  # noqa: F401
from generators.base import GeneratorFactory


class BasePlaybook:
    """Orchestrates multi-model event generation in a timed sequence."""

    name = "base"
    description = "Base playbook"

    def __init__(self):
        self.timeline = []  # [(offset_seconds, model_name, event_overrides)]

    def build_timeline(self):
        """Override in subclasses to define the attack timeline."""
        raise NotImplementedError

    def execute(self, base_time=None):
        """Generate all events in the timeline."""
        if base_time is None:
            base_time = time.time()

        self.build_timeline()

        results = []
        for offset, model_name, overrides in self.timeline:
            generator = GeneratorFactory.create(model_name)
            event = generator.generate_event(timestamp=base_time + offset)
            event.update(overrides)
            sourcetype = generator.get_sourcetype()
            results.append({
                "sourcetype": sourcetype,
                "event": event,
            })

        return results


_PLAYBOOK_REGISTRY = {}


def register_playbook(name):
    """Decorator to register a playbook class."""
    def decorator(cls):
        _PLAYBOOK_REGISTRY[name] = cls
        return cls
    return decorator


class PlaybookFactory:
    """Factory for creating playbooks by name."""

    @classmethod
    def create(cls, name):
        name = name.lower().strip()
        playbook_cls = _PLAYBOOK_REGISTRY.get(name)
        if playbook_cls is None:
            raise ValueError(
                f"Unknown playbook: {name}. "
                f"Available: {', '.join(cls.list_playbooks())}"
            )
        return playbook_cls()

    @classmethod
    def list_playbooks(cls):
        return sorted(_PLAYBOOK_REGISTRY.keys())
