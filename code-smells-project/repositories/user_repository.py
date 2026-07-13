import sqlite3

from errors import ConflictError
from models import User


PUBLIC_USER_COLUMNS = "id, nome, email, tipo, criado_em"


class UserRepository:
    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    def list_all(self, *, limit, offset):
        rows = self._connection_provider().execute(
            f"""
            SELECT {PUBLIC_USER_COLUMNS}
            FROM usuarios
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [User.from_public_row(row) for row in rows]

    def find_by_id(self, user_id):
        row = self._connection_provider().execute(
            f"SELECT {PUBLIC_USER_COLUMNS} FROM usuarios WHERE id = ?",
            (user_id,),
        ).fetchone()
        return User.from_public_row(row) if row else None

    def find_by_email_for_authentication(self, email):
        row = self._connection_provider().execute(
            f"""
            SELECT {PUBLIC_USER_COLUMNS}, senha
            FROM usuarios
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
        return User.from_auth_row(row) if row else None

    def create(self, *, name, email, password_hash, user_type="cliente"):
        connection = self._connection_provider()
        try:
            cursor = connection.execute(
                """
                INSERT INTO usuarios (nome, email, senha, tipo)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, password_hash, user_type),
            )
            connection.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            connection.rollback()
            raise ConflictError("Email já cadastrado") from error

    def update_password_hash(self, user_id, password_hash):
        connection = self._connection_provider()
        connection.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (password_hash, user_id),
        )
        connection.commit()
