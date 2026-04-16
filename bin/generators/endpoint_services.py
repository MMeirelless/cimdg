"""Endpoint Services CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("endpoint_services")
class EndpointServicesGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("endpoint_services")
