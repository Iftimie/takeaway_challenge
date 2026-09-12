import json
from typing import get_args, get_origin

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, TypeAdapter
from starlette.exceptions import HTTPException

from app.log_redaction import to_log_dict

MAX_LOG_BYTES = 4096
MAX_INSPECT_BYTES = 65536


def bounded(value: object) -> object:
    if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > MAX_LOG_BYTES:
        return {"omitted": "size_limit"}
    return value


def model_type(schema):
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return schema
    if get_origin(schema) is list:
        return model_type(get_args(schema)[0])
    return None


def payload_for_log(raw: bytes, schema) -> object:
    if model_type(schema) is None:
        return {"omitted": "no_schema"}
    if len(raw) > MAX_INSPECT_BYTES:
        return {"omitted": "size_limit"}
    try:
        value = TypeAdapter(schema).validate_json(raw)
        redacted = [to_log_dict(item) for item in value] if isinstance(value, list) else to_log_dict(value)
        return bounded(redacted)
    except Exception:
        # Logging must neither expose invalid data nor change the endpoint outcome.
        return {"omitted": "invalid_payload"}


def schema_field_names(schema) -> set[str]:
    model = model_type(schema)
    if model is None:
        return set()
    names = set(model.model_fields)
    for field in model.model_fields.values():
        names.update(schema_field_names(field.annotation))
    return names


class PayloadLoggingRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        request_schema = self.body_field.field_info.annotation if self.body_field else None
        allowed_locations = {"body", "query", "path", "header"} | schema_field_names(request_schema)
        for params in (self.dependant.path_params, self.dependant.query_params, self.dependant.header_params):
            allowed_locations.update(param.alias for param in params)

        async def with_payload_logging(request: Request):
            payloads = {"request_body": {"omitted": "no_schema"}, "response_body": {"omitted": "no_schema"}}
            request.state.log_payloads = payloads
            try:
                response = await handler(request)
            except RequestValidationError as error:
                payloads["request_body"] = {"omitted": "validation_failed"}
                # Extra-field names are user input too. Keep only known schema names.
                payloads["validation_errors"] = bounded([
                    {"loc": [part if isinstance(part, int) or part in allowed_locations else "<unknown_field>"
                             for part in item["loc"]], "type": item["type"]}
                    for item in error.errors()[:20]
                ])
                raise
            except HTTPException:
                if request_schema is not None:
                    payloads["request_body"] = payload_for_log(await request.body(), request_schema)
                payloads["response_body"] = {"omitted": "error_response"}
                raise
            else:
                if request_schema is not None:
                    payloads["request_body"] = payload_for_log(await request.body(), request_schema)
                raw = getattr(response, "body", None)
                if response.status_code < 400 and isinstance(raw, bytes) and response.media_type == "application/json":
                    payloads["response_body"] = payload_for_log(raw, self.response_model)
                return response

        return with_payload_logging
