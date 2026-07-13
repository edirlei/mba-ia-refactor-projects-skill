import secrets

from werkzeug.security import check_password_hash, generate_password_hash

from errors import AuthenticationError


HASH_PREFIXES = ("scrypt:", "pbkdf2:")


class UserService:
    def __init__(self, user_repository):
        self._user_repository = user_repository

    def create(self, user_data):
        return self._user_repository.create(
            name=user_data["nome"],
            email=user_data["email"],
            password_hash=generate_password_hash(user_data["senha"]),
        )


class AuthService:
    def __init__(self, user_repository):
        self._user_repository = user_repository

    def authenticate(self, email, password):
        user = self._user_repository.find_by_email_for_authentication(email)
        if user is None or not self._password_matches(user.password_hash, password):
            raise AuthenticationError("Email ou senha inválidos")

        if not user.password_hash.startswith(HASH_PREFIXES):
            self._user_repository.update_password_hash(
                user.id,
                generate_password_hash(password),
            )
        return user

    @staticmethod
    def _password_matches(stored_password, candidate_password):
        if not stored_password:
            return False
        if stored_password.startswith(HASH_PREFIXES):
            return check_password_hash(stored_password, candidate_password)
        return secrets.compare_digest(stored_password, candidate_password)
