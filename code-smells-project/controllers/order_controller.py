class OrderController:
    def __init__(self, order_service):
        self._order_service = order_service

    def create(self, order_data):
        return self._order_service.create(
            order_data["usuario_id"],
            order_data["itens"],
        )

    def list_all(self, *, user_id=None, limit, offset):
        return [
            order.to_dict()
            for order in self._order_service.list_all(
                user_id=user_id,
                limit=limit,
                offset=offset,
            )
        ]

    def update_status(self, order_id, status):
        self._order_service.update_status(order_id, status)
