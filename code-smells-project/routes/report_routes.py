from flask import Blueprint, jsonify


def create_report_blueprint(controller):
    blueprint = Blueprint("reports", __name__)

    @blueprint.get("/relatorios/vendas")
    def sales_report():
        return jsonify({"dados": controller.sales_report(), "sucesso": True}), 200

    return blueprint
