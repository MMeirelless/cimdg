"""Change CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("change")
class ChangeGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("change")
