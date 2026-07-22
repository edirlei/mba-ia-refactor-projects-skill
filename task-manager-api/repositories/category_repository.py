from sqlalchemy import func, select, update
from sqlalchemy.orm import noload

from database import db
from models.category import Category
from models.task import Task


class CategoryRepository:
    def list_with_task_counts(self, page, per_page):
        statement = (
            select(Category, func.count(Task.id).label("task_count"))
            .outerjoin(Task, Task.category_id == Category.id)
            .options(noload(Category.tasks))
            .group_by(Category.id)
            .order_by(Category.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return db.session.execute(statement).all()

    def get(self, category_id):
        return db.session.get(
            Category, category_id, options=(noload(Category.tasks),)
        )

    def add(self, category):
        db.session.add(category)

    def delete_and_unassign_tasks(self, category):
        db.session.execute(
            update(Task)
            .where(Task.category_id == category.id)
            .values(category_id=None)
        )
        db.session.delete(category)
