"""Alerts CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("alerts")
class AlertsGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("alerts")
