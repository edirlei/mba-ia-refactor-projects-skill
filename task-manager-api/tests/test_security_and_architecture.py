import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import event

from app import create_app
from database import db
from models.category import Category
from models.task import Task
from models.user import User


class SecurityAndArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-only-secret-key-with-32-bytes",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "TOKEN_MAX_AGE_SECONDS": 1,
                "CORS_ORIGINS": ["http://localhost"],
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            admin = User(
                name="Administrator",
                email="admin@example.com",
                role="admin",
                active=True,
            )
            admin.set_password("admin123")
            user = User(
                name="Regular User",
                email="user@example.com",
                role="user",
                active=True,
            )
            user.set_password("user123")
            other = User(
                name="Other User",
                email="other@example.com",
                role="user",
                active=True,
            )
            other.set_password("other123")
            category = Category(name="Security", color="#123456")
            db.session.add_all([admin, user, other, category])
            db.session.flush()
            task = Task(
                title="Other user task",
                user_id=other.id,
                category_id=category.id,
            )
            db.session.add(task)
            db.session.commit()
            self.admin_id = admin.id
            self.user_id = user.id
            self.other_id = other.id
            self.task_id = task.id
            self.category_id = category.id

        self.admin_headers = self._login_headers("admin@example.com", "admin123")
        self.user_headers = self._login_headers("user@example.com", "user123")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login_headers(self, email, password):
        response = self.client.post(
            "/login", json={"email": email, "password": password}
        )
        self.assertEqual(200, response.status_code, response.get_json())
        return {"Authorization": f"Bearer {response.get_json()['token']}"}

    def test_protected_endpoints_reject_anonymous_and_tampered_tokens(self):
        for method, path in (
            ("GET", "/users"),
            ("GET", "/tasks"),
            ("GET", "/categories"),
            ("GET", "/reports/summary"),
        ):
            response = self.client.open(path, method=method)
            self.assertEqual(401, response.status_code, path)

        response = self.client.get(
            "/tasks", headers={"Authorization": "Bearer altered.token"}
        )
        self.assertEqual(401, response.status_code)

    def test_expired_token_is_rejected(self):
        with patch("itsdangerous.timed.time.time", return_value=1000):
            headers = self._login_headers("user@example.com", "user123")
        with patch("itsdangerous.timed.time.time", return_value=1002):
            response = self.client.get("/tasks", headers=headers)
        self.assertEqual(401, response.status_code)
        self.assertEqual("Token expirado", response.get_json()["error"])

    def test_password_hash_never_leaves_the_api(self):
        created = self.client.post(
            "/users",
            json={
                "name": "Created",
                "email": "created@example.com",
                "password": "CreatedPass!2026",
            },
        )
        self.assertEqual(201, created.status_code)
        self.assertNotIn("password", created.get_json())

        login = self.client.post(
            "/login",
            json={
                "email": "created@example.com",
                "password": "CreatedPass!2026",
            },
        )
        self.assertEqual(200, login.status_code)
        self.assertNotIn("password", login.get_json()["user"])

        with self.app.app_context():
            stored = db.session.get(User, created.get_json()["id"])
            self.assertNotEqual("CreatedPass!2026", stored.password)
            self.assertFalse(re.fullmatch(r"[0-9a-f]{32}", stored.password))

    def test_role_escalation_and_cross_user_access_are_blocked(self):
        registration = self.client.post(
            "/users",
            json={
                "name": "Attacker",
                "email": "attacker@example.com",
                "password": "AttackerPass!2026",
                "role": "admin",
            },
        )
        self.assertEqual(403, registration.status_code)

        role_update = self.client.put(
            f"/users/{self.user_id}",
            headers=self.user_headers,
            json={"role": "admin"},
        )
        self.assertEqual(403, role_update.status_code)

        other_update = self.client.put(
            f"/users/{self.other_id}",
            headers=self.user_headers,
            json={"name": "Compromised"},
        )
        self.assertEqual(403, other_update.status_code)

        task_read = self.client.get(
            f"/tasks/{self.task_id}", headers=self.user_headers
        )
        self.assertEqual(403, task_read.status_code)

        admin_read = self.client.get(
            f"/tasks/{self.task_id}", headers=self.admin_headers
        )
        self.assertEqual(200, admin_read.status_code)

    def test_invalid_inputs_return_400_instead_of_500(self):
        for path in (
            "/tasks/search?priority=abc",
            "/tasks/search?user_id=abc",
            "/tasks?page=zero",
        ):
            response = self.client.get(path, headers=self.admin_headers)
            self.assertEqual(400, response.status_code, path)

        response = self.client.put(
            f"/categories/{self.category_id}", headers=self.admin_headers
        )
        self.assertEqual(400, response.status_code)

        weak_password = self.client.post(
            "/users",
            json={
                "name": "Weak Password",
                "email": "weak@example.com",
                "password": "short",
            },
        )
        self.assertEqual(400, weak_password.status_code)

    def test_pagination_caps_large_requests(self):
        with self.app.app_context():
            for index in range(120):
                db.session.add(
                    Task(title=f"Task {index:03}", user_id=self.user_id)
                )
            db.session.commit()

        response = self.client.get(
            "/tasks?per_page=1000", headers=self.admin_headers
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(100, len(response.get_json()))

    def test_deletions_preserve_integrity(self):
        category_delete = self.client.delete(
            f"/categories/{self.category_id}", headers=self.admin_headers
        )
        self.assertEqual(200, category_delete.status_code)
        remaining_task = self.client.get(
            f"/tasks/{self.task_id}", headers=self.admin_headers
        )
        self.assertEqual(200, remaining_task.status_code)
        self.assertIsNone(remaining_task.get_json()["category_id"])

        user_delete = self.client.delete(
            f"/users/{self.other_id}", headers=self.admin_headers
        )
        self.assertEqual(200, user_delete.status_code)
        deleted_task = self.client.get(
            f"/tasks/{self.task_id}", headers=self.admin_headers
        )
        self.assertEqual(404, deleted_task.status_code)

    def test_task_list_avoids_n_plus_one_queries(self):
        with self.app.app_context():
            for index in range(20):
                db.session.add(
                    Task(
                        title=f"Query task {index}",
                        user_id=self.user_id,
                        category_id=self.category_id,
                    )
                )
            db.session.commit()
            engine = db.engine

        statements = []

        def record_query(*args):
            statements.append(args[2])

        event.listen(engine, "before_cursor_execute", record_query)
        try:
            response = self.client.get("/tasks", headers=self.admin_headers)
        finally:
            event.remove(engine, "before_cursor_execute", record_query)

        self.assertEqual(200, response.status_code)
        self.assertLessEqual(len(statements), 2, statements)

    def test_routes_are_thin_and_import_has_no_database_side_effect(self):
        project_root = Path(__file__).resolve().parents[1]
        for route_file in (project_root / "routes").glob("*_routes.py"):
            source = route_file.read_text(encoding="utf-8")
            self.assertNotIn("from database import", source)
            self.assertNotRegex(source, r"\bdb\.")
            self.assertNotRegex(source, r"\.query\b")

        app_source = (project_root / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("db.create_all", app_source)
        self.assertFalse(hasattr(__import__("app"), "app"))

    def test_runtime_configuration_requires_a_strong_secret(self):
        with patch.dict(os.environ, {"SECRET_KEY": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "SECRET_KEY"):
                create_app()


if __name__ == "__main__":
    unittest.main()
