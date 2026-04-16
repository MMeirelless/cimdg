"""Updates CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("updates")
class UpdatesGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("updates")
