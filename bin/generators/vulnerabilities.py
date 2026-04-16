"""Vulnerabilities CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("vulnerabilities")
class VulnerabilitiesGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("vulnerabilities")
