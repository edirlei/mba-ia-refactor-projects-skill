from datetime import UTC, datetime, time

from marshmallow import ValidationError, fields, post_load, validate, validates

from models.constants import (
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_STATUSES,
)
from schemas.common import BaseSchema, PaginationSchema


class TaskFieldsMixin:
    title = fields.String(
        validate=validate.Length(
            min=MIN_TITLE_LENGTH,
            max=MAX_TITLE_LENGTH,
            error="Título deve ter entre 3 e 200 caracteres",
        )
    )
    description = fields.String(allow_none=True)
    status = fields.String(validate=validate.OneOf(VALID_STATUSES, error="Status inválido"))
    priority = fields.Integer(
        validate=validate.Range(
            min=MIN_PRIORITY,
            max=MAX_PRIORITY,
            error="Prioridade deve ser entre 1 e 5",
        )
    )
    user_id = fields.Integer(allow_none=True)
    category_id = fields.Integer(allow_none=True)
    due_date = fields.Date(format="%Y-%m-%d", allow_none=True)
    tags = fields.Raw(allow_none=True)

    @validates("tags")
    def validate_tags(self, value):
        if value is not None and not isinstance(value, (str, list)):
            raise ValidationError("Tags devem ser texto ou lista")
        if isinstance(value, list) and not all(isinstance(tag, str) for tag in value):
            raise ValidationError("Todas as tags devem ser textos")

    @post_load
    def normalize(self, data, **kwargs):
        if data.get("due_date") is not None:
            data["due_date"] = datetime.combine(data["due_date"], time.min, tzinfo=UTC)
        if isinstance(data.get("tags"), list):
            data["tags"] = ",".join(data["tags"])
        return data


class TaskCreateSchema(TaskFieldsMixin, BaseSchema):
    title = fields.String(
        required=True,
        validate=validate.Length(
            min=MIN_TITLE_LENGTH,
            max=MAX_TITLE_LENGTH,
            error="Título deve ter entre 3 e 200 caracteres",
        ),
    )
    status = fields.String(
        load_default="pending",
        validate=validate.OneOf(VALID_STATUSES, error="Status inválido"),
    )
    priority = fields.Integer(
        load_default=DEFAULT_PRIORITY,
        validate=validate.Range(
            min=MIN_PRIORITY,
            max=MAX_PRIORITY,
            error="Prioridade deve ser entre 1 e 5",
        ),
    )
    description = fields.String(load_default="", allow_none=True)


class TaskUpdateSchema(TaskFieldsMixin, BaseSchema):
    pass


class TaskSearchSchema(PaginationSchema):
    q = fields.String(load_default="")
    status = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(VALID_STATUSES, error="Status inválido"),
    )
    priority = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(
            min=MIN_PRIORITY,
            max=MAX_PRIORITY,
            error="Prioridade deve ser entre 1 e 5",
        ),
    )
    user_id = fields.Integer(load_default=None, allow_none=True)
