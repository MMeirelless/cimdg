"""Interprocess Messaging CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("interprocess_messaging")
class InterprocessMessagingGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("interprocess_messaging")
