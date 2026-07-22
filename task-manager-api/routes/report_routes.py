from flask import Blueprint, g, jsonify

from middlewares.authentication import require_auth
from routes.common import load_json, load_query
from schemas.category_schemas import CategoryCreateSchema, CategoryUpdateSchema
from schemas.common import PaginationSchema


def create_report_blueprint(
    report_controller, category_controller, auth_service
):
    blueprint = Blueprint("reports", __name__)

    @blueprint.get("/reports/summary")
    @require_auth(auth_service, roles=("admin", "manager"))
    def summary_report():
        return jsonify(report_controller.summary()), 200

    @blueprint.get("/reports/user/<int:user_id>")
    @require_auth(auth_service)
    def user_report(user_id):
        return jsonify(report_controller.user(g.current_user, user_id)), 200

    @blueprint.get("/categories")
    @require_auth(auth_service)
    def get_categories():
        query = load_query(PaginationSchema())
        payload = category_controller.list(query["page"], query["per_page"])
        return jsonify(payload), 200

    @blueprint.post("/categories")
    @require_auth(auth_service, roles=("admin", "manager"))
    def create_category():
        payload = category_controller.create(load_json(CategoryCreateSchema()))
        return jsonify(payload), 201

    @blueprint.put("/categories/<int:category_id>")
    @require_auth(auth_service, roles=("admin", "manager"))
    def update_category(category_id):
        payload = category_controller.update(
            category_id, load_json(CategoryUpdateSchema())
        )
        return jsonify(payload), 200

    @blueprint.delete("/categories/<int:category_id>")
    @require_auth(auth_service, roles=("admin", "manager"))
    def delete_category(category_id):
        return jsonify(category_controller.delete(category_id)), 200

    return blueprint
