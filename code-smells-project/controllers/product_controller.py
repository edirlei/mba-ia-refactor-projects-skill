from errors import NotFoundError


class ProductController:
    def __init__(self, product_repository):
        self._product_repository = product_repository

    def list_all(self, *, limit, offset):
        return [
            product.to_dict()
            for product in self._product_repository.list_all(limit=limit, offset=offset)
        ]

    def search(self, filters, *, limit, offset):
        return [
            product.to_dict()
            for product in self._product_repository.search(
                filters,
                limit=limit,
                offset=offset,
            )
        ]

    def get_by_id(self, product_id):
        product = self._product_repository.find_by_id(product_id)
        if product is None:
            raise NotFoundError("Produto não encontrado")
        return product.to_dict()

    def create(self, product_data):
        return self._product_repository.create(product_data)

    def update(self, product_id, product_data):
        if not self._product_repository.update(product_id, product_data):
            raise NotFoundError("Produto não encontrado")

    def delete(self, product_id):
        if not self._product_repository.delete(product_id):
            raise NotFoundError("Produto não encontrado")
