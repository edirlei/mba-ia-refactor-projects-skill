"""Executa os 22 endpoints originais por HTTP real em banco temporário."""
import tempfile
import threading
from pathlib import Path

import requests
from werkzeug.serving import make_server

from app import create_app
from database import db
from models.category import Category
from models.task import Task
from models.user import User


def seed_fixture(app):
    with app.app_context():
        db.create_all()
        admin = User(
            name="Smoke Admin",
            email="smoke-admin@example.com",
            role="admin",
        )
        admin.set_password("admin123")
        user = User(
            name="Smoke User",
            email="smoke-user@example.com",
            role="user",
        )
        user.set_password("user123")
        category = Category(name="Smoke Category", color="#123456")
        db.session.add_all([admin, user, category])
        db.session.flush()
        task = Task(
            title="Smoke task",
            user_id=user.id,
            category_id=category.id,
        )
        db.session.add(task)
        db.session.commit()
        return user.id, category.id, task.id


def run_smoke():
    with tempfile.TemporaryDirectory(prefix="task-manager-smoke-") as directory:
        database_path = (Path(directory) / "smoke.db").as_posix()
        app = create_app(
            {
                "TESTING": False,
                "SECRET_KEY": "smoke-only-secret-key-with-32-bytes",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
                "TOKEN_MAX_AGE_SECONDS": 3600,
                "CORS_ORIGINS": [],
            }
        )
        user_id, category_id, task_id = seed_fixture(app)
        server = make_server("127.0.0.1", 0, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        session = requests.Session()
        results = []

        def call(label, method, path, expected, **kwargs):
            response = session.request(
                method, f"{base_url}{path}", timeout=5, **kwargs
            )
            results.append((label, method, path, response.status_code, expected))
            if response.status_code != expected:
                raise AssertionError(
                    f"{label}: esperado {expected}, recebido "
                    f"{response.status_code}: {response.text}"
                )
            return response

        try:
            call("root", "GET", "/", 200)
            call("health", "GET", "/health", 200)
            login = call(
                "login",
                "POST",
                "/login",
                200,
                json={
                    "email": "smoke-admin@example.com",
                    "password": "admin123",
                },
            ).json()
            headers = {"Authorization": f"Bearer {login['token']}"}

            call("users-list", "GET", "/users", 200, headers=headers)
            call("users-get", "GET", f"/users/{user_id}", 200, headers=headers)
            created_user = call(
                "users-create",
                "POST",
                "/users",
                201,
                json={
                    "name": "Created User",
                    "email": "created-smoke@example.com",
                    "password": "CreatedPass!2026",
                },
            ).json()
            call(
                "users-update",
                "PUT",
                f"/users/{created_user['id']}",
                200,
                headers=headers,
                json={"name": "Updated User"},
            )
            call(
                "users-tasks",
                "GET",
                f"/users/{user_id}/tasks",
                200,
                headers=headers,
            )

            call("tasks-list", "GET", "/tasks", 200, headers=headers)
            call("tasks-get", "GET", f"/tasks/{task_id}", 200, headers=headers)
            created_task = call(
                "tasks-create",
                "POST",
                "/tasks",
                201,
                headers=headers,
                json={
                    "title": "Created smoke task",
                    "user_id": user_id,
                    "category_id": category_id,
                },
            ).json()
            call(
                "tasks-update",
                "PUT",
                f"/tasks/{created_task['id']}",
                200,
                headers=headers,
                json={"status": "in_progress"},
            )
            call(
                "tasks-search",
                "GET",
                "/tasks/search?q=smoke&priority=3",
                200,
                headers=headers,
            )
            call("tasks-stats", "GET", "/tasks/stats", 200, headers=headers)
            call(
                "reports-summary",
                "GET",
                "/reports/summary",
                200,
                headers=headers,
            )
            call(
                "reports-user",
                "GET",
                f"/reports/user/{user_id}",
                200,
                headers=headers,
            )

            call("categories-list", "GET", "/categories", 200, headers=headers)
            created_category = call(
                "categories-create",
                "POST",
                "/categories",
                201,
                headers=headers,
                json={"name": "Created Category", "color": "#abcdef"},
            ).json()
            call(
                "categories-update",
                "PUT",
                f"/categories/{created_category['id']}",
                200,
                headers=headers,
                json={"description": "updated"},
            )
            call(
                "tasks-delete",
                "DELETE",
                f"/tasks/{created_task['id']}",
                200,
                headers=headers,
            )
            call(
                "categories-delete",
                "DELETE",
                f"/categories/{created_category['id']}",
                200,
                headers=headers,
            )
            call(
                "users-delete",
                "DELETE",
                f"/users/{created_user['id']}",
                200,
                headers=headers,
            )
        finally:
            session.close()
            server.shutdown()
            thread.join(timeout=5)
            with app.app_context():
                db.session.remove()
                db.engine.dispose()

        for label, method, path, status, expected in results:
            print(f"{status:3} {method:6} {path:42} {label}")
        print(f"HTTP_ENDPOINTS={len(results)}/22")
        if len(results) != 22:
            raise AssertionError(f"Esperados 22 endpoints, executados {len(results)}")


if __name__ == "__main__":
    run_smoke()
