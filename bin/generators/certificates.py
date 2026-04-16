"""Certificates CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("certificates")
class CertificatesGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("certificates")
