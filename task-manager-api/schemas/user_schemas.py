from marshmallow import fields, validate

from models.constants import MIN_PASSWORD_LENGTH, VALID_ROLES
from schemas.common import BaseSchema


EMAIL_PATTERN = r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"


class UserCreateSchema(BaseSchema):
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error="Nome inválido"),
    )
    email = fields.String(
        required=True,
        validate=validate.Regexp(EMAIL_PATTERN, error="Email inválido"),
    )
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(
            min=MIN_PASSWORD_LENGTH,
            max=256,
            error=f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres",
        ),
    )
    role = fields.String(
        load_default="user",
        validate=validate.OneOf(VALID_ROLES, error="Role inválido"),
    )


class UserUpdateSchema(BaseSchema):
    name = fields.String(validate=validate.Length(min=1, max=100, error="Nome inválido"))
    email = fields.String(validate=validate.Regexp(EMAIL_PATTERN, error="Email inválido"))
    password = fields.String(
        load_only=True,
        validate=validate.Length(
            min=MIN_PASSWORD_LENGTH,
            max=256,
            error=f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres",
        ),
    )
    role = fields.String(validate=validate.OneOf(VALID_ROLES, error="Role inválido"))
    active = fields.Boolean()


class LoginSchema(BaseSchema):
    email = fields.String(required=True, validate=validate.Regexp(EMAIL_PATTERN))
    password = fields.String(required=True, load_only=True)
