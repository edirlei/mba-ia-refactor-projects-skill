from models import Product


PRODUCT_COLUMNS = """
    id, nome, descricao, preco, estoque, categoria, ativo, criado_em
"""


class ProductRepository:
    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    def list_all(self, *, limit, offset):
        rows = self._connection_provider().execute(
            f"""
            SELECT {PRODUCT_COLUMNS}
            FROM produtos
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [Product.from_row(row) for row in rows]

    def find_by_id(self, product_id):
        row = self._connection_provider().execute(
            f"SELECT {PRODUCT_COLUMNS} FROM produtos WHERE id = ?",
            (product_id,),
        ).fetchone()
        return Product.from_row(row) if row else None

    def create(self, product):
        connection = self._connection_provider()
        cursor = connection.execute(
            """
            INSERT INTO produtos (nome, descricao, preco, estoque, categoria)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                product["nome"],
                product["descricao"],
                product["preco"],
                product["estoque"],
                product["categoria"],
            ),
        )
        connection.commit()
        return cursor.lastrowid

    def update(self, product_id, product):
        connection = self._connection_provider()
        cursor = connection.execute(
            """
            UPDATE produtos
            SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
            WHERE id = ?
            """,
            (
                product["nome"],
                product["descricao"],
                product["preco"],
                product["estoque"],
                product["categoria"],
                product_id,
            ),
        )
        connection.commit()
        return cursor.rowcount > 0

    def delete(self, product_id):
        connection = self._connection_provider()
        cursor = connection.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
        connection.commit()
        return cursor.rowcount > 0

    def search(self, filters, *, limit, offset):
        query = f"SELECT {PRODUCT_COLUMNS} FROM produtos WHERE 1 = 1"
        parameters = []

        if filters["termo"]:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            term = f"%{filters['termo']}%"
            parameters.extend((term, term))
        if filters["categoria"]:
            query += " AND categoria = ?"
            parameters.append(filters["categoria"])
        if filters["preco_min"] is not None:
            query += " AND preco >= ?"
            parameters.append(filters["preco_min"])
        if filters["preco_max"] is not None:
            query += " AND preco <= ?"
            parameters.append(filters["preco_max"])

        query += " ORDER BY id LIMIT ? OFFSET ?"
        parameters.extend((limit, offset))
        rows = self._connection_provider().execute(query, parameters).fetchall()
        return [Product.from_row(row) for row in rows]
