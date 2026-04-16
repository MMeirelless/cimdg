"""Ticket Management CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("ticket_management")
class TicketManagementGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("ticket_management")
