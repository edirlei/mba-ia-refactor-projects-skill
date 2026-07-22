from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from errors import AuthenticationError


class AuthService:
    TOKEN_SALT = "task-manager-auth"

    def __init__(self, user_repository, secret_key, max_age_seconds):
        self.user_repository = user_repository
        self.serializer = URLSafeTimedSerializer(secret_key, salt=self.TOKEN_SALT)
        self.max_age_seconds = max_age_seconds

    def login(self, email, password):
        user = self.user_repository.find_by_email(email)
        if not user or not user.check_password(password):
            raise AuthenticationError("Credenciais inválidas")
        if not user.active:
            raise AuthenticationError("Usuário inativo")
        return user, self.serializer.dumps({"sub": user.id})

    def resolve_token(self, token):
        try:
            payload = self.serializer.loads(token, max_age=self.max_age_seconds)
            user_id = int(payload["sub"])
        except SignatureExpired as error:
            raise AuthenticationError("Token expirado") from error
        except (BadSignature, KeyError, TypeError, ValueError) as error:
            raise AuthenticationError("Token inválido") from error

        user = self.user_repository.get(user_id)
        if not user or not user.active:
            raise AuthenticationError("Token inválido")
        return user
