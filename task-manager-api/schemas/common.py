from marshmallow import EXCLUDE, Schema, fields, validate


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class PaginationSchema(BaseSchema):
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, error="Página deve ser maior que zero"),
    )
    per_page = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="Limite deve ser maior que zero"),
    )
