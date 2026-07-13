from flask import Blueprint, jsonify, request

from schemas import (
    parse_pagination,
    parse_product_payload,
    parse_search_filters,
    require_json_object,
)


def create_product_blueprint(controller):
    blueprint = Blueprint("products", __name__)

    @blueprint.get("/produtos")
    def list_products():
        limit, offset = parse_pagination(request.args)
        products = controller.list_all(limit=limit, offset=offset)
        return jsonify({"dados": products, "sucesso": True}), 200

    @blueprint.get("/produtos/busca")
    def search_products():
        filters = parse_search_filters(request.args)
        limit, offset = parse_pagination(request.args)
        products = controller.search(filters, limit=limit, offset=offset)
        return jsonify(
            {"dados": products, "total": len(products), "sucesso": True}
        ), 200

    @blueprint.get("/produtos/<int:product_id>")
    def get_product(product_id):
        return jsonify({"dados": controller.get_by_id(product_id), "sucesso": True}), 200

    @blueprint.post("/produtos")
    def create_product():
        product = parse_product_payload(require_json_object(request))
        product_id = controller.create(product)
        return jsonify(
            {
                "dados": {"id": product_id},
                "sucesso": True,
                "mensagem": "Produto criado",
            }
        ), 201

    @blueprint.put("/produtos/<int:product_id>")
    def update_product(product_id):
        product = parse_product_payload(require_json_object(request))
        controller.update(product_id, product)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @blueprint.delete("/produtos/<int:product_id>")
    def delete_product(product_id):
        controller.delete(product_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    return blueprint
