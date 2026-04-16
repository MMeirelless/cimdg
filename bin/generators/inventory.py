"""Inventory CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("inventory")
class InventoryGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("inventory")
