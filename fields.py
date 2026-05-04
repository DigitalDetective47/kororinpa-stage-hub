from django.db.models import BinaryField
from koro import BinSlot, Stage, XmlSlot


class StageField(BinaryField):
    description = "An in-game stage"

    def from_db_value(self, value, expression, connection):
        if not value:
            return None
        return BinSlot.deserialize(value)

    def get_prep_value(self, value):
        if not value:
            return None
        return BinSlot.serialize(value)

    def to_python(self, value):
        if not value or isinstance(value, Stage):
            return None
        return XmlSlot.deserialize(value)
