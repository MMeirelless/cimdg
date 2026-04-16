"""Event Signatures CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("event_signatures")
class EventSignaturesGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("event_signatures")
