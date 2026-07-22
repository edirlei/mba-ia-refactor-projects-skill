class CategoryController:
    def __init__(self, category_service):
        self.category_service = category_service

    def list(self, page, per_page):
        return self.category_service.list_categories(page, per_page)

    def create(self, data):
        return self.category_service.create_category(data)

    def update(self, category_id, data):
        return self.category_service.update_category(category_id, data)

    def delete(self, category_id):
        return self.category_service.delete_category(category_id)
