class ApplicationError(Exception):
    status_code = 500
    default_message = "Erro interno"

    def __init__(self, message=None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class AuthenticationError(ApplicationError):
    status_code = 401
    default_message = "Autenticação necessária"


class AuthorizationError(ApplicationError):
    status_code = 403
    default_message = "Acesso não autorizado"


class NotFoundError(ApplicationError):
    status_code = 404
    default_message = "Recurso não encontrado"


class ConflictError(ApplicationError):
    status_code = 409
    default_message = "Conflito ao processar o recurso"
