"""Endpoint Ports CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("endpoint_ports")
class EndpointPortsGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("endpoint_ports")
