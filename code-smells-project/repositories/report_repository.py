class ReportRepository:
    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    def sales_totals(self):
        row = self._connection_provider().execute(
            """
            SELECT
                COUNT(id) AS total_pedidos,
                COALESCE(SUM(total), 0) AS faturamento,
                COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
                COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
                COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
            FROM pedidos
            """,
            ("pendente", "aprovado", "cancelado"),
        ).fetchone()
        return dict(row)
