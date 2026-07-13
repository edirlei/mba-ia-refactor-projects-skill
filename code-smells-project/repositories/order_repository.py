import sqlite3

from errors import ConflictError, NotFoundError, ValidationError
from models import Order, OrderItem


class OrderRepository:
    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    def create(self, user_id, items):
        connection = self._connection_provider()
        try:
            connection.execute("BEGIN IMMEDIATE")
            user = connection.execute(
                "SELECT id FROM usuarios WHERE id = ?",
                (user_id,),
            ).fetchone()
            if user is None:
                raise ValidationError("Usuário não encontrado")

            prepared_items = []
            total = 0
            for item in items:
                product = connection.execute(
                    """
                    SELECT id, nome, preco, estoque
                    FROM produtos
                    WHERE id = ? AND ativo = 1
                    """,
                    (item["produto_id"],),
                ).fetchone()
                if product is None:
                    raise ValidationError(
                        f"Produto {item['produto_id']} não encontrado"
                    )
                if product["estoque"] < item["quantidade"]:
                    raise ValidationError(
                        f"Estoque insuficiente para {product['nome']}"
                    )
                prepared_items.append((product, item["quantidade"]))
                total += product["preco"] * item["quantidade"]

            cursor = connection.execute(
                """
                INSERT INTO pedidos (usuario_id, status, total)
                VALUES (?, ?, ?)
                """,
                (user_id, "pendente", total),
            )
            order_id = cursor.lastrowid

            for product, quantity in prepared_items:
                connection.execute(
                    """
                    INSERT INTO itens_pedido
                        (pedido_id, produto_id, quantidade, preco_unitario)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, product["id"], quantity, product["preco"]),
                )
                update = connection.execute(
                    """
                    UPDATE produtos
                    SET estoque = estoque - ?
                    WHERE id = ? AND estoque >= ?
                    """,
                    (quantity, product["id"], quantity),
                )
                if update.rowcount != 1:
                    raise ConflictError("Estoque alterado durante o pedido")

            connection.commit()
            return {"pedido_id": order_id, "total": total}
        except (ValidationError, ConflictError):
            connection.rollback()
            raise
        except sqlite3.Error as error:
            connection.rollback()
            raise ConflictError("Não foi possível concluir o pedido") from error

    def list_all(self, *, user_id=None, limit, offset):
        user_filter = "WHERE usuario_id = ?" if user_id is not None else ""
        parameters = [user_id] if user_id is not None else []
        parameters.extend((limit, offset))

        rows = self._connection_provider().execute(
            f"""
            WITH selected_orders AS (
                SELECT id, usuario_id, status, total, criado_em
                FROM pedidos
                {user_filter}
                ORDER BY id
                LIMIT ? OFFSET ?
            )
            SELECT
                selected_orders.id AS order_id,
                selected_orders.usuario_id,
                selected_orders.status,
                selected_orders.total,
                selected_orders.criado_em,
                itens_pedido.id AS item_id,
                itens_pedido.produto_id,
                produtos.nome AS produto_nome,
                itens_pedido.quantidade,
                itens_pedido.preco_unitario
            FROM selected_orders
            LEFT JOIN itens_pedido
                ON itens_pedido.pedido_id = selected_orders.id
            LEFT JOIN produtos
                ON produtos.id = itens_pedido.produto_id
            ORDER BY selected_orders.id, itens_pedido.id
            """,
            parameters,
        ).fetchall()

        orders = {}
        for row in rows:
            order_id = row["order_id"]
            if order_id not in orders:
                orders[order_id] = Order(
                    id=order_id,
                    usuario_id=row["usuario_id"],
                    status=row["status"],
                    total=row["total"],
                    criado_em=row["criado_em"],
                )
            if row["item_id"] is not None:
                orders[order_id].itens.append(
                    OrderItem(
                        produto_id=row["produto_id"],
                        produto_nome=row["produto_nome"] or "Desconhecido",
                        quantidade=row["quantidade"],
                        preco_unitario=row["preco_unitario"],
                    )
                )
        return list(orders.values())

    def update_status(self, order_id, status):
        connection = self._connection_provider()
        cursor = connection.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (status, order_id),
        )
        connection.commit()
        if cursor.rowcount == 0:
            raise NotFoundError("Pedido não encontrado")
