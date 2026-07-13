import logging


LOGGER = logging.getLogger(__name__)


class OrderService:
    def __init__(self, order_repository):
        self._order_repository = order_repository

    def create(self, user_id, items):
        result = self._order_repository.create(user_id, items)
        LOGGER.info("order_created", extra={"order_id": result["pedido_id"]})
        return result

    def list_all(self, *, user_id=None, limit, offset):
        return self._order_repository.list_all(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def update_status(self, order_id, status):
        self._order_repository.update_status(order_id, status)
        LOGGER.info("order_status_updated", extra={"order_id": order_id})
