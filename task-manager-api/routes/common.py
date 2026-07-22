from flask import current_app, request
from marshmallow import ValidationError


def load_json(schema):
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        raise ValidationError({"json": ["Dados inválidos"]})
    return schema.load(payload)


def load_query(schema):
    data = schema.load(request.args.to_dict())
    per_page = data.get("per_page") or current_app.config["DEFAULT_PAGE_SIZE"]
    data["per_page"] = min(per_page, current_app.config["MAX_PAGE_SIZE"])
    return data
