from database import db
from errors import AuthorizationError, NotFoundError
from models.task import Task
from utils.time import utc_now


class TaskService:
    def __init__(self, task_repository, user_repository, category_repository):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.category_repository = category_repository

    def list_tasks(self, actor, page, per_page):
        scope_user_id = None if actor.is_staff() else actor.id
        tasks = self.task_repository.list(page, per_page, scope_user_id)
        return [
            task.to_dict(include_related=True, include_overdue=True) for task in tasks
        ]

    def get_task(self, actor, task_id):
        task = self._get_authorized_task(actor, task_id)
        return task.to_dict(include_overdue=True)

    def create_task(self, actor, data):
        user_id = data.get("user_id")
        if not actor.is_staff():
            if user_id not in (None, actor.id):
                raise AuthorizationError("Usuário não pode atribuir tarefa a terceiros")
            user_id = actor.id
        self._validate_relations(user_id, data.get("category_id"))

        task = Task(
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            priority=data.get("priority", 3),
            user_id=user_id,
            category_id=data.get("category_id"),
            due_date=data.get("due_date"),
            tags=data.get("tags"),
        )
        self.task_repository.add(task)
        self._commit()
        return task.to_dict()

    def update_task(self, actor, task_id, data):
        task = self._get_authorized_task(actor, task_id)
        if "user_id" in data:
            if not actor.is_staff() and data["user_id"] != actor.id:
                raise AuthorizationError("Usuário não pode reatribuir a tarefa")
            self._validate_user(data["user_id"])
        if "category_id" in data:
            self._validate_category(data["category_id"])

        for field in (
            "title",
            "description",
            "status",
            "priority",
            "user_id",
            "category_id",
            "due_date",
            "tags",
        ):
            if field in data:
                setattr(task, field, data[field])
        task.updated_at = utc_now()
        self._commit()
        return task.to_dict()

    def delete_task(self, actor, task_id):
        task = self._get_authorized_task(actor, task_id)
        self.task_repository.delete(task)
        self._commit()
        return {"message": "Task deletada com sucesso"}

    def search_tasks(self, actor, filters, page, per_page):
        scope_user_id = None if actor.is_staff() else actor.id
        if not actor.is_staff() and filters.get("user_id") not in (None, actor.id):
            raise AuthorizationError()
        tasks = self.task_repository.search(filters, page, per_page, scope_user_id)
        return [task.to_dict() for task in tasks]

    def task_stats(self, actor):
        scope_user_id = None if actor.is_staff() else actor.id
        return self.task_repository.stats(scope_user_id)

    def _get_authorized_task(self, actor, task_id):
        task = self.task_repository.get(task_id)
        if not task:
            raise NotFoundError("Task não encontrada")
        if not actor.is_staff() and task.user_id != actor.id:
            raise AuthorizationError()
        return task

    def _validate_relations(self, user_id, category_id):
        self._validate_user(user_id)
        self._validate_category(category_id)

    def _validate_user(self, user_id):
        if user_id is not None and not self.user_repository.get(user_id):
            raise NotFoundError("Usuário não encontrado")

    def _validate_category(self, category_id):
        if category_id is not None and not self.category_repository.get(category_id):
            raise NotFoundError("Categoria não encontrada")

    @staticmethod
    def _commit():
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
