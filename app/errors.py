from uuid import uuid4

from flask import g, jsonify
from pydantic import ValidationError


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        field_errors: list[dict] | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.field_errors = field_errors


def request_id() -> str:
    current = getattr(g, "request_id", None)
    if current:
        return current
    generated = str(uuid4())
    g.request_id = generated
    return generated


def error_payload(
    code: str,
    message: str,
    field_errors: list[dict] | None = None,
) -> dict:
    payload = {
        "code": code,
        "message": message,
        "requestId": request_id(),
    }
    if field_errors is not None:
        payload["fieldErrors"] = field_errors
    return payload


def validation_error(error: ValidationError) -> tuple:
    field_errors = []
    for item in error.errors():
        location = ".".join(str(part) for part in item.get("loc", ()))
        field_errors.append(
            {"field": location or "body", "message": item.get("msg", "inválido")}
        )
    return (
        jsonify(
            error_payload(
                "VALIDATION_ERROR",
                "Regla de negocio o esquema inválido",
                field_errors,
            )
        ),
        422,
    )


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify(
            error_payload(error.code, error.message, error.field_errors)
        ), error.status
