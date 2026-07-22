import importlib
import unittest

from database import db
from models.category import Category
from models.task import Task
from models.user import User


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module = importlib.import_module("app")
        if hasattr(app_module, "create_app"):
            cls.app = app_module.create_app(
                {
                    "TESTING": True,
                    "SECRET_KEY": "test-only-secret-key-with-32-bytes",
                    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                    "TOKEN_MAX_AGE_SECONDS": 3600,
                    "CORS_ORIGINS": ["http://localhost"],
                }
            )
        else:
            cls.app = app_module.app
            cls.app.config.update(TESTING=True)

        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.drop_all()
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
            category = Category(
                name="Initial Category",
                description="Contract fixture",
                color="#123456",
            )
            db.session.add_all([admin, user, category])
            db.session.flush()
            task = Task(
                title="Initial task",
                description="Contract fixture",
                status="pending",
                priority=3,
                user_id=user.id,
                category_id=category.id,
            )
            db.session.add(task)
            db.session.commit()

            cls.admin_id = admin.id
            cls.user_id = user.id
            cls.category_id = category.id
            cls.task_id = task.id

        cls.admin_headers = cls._login_headers("admin@example.com", "admin123")
        cls.user_headers = cls._login_headers("user@example.com", "user123")

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    @classmethod
    def _login_headers(cls, email, password):
        response = cls.client.post(
            "/login",
            json={"email": email, "password": password},
        )
        if response.status_code != 200:
            raise AssertionError(response.get_json())
        token = response.get_json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def assert_keys(self, payload, expected):
        self.assertTrue(set(expected).issubset(payload), payload)

    def test_01_general_endpoints(self):
        root = self.client.get("/")
        self.assertEqual(200, root.status_code)
        self.assert_keys(root.get_json(), {"message", "version"})

        health = self.client.get("/health")
        self.assertEqual(200, health.status_code)
        self.assert_keys(health.get_json(), {"status", "timestamp"})

    def test_02_user_endpoints(self):
        users = self.client.get("/users", headers=self.admin_headers)
        self.assertEqual(200, users.status_code)
        self.assertIsInstance(users.get_json(), list)

        user = self.client.get(
            f"/users/{self.user_id}", headers=self.user_headers
        )
        self.assertEqual(200, user.status_code)
        self.assert_keys(user.get_json(), {"id", "name", "email", "role", "tasks"})

        created = self.client.post(
            "/users",
            json={
                "name": "Created User",
                "email": "created@example.com",
                "password": "CreatedPass!2026",
                "role": "user",
            },
        )
        self.assertEqual(201, created.status_code)
        created_id = created.get_json()["id"]

        updated = self.client.put(
            f"/users/{created_id}",
            headers=self.admin_headers,
            json={"name": "Updated User"},
        )
        self.assertEqual(200, updated.status_code)
        self.assertEqual("Updated User", updated.get_json()["name"])

        tasks = self.client.get(
            f"/users/{self.user_id}/tasks", headers=self.user_headers
        )
        self.assertEqual(200, tasks.status_code)
        self.assertIsInstance(tasks.get_json(), list)

        deleted = self.client.delete(
            f"/users/{created_id}", headers=self.admin_headers
        )
        self.assertEqual(200, deleted.status_code)

    def test_03_login_endpoint(self):
        response = self.client.post(
            "/login",
            json={"email": "user@example.com", "password": "user123"},
        )
        self.assertEqual(200, response.status_code)
        self.assert_keys(response.get_json(), {"message", "user", "token"})

    def test_04_task_endpoints(self):
        tasks = self.client.get("/tasks", headers=self.admin_headers)
        self.assertEqual(200, tasks.status_code)
        self.assertIsInstance(tasks.get_json(), list)

        task = self.client.get(
            f"/tasks/{self.task_id}", headers=self.user_headers
        )
        self.assertEqual(200, task.status_code)
        self.assert_keys(task.get_json(), {"id", "title", "status", "priority"})

        created = self.client.post(
            "/tasks",
            headers=self.admin_headers,
            json={
                "title": "Created task",
                "user_id": self.user_id,
                "category_id": self.category_id,
            },
        )
        self.assertEqual(201, created.status_code)
        created_id = created.get_json()["id"]

        updated = self.client.put(
            f"/tasks/{created_id}",
            headers=self.admin_headers,
            json={"status": "in_progress"},
        )
        self.assertEqual(200, updated.status_code)
        self.assertEqual("in_progress", updated.get_json()["status"])

        search = self.client.get(
            "/tasks/search?q=task&priority=3", headers=self.admin_headers
        )
        self.assertEqual(200, search.status_code)
        self.assertIsInstance(search.get_json(), list)

        stats = self.client.get("/tasks/stats", headers=self.admin_headers)
        self.assertEqual(200, stats.status_code)
        self.assert_keys(stats.get_json(), {"total", "pending", "overdue"})

        deleted = self.client.delete(
            f"/tasks/{created_id}", headers=self.admin_headers
        )
        self.assertEqual(200, deleted.status_code)

    def test_05_report_endpoints(self):
        summary = self.client.get(
            "/reports/summary", headers=self.admin_headers
        )
        self.assertEqual(200, summary.status_code)
        self.assert_keys(
            summary.get_json(),
            {"generated_at", "overview", "tasks_by_status", "user_productivity"},
        )

        user_report = self.client.get(
            f"/reports/user/{self.user_id}", headers=self.user_headers
        )
        self.assertEqual(200, user_report.status_code)
        self.assert_keys(user_report.get_json(), {"user", "statistics"})

    def test_06_category_endpoints(self):
        categories = self.client.get("/categories", headers=self.user_headers)
        self.assertEqual(200, categories.status_code)
        self.assertIsInstance(categories.get_json(), list)

        created = self.client.post(
            "/categories",
            headers=self.admin_headers,
            json={"name": "Created Category", "color": "#abcdef"},
        )
        self.assertEqual(201, created.status_code)
        created_id = created.get_json()["id"]

        updated = self.client.put(
            f"/categories/{created_id}",
            headers=self.admin_headers,
            json={"description": "updated"},
        )
        self.assertEqual(200, updated.status_code)
        self.assertEqual("updated", updated.get_json()["description"])

        deleted = self.client.delete(
            f"/categories/{created_id}", headers=self.admin_headers
        )
        self.assertEqual(200, deleted.status_code)


if __name__ == "__main__":
    unittest.main()
