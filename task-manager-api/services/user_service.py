from sqlalchemy.exc import IntegrityError

from database import db
from errors import AuthorizationError, ConflictError, NotFoundError
from models.user import User


class UserService:
    def __init__(self, user_repository, task_repository):
        self.user_repository = user_repository
        self.task_repository = task_repository

    def list_users(self, page, per_page):
        rows = self.user_repository.list_with_task_counts(page, per_page)
        result = []
        for user, task_count in rows:
            data = user.to_dict()
            data["task_count"] = int(task_count)
            result.append(data)
        return result

    def get_user(self, actor, user_id, page, per_page):
        user = self._get_user(user_id)
        self._require_self_or_staff(actor, user)
        data = user.to_dict()
        tasks = self.task_repository.list_for_user(user_id, page, per_page)
        data["tasks"] = [task.to_dict() for task in tasks]
        return data

    def create_user(self, data):
        if data.get("role", "user") != "user":
            raise AuthorizationError("Cadastro público não permite papel privilegiado")
        if self.user_repository.find_by_email(data["email"]):
            raise ConflictError("Email já cadastrado")

        user = User(name=data["name"], email=data["email"], role="user")
        user.set_password(data["password"])
        self.user_repository.add(user)
        self._commit("Erro ao criar usuário")
        return user.to_dict()

    def update_user(self, actor, user_id, data):
        user = self._get_user(user_id)
        self._require_self_or_staff(actor, user)
        if "role" in data and not actor.is_admin():
            raise AuthorizationError("Somente administradores podem alterar papéis")
        if "active" in data and not actor.is_admin():
            raise AuthorizationError("Somente administradores podem alterar o status")

        if "email" in data:
            existing = self.user_repository.find_by_email(data["email"])
            if existing and existing.id != user.id:
                raise ConflictError("Email já cadastrado")
            user.email = data["email"]
        if "name" in data:
            user.name = data["name"]
        if "password" in data:
            user.set_password(data["password"])
        if "role" in data:
            user.role = data["role"]
        if "active" in data:
            user.active = data["active"]

        self._commit("Erro ao atualizar usuário")
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get_user(user_id)
        self.user_repository.delete_with_tasks(user)
        self._commit("Erro ao deletar usuário")
        return {"message": "Usuário deletado com sucesso"}

    def list_user_tasks(self, actor, user_id, page, per_page):
        user = self._get_user(user_id)
        self._require_self_or_staff(actor, user)
        tasks = self.task_repository.list_for_user(user_id, page, per_page)
        return [task.to_dict(include_overdue=True) for task in tasks]

    def _get_user(self, user_id):
        user = self.user_repository.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")
        return user

    @staticmethod
    def _require_self_or_staff(actor, user):
        if not actor.is_staff() and actor.id != user.id:
            raise AuthorizationError()

    @staticmethod
    def _commit(message):
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ConflictError(message) from error
        except Exception:
            db.session.rollback()
            raise
