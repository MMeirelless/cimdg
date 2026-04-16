"""DLP (Data Loss Prevention) CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("dlp")
class DLPGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("dlp")
