from sqlalchemy import delete, func, select
from sqlalchemy.orm import noload

from database import db
from models.task import Task
from models.user import User


class UserRepository:
    def list_with_task_counts(self, page, per_page):
        statement = (
            select(User, func.count(Task.id).label("task_count"))
            .outerjoin(Task, Task.user_id == User.id)
            .options(noload(User.tasks))
            .group_by(User.id)
            .order_by(User.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return db.session.execute(statement).all()

    def get(self, user_id):
        return db.session.get(User, user_id, options=(noload(User.tasks),))

    def find_by_email(self, email):
        statement = select(User).options(noload(User.tasks)).where(User.email == email)
        return db.session.scalar(statement)

    def add(self, user):
        db.session.add(user)

    def delete_with_tasks(self, user):
        db.session.execute(delete(Task).where(Task.user_id == user.id))
        db.session.delete(user)
