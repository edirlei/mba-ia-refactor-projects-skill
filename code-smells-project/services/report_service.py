class ReportService:
    def __init__(self, report_repository):
        self._report_repository = report_repository

    def sales_report(self):
        totals = self._report_repository.sales_totals()
        revenue = totals["faturamento"]
        discount = self._discount_for(revenue)
        order_count = totals["total_pedidos"]
        return {
            "total_pedidos": order_count,
            "faturamento_bruto": round(revenue, 2),
            "desconto_aplicavel": round(discount, 2),
            "faturamento_liquido": round(revenue - discount, 2),
            "pedidos_pendentes": totals["pendentes"],
            "pedidos_aprovados": totals["aprovados"],
            "pedidos_cancelados": totals["cancelados"],
            "ticket_medio": round(revenue / order_count, 2) if order_count else 0,
        }

    @staticmethod
    def _discount_for(revenue):
        if revenue > 10000:
            return revenue * 0.10
        if revenue > 5000:
            return revenue * 0.05
        if revenue > 1000:
            return revenue * 0.02
        return 0
