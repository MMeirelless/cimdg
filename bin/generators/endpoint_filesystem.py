"""Endpoint Filesystem CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("endpoint_filesystem")
class EndpointFilesystemGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("endpoint_filesystem")
