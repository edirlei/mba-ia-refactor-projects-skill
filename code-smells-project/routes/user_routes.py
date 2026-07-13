from flask import Blueprint, jsonify, request

from schemas import (
    parse_login_payload,
    parse_pagination,
    parse_user_payload,
    require_json_object,
)


def create_user_blueprint(controller):
    blueprint = Blueprint("users", __name__)

    @blueprint.get("/usuarios")
    def list_users():
        limit, offset = parse_pagination(request.args)
        users = controller.list_all(limit=limit, offset=offset)
        return jsonify({"dados": users, "sucesso": True}), 200

    @blueprint.get("/usuarios/<int:user_id>")
    def get_user(user_id):
        return jsonify({"dados": controller.get_by_id(user_id), "sucesso": True}), 200

    @blueprint.post("/usuarios")
    def create_user():
        user = parse_user_payload(require_json_object(request))
        user_id = controller.create(user)
        return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201

    @blueprint.post("/login")
    def login():
        credentials = parse_login_payload(require_json_object(request))
        user = controller.login(credentials)
        return jsonify(
            {"dados": user, "sucesso": True, "mensagem": "Login OK"}
        ), 200

    return blueprint
