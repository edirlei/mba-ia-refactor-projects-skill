import importlib
import os
import tempfile
import unittest
from pathlib import Path

class SecurityAndArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls._database_path = os.path.join(cls._temporary_directory.name, "security.db")
        app_module = importlib.import_module("app")
        database_module = importlib.import_module("database")
        repositories_module = importlib.import_module("repositories")
        cls._get_db = staticmethod(database_module.get_db)
        cls._order_repository = repositories_module.OrderRepository
        cls.app = app_module.create_app(
            {
                "TESTING": True,
                "DATABASE": cls._database_path,
                "SECRET_KEY": "test-only-secret",
                "ADMIN_TOKEN": "test-admin-token",
                "SEED_PASSWORDS": {
                    "admin": "admin123",
                    "joao": "test-user-password",
                    "maria": "test-second-user-password",
                },
            }
        )
        with cls.app.app_context():
            database_module.init_db()
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls._temporary_directory.cleanup()

    def test_01_passwords_are_hashed_and_never_serialized(self):
        users_response = self.client.get("/usuarios")
        self.assertEqual(200, users_response.status_code)
        for user in users_response.get_json()["dados"]:
            self.assertNotIn("senha", user)
            self.assertNotIn("password_hash", user)

        user_response = self.client.get("/usuarios/1")
        self.assertNotIn("senha", user_response.get_json()["dados"])

        with self.app.app_context():
            stored_passwords = [
                row["senha"]
                for row in self._get_db().execute("SELECT senha FROM usuarios").fetchall()
            ]
        self.assertTrue(stored_passwords)
        self.assertTrue(
            all(
                password.startswith(("scrypt:", "pbkdf2:"))
                for password in stored_passwords
            )
        )
        self.assertNotIn("admin123", stored_passwords)

    def test_02_sql_input_is_parameterized_and_tables_remain_available(self):
        suspicious_name = "Produto '); DROP TABLE produtos; --"
        response = self.client.post(
            "/produtos",
            json={
                "nome": suspicious_name,
                "descricao": "Entrada tratada como dado",
                "preco": 10,
                "estoque": 2,
                "categoria": "geral",
            },
        )
        self.assertEqual(201, response.status_code)

        search = self.client.get("/produtos/busca", query_string={"q": "DROP TABLE"})
        self.assertEqual(200, search.status_code)
        self.assertEqual(suspicious_name, search.get_json()["dados"][0]["nome"])

        with self.app.app_context():
            count = self._get_db().execute(
                "SELECT COUNT(id) FROM produtos"
            ).fetchone()[0]
        self.assertGreater(count, 0)

    def test_03_order_failure_rolls_back_header_items_and_stock(self):
        with self.app.app_context():
            connection = self._get_db()
            initial_orders = connection.execute(
                "SELECT COUNT(id) FROM pedidos"
            ).fetchone()[0]
            initial_stock = connection.execute(
                "SELECT estoque FROM produtos WHERE id = ?",
                (1,),
            ).fetchone()[0]

        response = self.client.post(
            "/pedidos",
            json={
                "usuario_id": 1,
                "itens": [
                    {"produto_id": 1, "quantidade": 6},
                    {"produto_id": 1, "quantidade": 6},
                ],
            },
        )
        self.assertEqual(409, response.status_code)

        with self.app.app_context():
            connection = self._get_db()
            final_orders = connection.execute(
                "SELECT COUNT(id) FROM pedidos"
            ).fetchone()[0]
            final_items = connection.execute(
                "SELECT COUNT(id) FROM itens_pedido"
            ).fetchone()[0]
            final_stock = connection.execute(
                "SELECT estoque FROM produtos WHERE id = ?",
                (1,),
            ).fetchone()[0]

        self.assertEqual(initial_orders, final_orders)
        self.assertEqual(0, final_items)
        self.assertEqual(initial_stock, final_stock)

    def test_04_order_listing_uses_one_query_and_schema_has_foreign_keys(self):
        create_response = self.client.post(
            "/pedidos",
            json={
                "usuario_id": 1,
                "itens": [{"produto_id": 1, "quantidade": 1}],
            },
        )
        self.assertEqual(201, create_response.status_code)

        with self.app.app_context():
            connection = self._get_db()
            statements = []
            connection.set_trace_callback(statements.append)
            orders = self._order_repository(self._get_db).list_all(limit=100, offset=0)
            connection.set_trace_callback(None)

            order_foreign_keys = connection.execute(
                "PRAGMA foreign_key_list(pedidos)"
            ).fetchall()
            item_foreign_keys = connection.execute(
                "PRAGMA foreign_key_list(itens_pedido)"
            ).fetchall()

        list_queries = [
            statement
            for statement in statements
            if statement.lstrip().upper().startswith(("SELECT", "WITH"))
        ]
        self.assertTrue(orders)
        self.assertEqual(1, len(list_queries))
        self.assertEqual(1, len(order_foreign_keys))
        self.assertEqual(2, len(item_foreign_keys))

    def test_05_validation_conflicts_and_errors_are_safe(self):
        user_payload = {
            "nome": "Usuário Único",
            "email": "unico@example.com",
            "senha": "senha-segura-123",
        }
        self.assertEqual(201, self.client.post("/usuarios", json=user_payload).status_code)
        conflict = self.client.post("/usuarios", json=user_payload)
        self.assertEqual(409, conflict.status_code)
        self.assertNotIn("UNIQUE", conflict.get_data(as_text=True).upper())
        self.assertNotIn("SQLITE", conflict.get_data(as_text=True).upper())

        invalid = self.client.post("/pedidos", json={"usuario_id": "um", "itens": []})
        self.assertEqual(400, invalid.status_code)
        self.assertEqual(404, self.client.get("/rota-inexistente").status_code)

    def test_06_admin_routes_are_protected_and_arbitrary_sql_is_disabled(self):
        query = self.client.post(
            "/admin/query",
            json={"sql": "SELECT 1"},
            headers={"X-Admin-Token": "test-admin-token"},
        )
        self.assertEqual(403, query.status_code)

        unauthorized_reset = self.client.post("/admin/reset-db")
        self.assertEqual(403, unauthorized_reset.status_code)

        authorized_reset = self.client.post(
            "/admin/reset-db",
            headers={"X-Admin-Token": "test-admin-token"},
        )
        self.assertEqual(200, authorized_reset.status_code)

    def test_07_layer_boundaries_are_explicit(self):
        project_root = Path(__file__).resolve().parents[1]
        expected_directories = {
            "controllers",
            "models",
            "repositories",
            "routes",
            "schemas",
            "services",
        }
        self.assertTrue(
            all((project_root / directory).is_dir() for directory in expected_directories)
        )

        for route_file in (project_root / "routes").glob("*.py"):
            source = route_file.read_text(encoding="utf-8")
            self.assertNotIn("import sqlite3", source)
            self.assertNotIn("from database", source)
            self.assertNotIn("from repositories", source)

        for controller_file in (project_root / "controllers").glob("*.py"):
            source = controller_file.read_text(encoding="utf-8")
            self.assertNotIn("import sqlite3", source)
            self.assertNotIn("SELECT ", source)
            self.assertNotIn("INSERT ", source)

        model_source = (project_root / "models" / "entities.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("from flask", model_source)


if __name__ == "__main__":
    unittest.main()
