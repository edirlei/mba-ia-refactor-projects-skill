from flask import Blueprint, jsonify, request


def create_system_blueprint(controller):
    blueprint = Blueprint("system", __name__)

    @blueprint.get("/")
    def index():
        return jsonify(
            {
                "mensagem": "Bem-vindo à API da Loja",
                "versao": "1.0.0",
                "endpoints": {
                    "produtos": "/produtos",
                    "usuarios": "/usuarios",
                    "pedidos": "/pedidos",
                    "login": "/login",
                    "relatorios": "/relatorios/vendas",
                    "health": "/health",
                },
            }
        ), 200

    @blueprint.get("/health")
    def health_check():
        return jsonify(
            {
                "status": "ok",
                "database": "connected",
                "counts": controller.health(),
                "versao": "1.0.0",
            }
        ), 200

    @blueprint.post("/admin/reset-db")
    def reset_database():
        controller.reset_database(request.headers.get("X-Admin-Token"))
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @blueprint.post("/admin/query")
    def reject_arbitrary_query():
        controller.reject_arbitrary_query()

    return blueprint
