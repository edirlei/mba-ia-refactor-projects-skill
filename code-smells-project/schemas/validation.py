from errors import ValidationError


VALID_CATEGORIES = {
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
}
VALID_ORDER_STATUSES = {
    "pendente",
    "aprovado",
    "enviado",
    "entregue",
    "cancelado",
}
MAX_PAGE_SIZE = 100


def require_json_object(request):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    return data


def parse_product_payload(data):
    for field, label in (
        ("nome", "Nome"),
        ("preco", "Preço"),
        ("estoque", "Estoque"),
    ):
        if field not in data:
            raise ValidationError(f"{label} é obrigatório")

    name = data["nome"]
    price = data["preco"]
    stock = data["estoque"]
    category = data.get("categoria", "geral")
    description = data.get("descricao", "")

    if not isinstance(name, str) or not 2 <= len(name) <= 200:
        raise ValidationError("Nome deve ter entre 2 e 200 caracteres")
    if not isinstance(description, str):
        raise ValidationError("Descrição inválida")
    if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
        raise ValidationError("Preço não pode ser negativo")
    if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if category not in VALID_CATEGORIES:
        raise ValidationError(f"Categoria inválida. Válidas: {sorted(VALID_CATEGORIES)}")

    return {
        "nome": name,
        "descricao": description,
        "preco": price,
        "estoque": stock,
        "categoria": category,
    }


def parse_user_payload(data):
    name = data.get("nome", "")
    email = data.get("email", "")
    password = data.get("senha", "")
    if not all(isinstance(value, str) and value.strip() for value in (name, email, password)):
        raise ValidationError("Nome, email e senha são obrigatórios")
    if "@" not in email or len(email) > 254:
        raise ValidationError("Email inválido")
    if len(password) < 8:
        raise ValidationError("Senha deve ter pelo menos 8 caracteres")
    return {"nome": name.strip(), "email": email.strip().lower(), "senha": password}


def parse_login_payload(data):
    email = data.get("email", "")
    password = data.get("senha", "")
    if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
        raise ValidationError("Email e senha são obrigatórios")
    return {"email": email.strip().lower(), "senha": password}


def parse_order_payload(data):
    user_id = data.get("usuario_id")
    items = data.get("itens")
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValidationError("Usuario ID é obrigatório")
    if not isinstance(items, list) or not items:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    parsed_items = []
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("Item do pedido inválido")
        product_id = item.get("produto_id")
        quantity = item.get("quantidade")
        if isinstance(product_id, bool) or not isinstance(product_id, int) or product_id <= 0:
            raise ValidationError("Produto ID inválido")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
        parsed_items.append({"produto_id": product_id, "quantidade": quantity})

    return {"usuario_id": user_id, "itens": parsed_items}


def parse_status_payload(data):
    status = data.get("status", "")
    if status not in VALID_ORDER_STATUSES:
        raise ValidationError("Status inválido")
    return status


def parse_pagination(arguments):
    try:
        page = int(arguments.get("page", 1))
        page_size = int(arguments.get("page_size", MAX_PAGE_SIZE))
    except (TypeError, ValueError) as error:
        raise ValidationError("Paginação inválida") from error
    if page < 1 or page_size < 1 or page_size > MAX_PAGE_SIZE:
        raise ValidationError(f"page_size deve estar entre 1 e {MAX_PAGE_SIZE}")
    return page_size, (page - 1) * page_size


def parse_search_filters(arguments):
    filters = {
        "termo": arguments.get("q", ""),
        "categoria": arguments.get("categoria"),
        "preco_min": _optional_float(arguments.get("preco_min"), "preco_min"),
        "preco_max": _optional_float(arguments.get("preco_max"), "preco_max"),
    }
    if filters["categoria"] and filters["categoria"] not in VALID_CATEGORIES:
        raise ValidationError("Categoria inválida")
    if (
        filters["preco_min"] is not None
        and filters["preco_max"] is not None
        and filters["preco_min"] > filters["preco_max"]
    ):
        raise ValidationError("Faixa de preço inválida")
    return filters


def _optional_float(value, field):
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{field} inválido") from error
    if parsed < 0:
        raise ValidationError(f"{field} não pode ser negativo")
    return parsed
