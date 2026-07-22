from errors import AuthorizationError, NotFoundError
from utils.time import as_utc


class ReportService:
    def __init__(self, report_repository, task_repository, user_repository):
        self.report_repository = report_repository
        self.task_repository = task_repository
        self.user_repository = user_repository

    def summary(self):
        data = self.report_repository.summary_data()
        status_counts = data["status_counts"]
        priority_counts = data["priority_counts"]
        overdue_tasks = [
            {
                "id": task.id,
                "title": task.title,
                "due_date": str(task.due_date),
                "days_overdue": (as_utc(data["now"]) - as_utc(task.due_date)).days,
            }
            for task in data["overdue_tasks"]
        ]
        user_productivity = []
        for user_id, user_name, total, completed in data["user_rows"]:
            total = int(total or 0)
            completed = int(completed or 0)
            user_productivity.append(
                {
                    "user_id": user_id,
                    "user_name": user_name,
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "completion_rate": (
                        round((completed / total) * 100, 2) if total else 0
                    ),
                }
            )

        return {
            "generated_at": str(data["now"]),
            "overview": {
                "total_tasks": data["total_tasks"],
                "total_users": data["total_users"],
                "total_categories": data["total_categories"],
            },
            "tasks_by_status": {
                status: int(status_counts.get(status, 0))
                for status in ("pending", "in_progress", "done", "cancelled")
            },
            "tasks_by_priority": {
                "critical": int(priority_counts.get(1, 0)),
                "high": int(priority_counts.get(2, 0)),
                "medium": int(priority_counts.get(3, 0)),
                "low": int(priority_counts.get(4, 0)),
                "minimal": int(priority_counts.get(5, 0)),
            },
            "overdue": {
                "count": data["overdue_count"],
                "tasks": overdue_tasks,
            },
            "recent_activity": {
                "tasks_created_last_7_days": data["recent_tasks"],
                "tasks_completed_last_7_days": data["recent_done"],
            },
            "user_productivity": user_productivity,
        }

    def user_report(self, actor, user_id):
        user = self.user_repository.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")
        if not actor.is_staff() and actor.id != user.id:
            raise AuthorizationError()

        stats = self.task_repository.stats(user_id)
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "statistics": {
                "total_tasks": stats["total"],
                "done": stats["done"],
                "pending": stats["pending"],
                "in_progress": stats["in_progress"],
                "cancelled": stats["cancelled"],
                "overdue": stats["overdue"],
                "high_priority": self.task_repository.high_priority_count(user_id),
                "completion_rate": stats["completion_rate"],
            },
        }
