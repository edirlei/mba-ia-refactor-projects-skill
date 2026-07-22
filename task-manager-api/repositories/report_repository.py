from datetime import timedelta

from sqlalchemy import case, func, select

from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.time import utc_now


class ReportRepository:
    def __init__(self, detail_limit):
        self.detail_limit = detail_limit

    def summary_data(self):
        now = utc_now()
        seven_days_ago = now - timedelta(days=7)

        total_tasks = db.session.scalar(select(func.count(Task.id))) or 0
        total_users = db.session.scalar(select(func.count(User.id))) or 0
        total_categories = db.session.scalar(select(func.count(Category.id))) or 0

        status_rows = db.session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        ).all()
        priority_rows = db.session.execute(
            select(Task.priority, func.count(Task.id)).group_by(Task.priority)
        ).all()

        overdue_statement = (
            select(Task)
            .where(
                Task.due_date.is_not(None),
                Task.due_date < now,
                Task.status.not_in(("done", "cancelled")),
            )
            .order_by(Task.due_date)
            .limit(self.detail_limit)
        )
        overdue_tasks = list(db.session.scalars(overdue_statement))
        overdue_count = db.session.scalar(
            select(func.count(Task.id)).where(
                Task.due_date.is_not(None),
                Task.due_date < now,
                Task.status.not_in(("done", "cancelled")),
            )
        ) or 0

        recent_tasks = db.session.scalar(
            select(func.count(Task.id)).where(Task.created_at >= seven_days_ago)
        ) or 0
        recent_done = db.session.scalar(
            select(func.count(Task.id)).where(
                Task.status == "done", Task.updated_at >= seven_days_ago
            )
        ) or 0

        user_rows = db.session.execute(
            select(
                User.id,
                User.name,
                func.count(Task.id),
                func.sum(case((Task.status == "done", 1), else_=0)),
            )
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
            .order_by(User.id)
        ).all()

        return {
            "now": now,
            "total_tasks": int(total_tasks),
            "total_users": int(total_users),
            "total_categories": int(total_categories),
            "status_counts": {status: count for status, count in status_rows},
            "priority_counts": {priority: count for priority, count in priority_rows},
            "overdue_tasks": overdue_tasks,
            "overdue_count": int(overdue_count),
            "recent_tasks": int(recent_tasks),
            "recent_done": int(recent_done),
            "user_rows": user_rows,
        }
