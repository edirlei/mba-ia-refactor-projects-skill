import importlib
import os
import tempfile
import unittest


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls._database_path = os.path.join(
            cls._temporary_directory.name,
            "characterization.db",
        )

        os.environ["DATABASE_PATH"] = cls._database_path
        os.environ["SECRET_KEY"] = "test-only-secret"
        os.environ["ADMIN_TOKEN"] = "test-admin-token"
        os.environ["SEED_ADMIN_PASSWORD"] = "admin123"
        os.environ["SEED_USER_PASSWORD"] = "test-user-password"
        os.environ["SEED_SECOND_USER_PASSWORD"] = "test-second-user-password"

        cls._database_module = importlib.import_module("database")
        cls._is_legacy_database = hasattr(cls._database_module, "db_connection")

        if cls._is_legacy_database:
            cls._database_module.db_connection = None
            cls._database_module.db_path = cls._database_path

        app_module = importlib.import_module("app")
        if hasattr(app_module, "create_app"):
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
        else:
            cls.app = app_module.app
            cls.app.config.update(TESTING=True)

        with cls.app.app_context():
            cls._database_module.init_db()

        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        if cls._is_legacy_database:
            connection = cls._database_module.db_connection
            if connection is not None:
                connection.close()
                cls._database_module.db_connection = None

        cls._temporary_directory.cleanup()

    def test_01_original_route_inventory_contains_19_endpoints(self):
        routes = {
            (rule.rule, method)
            for rule in self.app.url_map.iter_rules()
            if rule.endpoint != "static"
            for method in rule.methods
            if method not in {"HEAD", "OPTIONS"}
        }
        self.assertEqual(19, len(routes))

    def test_02_original_endpoints_keep_their_public_contracts(self):
        responses = []

        responses.append(("GET /", self.client.get("/"), 200))
        responses.append(("GET /produtos", self.client.get("/produtos"), 200))
        responses.append(
            (
                "GET /produtos/busca",
                self.client.get("/produtos/busca?q=Mouse&categoria=informatica"),
                200,
            )
        )
        responses.append(
            ("GET /produtos/1", self.client.get("/produtos/1"), 200)
        )

        create_product = self.client.post(
            "/produtos",
            json={
                "nome": "Produto Teste",
                "descricao": "Criado pelo teste de caracterização",
                "preco": 25.5,
                "estoque": 4,
                "categoria": "geral",
            },
        )
        responses.append(("POST /produtos", create_product, 201))
        product_id = create_product.get_json()["dados"]["id"]

        responses.append(
            (
                "PUT /produtos/1",
                self.client.put(
                    "/produtos/1",
                    json={
                        "nome": "Notebook Gamer",
                        "descricao": "Notebook potente para jogos",
                        "preco": 5999.99,
                        "estoque": 10,
                        "categoria": "informatica",
                    },
                ),
                200,
            )
        )
        responses.append(
            (
                "DELETE /produtos/<id>",
                self.client.delete(f"/produtos/{product_id}"),
                200,
            )
        )

        responses.append(("GET /usuarios", self.client.get("/usuarios"), 200))
        responses.append(
            ("GET /usuarios/1", self.client.get("/usuarios/1"), 200)
        )
        responses.append(
            (
                "POST /usuarios",
                self.client.post(
                    "/usuarios",
                    json={
                        "nome": "Usuário Teste",
                        "email": "teste@example.com",
                        "senha": "senha-segura-123",
                    },
                ),
                201,
            )
        )
        responses.append(
            (
                "POST /login",
                self.client.post(
                    "/login",
                    json={"email": "admin@loja.com", "senha": "admin123"},
                ),
                200,
            )
        )

        create_order = self.client.post(
            "/pedidos",
            json={"usuario_id": 1, "itens": [{"produto_id": 1, "quantidade": 1}]},
        )
        responses.append(("POST /pedidos", create_order, 201))
        order_id = create_order.get_json()["dados"]["pedido_id"]

        responses.append(("GET /pedidos", self.client.get("/pedidos"), 200))
        responses.append(
            (
                "GET /pedidos/usuario/1",
                self.client.get("/pedidos/usuario/1"),
                200,
            )
        )
        responses.append(
            (
                "PUT /pedidos/<id>/status",
                self.client.put(
                    f"/pedidos/{order_id}/status",
                    json={"status": "aprovado"},
                ),
                200,
            )
        )
        responses.append(
            ("GET /relatorios/vendas", self.client.get("/relatorios/vendas"), 200)
        )
        responses.append(("GET /health", self.client.get("/health"), 200))

        query_response = self.client.post(
            "/admin/query",
            json={"sql": "SELECT 1 AS ok"},
        )
        responses.append(("POST /admin/query", query_response, {200, 403}))

        reset_response = self.client.post("/admin/reset-db")
        responses.append(("POST /admin/reset-db", reset_response, {200, 403}))

        self.assertEqual(19, len(responses))
        for label, response, expected_status in responses:
            with self.subTest(endpoint=label):
                if isinstance(expected_status, set):
                    self.assertIn(response.status_code, expected_status)
                else:
                    self.assertEqual(expected_status, response.status_code)
                self.assertIsNotNone(response.get_json(silent=True))


if __name__ == "__main__":
    unittest.main()
