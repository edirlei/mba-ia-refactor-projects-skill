import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException


LOGGER = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400
    code = "application_error"

    def __init__(self, message, *, status_code=None, code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class ValidationError(AppError):
    status_code = 400
    code = "validation_error"


class AuthenticationError(AppError):
    status_code = 401
    code = "authentication_error"


class AuthorizationError(AppError):
    status_code = 403
    code = "authorization_error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify(
            {
                "erro": error.message,
                "sucesso": False,
            }
        ), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify(
            {
                "erro": error.description,
                "sucesso": False,
            }
        ), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        LOGGER.exception("request_failed", exc_info=error)
        return jsonify(
            {
                "erro": "Erro interno do servidor",
                "sucesso": False,
            }
        ), 500
