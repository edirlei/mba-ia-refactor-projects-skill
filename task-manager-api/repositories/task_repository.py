from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from utils.time import utc_now


class TaskRepository:
    @staticmethod
    def _with_scope(statement, user_id):
        if user_id is not None:
            return statement.where(Task.user_id == user_id)
        return statement

    def list(self, page, per_page, user_id=None):
        statement = (
            select(Task)
            .options(joinedload(Task.user), joinedload(Task.category))
            .order_by(Task.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        statement = self._with_scope(statement, user_id)
        return list(db.session.scalars(statement).unique())

    def list_for_user(self, user_id, page, per_page):
        return self.list(page=page, per_page=per_page, user_id=user_id)

    def search(self, filters, page, per_page, scope_user_id=None):
        statement = select(Task).options(
            joinedload(Task.user), joinedload(Task.category)
        )
        statement = self._with_scope(statement, scope_user_id)
        if filters.get("q"):
            pattern = f"%{filters['q']}%"
            statement = statement.where(
                or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
            )
        if filters.get("status"):
            statement = statement.where(Task.status == filters["status"])
        if filters.get("priority") is not None:
            statement = statement.where(Task.priority == filters["priority"])
        if filters.get("user_id") is not None:
            statement = statement.where(Task.user_id == filters["user_id"])
        statement = (
            statement.order_by(Task.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(db.session.scalars(statement).unique())

    def get(self, task_id):
        return db.session.get(
            Task,
            task_id,
            options=(joinedload(Task.user), joinedload(Task.category)),
        )

    def add(self, task):
        db.session.add(task)

    def delete(self, task):
        db.session.delete(task)

    def stats(self, user_id=None):
        now = utc_now()
        statement = select(
            func.count(Task.id),
            func.sum(case((Task.status == "pending", 1), else_=0)),
            func.sum(case((Task.status == "in_progress", 1), else_=0)),
            func.sum(case((Task.status == "done", 1), else_=0)),
            func.sum(case((Task.status == "cancelled", 1), else_=0)),
            func.sum(
                case(
                    (
                        Task.due_date.is_not(None)
                        & (Task.due_date < now)
                        & Task.status.not_in(("done", "cancelled")),
                        1,
                    ),
                    else_=0,
                )
            ),
        )
        statement = self._with_scope(statement, user_id)
        total, pending, in_progress, done, cancelled, overdue = db.session.execute(
            statement
        ).one()
        total = int(total or 0)
        done = int(done or 0)
        return {
            "total": total,
            "pending": int(pending or 0),
            "in_progress": int(in_progress or 0),
            "done": done,
            "cancelled": int(cancelled or 0),
            "overdue": int(overdue or 0),
            "completion_rate": round((done / total) * 100, 2) if total else 0,
        }

    def high_priority_count(self, user_id):
        statement = select(func.count(Task.id)).where(
            Task.user_id == user_id,
            Task.priority <= 2,
        )
        return int(db.session.scalar(statement) or 0)
