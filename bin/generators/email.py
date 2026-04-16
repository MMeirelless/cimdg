"""Email CIM data model generator."""

from generators.base import BaseGenerator, register_generator


@register_generator("email")
class EmailGenerator(BaseGenerator):

    def __init__(self):
        super().__init__("email")

    def generate_event(self, timestamp=None, timerange_seconds=3600):
        event = super().generate_event(timestamp=timestamp, timerange_seconds=timerange_seconds)
        # Clear file_hash when no attachment
        if not event.get("file_name"):
            event.pop("file_hash", None)
        return event
