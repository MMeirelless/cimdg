"""Endpoint Registry CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("endpoint_registry")
class EndpointRegistryGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("endpoint_registry")
