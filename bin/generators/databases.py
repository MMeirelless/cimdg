"""Databases CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("databases")
class DatabasesGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("databases")
