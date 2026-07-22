from flask import jsonify
from marshmallow import ValidationError

from database import db
from errors import ApplicationError


def _first_validation_message(messages):
    if isinstance(messages, dict):
        for value in messages.values():
            return _first_validation_message(value)
    if isinstance(messages, list) and messages:
        return _first_validation_message(messages[0])
    return str(messages)


def register_error_handlers(app):
    @app.errorhandler(ApplicationError)
    def handle_application_error(error):
        db.session.rollback()
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        db.session.rollback()
        return jsonify({"error": _first_validation_message(error.messages)}), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        app.logger.exception("request_failed", exc_info=error)
        return jsonify({"error": "Erro interno"}), 500
