"""Popula explicitamente o banco com dados iniciais de desenvolvimento."""
import os
from datetime import timedelta

from app import create_app
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.time import utc_now


def seed_data():
    app = create_app()
    with app.app_context():
        db.create_all()
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        passwords = _load_seed_passwords()
        users = [
            User(name="João Silva", email="joao@email.com", role="admin"),
            User(name="Maria Santos", email="maria@email.com", role="user"),
            User(name="Pedro Oliveira", email="pedro@email.com", role="manager"),
        ]
        for user, password in zip(users, passwords.values()):
            user.set_password(password)
        db.session.add_all(users)

        categories = [
            Category(name="Backend", description="Tarefas de backend", color="#3498db"),
            Category(name="Frontend", description="Tarefas de frontend", color="#2ecc71"),
            Category(name="DevOps", description="Tarefas de infraestrutura", color="#e74c3c"),
            Category(name="Bug", description="Correção de bugs", color="#e67e22"),
        ]
        db.session.add_all(categories)
        db.session.flush()

        task_rows = [
            ("Implementar autenticação", "pending", 1, 0, 0, -3, None),
            ("Criar tela de login", "in_progress", 2, 1, 1, 5, None),
            ("Configurar CI/CD", "done", 2, 2, 2, None, "devops,ci,github"),
            ("Corrigir filtro de busca", "pending", 1, 0, 3, -1, None),
            ("Adicionar paginação", "pending", 3, 0, 0, 10, None),
            ("Escrever testes unitários", "pending", 2, 1, 0, None, None),
            ("Documentar API", "cancelled", 4, 2, 0, None, None),
            ("Refatorar models", "in_progress", 3, 1, 0, None, "refactor,tech-debt"),
            ("Configurar monitoramento", "pending", 4, 2, 2, 20, None),
            ("Melhorar validações", "pending", 3, 0, 0, None, "improvement,validation"),
        ]
        for title, status, priority, user_index, category_index, due_days, tags in task_rows:
            due_date = utc_now() + timedelta(days=due_days) if due_days is not None else None
            db.session.add(
                Task(
                    title=title,
                    description=f"Dados de exemplo para {title.lower()}",
                    status=status,
                    priority=priority,
                    user_id=users[user_index].id,
                    category_id=categories[category_index].id,
                    due_date=due_date,
                    tags=tags,
                )
            )
        db.session.commit()

        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")


def _load_seed_passwords():
    mapping = {
        "admin": "SEED_ADMIN_PASSWORD",
        "user": "SEED_USER_PASSWORD",
        "manager": "SEED_MANAGER_PASSWORD",
    }
    passwords = {role: os.getenv(variable, "") for role, variable in mapping.items()}
    missing = [mapping[role] for role, value in passwords.items() if len(value) < 12]
    if missing:
        raise RuntimeError(
            "Defina senhas de seed com pelo menos 12 caracteres: " + ", ".join(missing)
        )
    return passwords


if __name__ == "__main__":
    seed_data()
