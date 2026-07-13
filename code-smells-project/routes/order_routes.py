from flask import Blueprint, jsonify, request

from schemas import (
    parse_order_payload,
    parse_pagination,
    parse_status_payload,
    require_json_object,
)


def create_order_blueprint(controller):
    blueprint = Blueprint("orders", __name__)

    @blueprint.post("/pedidos")
    def create_order():
        order = parse_order_payload(require_json_object(request))
        result = controller.create(order)
        return jsonify(
            {
                "dados": result,
                "sucesso": True,
                "mensagem": "Pedido criado com sucesso",
            }
        ), 201

    @blueprint.get("/pedidos")
    def list_orders():
        limit, offset = parse_pagination(request.args)
        orders = controller.list_all(limit=limit, offset=offset)
        return jsonify({"dados": orders, "sucesso": True}), 200

    @blueprint.get("/pedidos/usuario/<int:user_id>")
    def list_user_orders(user_id):
        limit, offset = parse_pagination(request.args)
        orders = controller.list_all(user_id=user_id, limit=limit, offset=offset)
        return jsonify({"dados": orders, "sucesso": True}), 200

    @blueprint.put("/pedidos/<int:order_id>/status")
    def update_order_status(order_id):
        status = parse_status_payload(require_json_object(request))
        controller.update_status(order_id, status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    return blueprint
