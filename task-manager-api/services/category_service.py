from database import db
from errors import NotFoundError
from models.category import Category


class CategoryService:
    def __init__(self, category_repository):
        self.category_repository = category_repository

    def list_categories(self, page, per_page):
        rows = self.category_repository.list_with_task_counts(page, per_page)
        result = []
        for category, task_count in rows:
            data = category.to_dict()
            data["task_count"] = int(task_count)
            result.append(data)
        return result

    def create_category(self, data):
        category = Category(**data)
        self.category_repository.add(category)
        self._commit()
        return category.to_dict()

    def update_category(self, category_id, data):
        category = self._get_category(category_id)
        for field in ("name", "description", "color"):
            if field in data:
                setattr(category, field, data[field])
        self._commit()
        return category.to_dict()

    def delete_category(self, category_id):
        category = self._get_category(category_id)
        self.category_repository.delete_and_unassign_tasks(category)
        self._commit()
        return {"message": "Categoria deletada"}

    def _get_category(self, category_id):
        category = self.category_repository.get(category_id)
        if not category:
            raise NotFoundError("Categoria não encontrada")
        return category

    @staticmethod
    def _commit():
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
