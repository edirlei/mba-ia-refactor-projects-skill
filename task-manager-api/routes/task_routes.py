from flask import Blueprint, g, jsonify

from middlewares.authentication import require_auth
from routes.common import load_json, load_query
from schemas.common import PaginationSchema
from schemas.task_schemas import TaskCreateSchema, TaskSearchSchema, TaskUpdateSchema


def create_task_blueprint(task_controller, auth_service):
    blueprint = Blueprint("tasks", __name__)

    @blueprint.get("/tasks")
    @require_auth(auth_service)
    def get_tasks():
        query = load_query(PaginationSchema())
        payload = task_controller.list(
            g.current_user, query["page"], query["per_page"]
        )
        return jsonify(payload), 200

    @blueprint.get("/tasks/<int:task_id>")
    @require_auth(auth_service)
    def get_task(task_id):
        return jsonify(task_controller.get(g.current_user, task_id)), 200

    @blueprint.post("/tasks")
    @require_auth(auth_service)
    def create_task():
        payload = task_controller.create(
            g.current_user, load_json(TaskCreateSchema())
        )
        return jsonify(payload), 201

    @blueprint.put("/tasks/<int:task_id>")
    @require_auth(auth_service)
    def update_task(task_id):
        payload = task_controller.update(
            g.current_user, task_id, load_json(TaskUpdateSchema())
        )
        return jsonify(payload), 200

    @blueprint.delete("/tasks/<int:task_id>")
    @require_auth(auth_service)
    def delete_task(task_id):
        return jsonify(task_controller.delete(g.current_user, task_id)), 200

    @blueprint.get("/tasks/search")
    @require_auth(auth_service)
    def search_tasks():
        filters = load_query(TaskSearchSchema())
        payload = task_controller.search(
            g.current_user, filters, filters["page"], filters["per_page"]
        )
        return jsonify(payload), 200

    @blueprint.get("/tasks/stats")
    @require_auth(auth_service)
    def task_stats():
        return jsonify(task_controller.stats(g.current_user)), 200

    return blueprint
