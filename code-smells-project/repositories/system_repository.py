class SystemRepository:
    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    def health_counts(self):
        row = self._connection_provider().execute(
            """
            SELECT
                (SELECT COUNT(id) FROM produtos) AS produtos,
                (SELECT COUNT(id) FROM usuarios) AS usuarios,
                (SELECT COUNT(id) FROM pedidos) AS pedidos
            """
        ).fetchone()
        return dict(row)

    def reset(self):
        connection = self._connection_provider()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM itens_pedido")
            connection.execute("DELETE FROM pedidos")
            connection.execute("DELETE FROM produtos")
            connection.execute("DELETE FROM usuarios")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
