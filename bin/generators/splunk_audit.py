"""Splunk Audit CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("splunk_audit")
class SplunkAuditGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("splunk_audit")
