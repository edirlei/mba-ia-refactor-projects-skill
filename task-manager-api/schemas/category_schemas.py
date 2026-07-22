from marshmallow import fields, validate

from models.constants import DEFAULT_COLOR
from schemas.common import BaseSchema


COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"


class CategoryCreateSchema(BaseSchema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error="Nome inválido"),
    )
    description = fields.String(load_default="", allow_none=True)
    color = fields.String(
        load_default=DEFAULT_COLOR,
        validate=validate.Regexp(COLOR_PATTERN, error="Cor inválida"),
    )


class CategoryUpdateSchema(BaseSchema):
    name = fields.String(validate=validate.Length(min=1, max=100, error="Nome inválido"))
    description = fields.String(allow_none=True)
    color = fields.String(validate=validate.Regexp(COLOR_PATTERN, error="Cor inválida"))
