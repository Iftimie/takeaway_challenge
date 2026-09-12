from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, SecretBytes, SecretStr

REDACTED = "[REDACTED]"


def to_log_dict(model: BaseModel) -> dict[str, object]:
    """Build a separate logging representation using declared schema fields only."""
    if not isinstance(model, BaseModel):
        raise TypeError("to_log_dict requires a Pydantic model")
    result = {}
    for name, field in type(model).model_fields.items():
        metadata = field.json_schema_extra
        if isinstance(metadata, dict) and metadata.get("sensitive") is True:
            result[name] = REDACTED
        else:
            result[name] = _log_value(getattr(model, name))
    return result


def _log_value(value: object) -> object:
    if isinstance(value, (SecretStr, SecretBytes)):
        return REDACTED
    if isinstance(value, BaseModel):
        return to_log_dict(value)
    if isinstance(value, (list, tuple)):
        return [_log_value(item) for item in value]
    if isinstance(value, Enum):
        return _log_value(value.value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    # Untyped dictionaries and arbitrary objects have no field-redaction contract.
    return "[OMITTED]"
