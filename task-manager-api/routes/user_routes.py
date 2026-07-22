from flask import Blueprint, g, jsonify

from middlewares.authentication import require_auth
from routes.common import load_json, load_query
from schemas.common import PaginationSchema
from schemas.user_schemas import LoginSchema, UserCreateSchema, UserUpdateSchema


def create_user_blueprint(user_controller, auth_controller, auth_service):
    blueprint = Blueprint("users", __name__)

    @blueprint.get("/users")
    @require_auth(auth_service, roles=("admin", "manager"))
    def get_users():
        query = load_query(PaginationSchema())
        return jsonify(user_controller.list(query["page"], query["per_page"])), 200

    @blueprint.get("/users/<int:user_id>")
    @require_auth(auth_service)
    def get_user(user_id):
        query = load_query(PaginationSchema())
        payload = user_controller.get(
            g.current_user, user_id, query["page"], query["per_page"]
        )
        return jsonify(payload), 200

    @blueprint.post("/users")
    def create_user():
        payload = user_controller.create(load_json(UserCreateSchema()))
        return jsonify(payload), 201

    @blueprint.put("/users/<int:user_id>")
    @require_auth(auth_service)
    def update_user(user_id):
        payload = user_controller.update(
            g.current_user, user_id, load_json(UserUpdateSchema())
        )
        return jsonify(payload), 200

    @blueprint.delete("/users/<int:user_id>")
    @require_auth(auth_service, roles=("admin",))
    def delete_user(user_id):
        return jsonify(user_controller.delete(user_id)), 200

    @blueprint.get("/users/<int:user_id>/tasks")
    @require_auth(auth_service)
    def get_user_tasks(user_id):
        query = load_query(PaginationSchema())
        payload = user_controller.tasks(
            g.current_user, user_id, query["page"], query["per_page"]
        )
        return jsonify(payload), 200

    @blueprint.post("/login")
    def login():
        return jsonify(auth_controller.login(load_json(LoginSchema()))), 200

    return blueprint
