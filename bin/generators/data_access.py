"""Data Access CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("data_access")
class DataAccessGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("data_access")
