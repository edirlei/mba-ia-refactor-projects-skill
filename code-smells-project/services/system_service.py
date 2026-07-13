import secrets

from errors import AuthorizationError


class SystemService:
    def __init__(self, system_repository, admin_token):
        self._system_repository = system_repository
        self._admin_token = admin_token

    def health(self):
        return self._system_repository.health_counts()

    def reset_database(self, provided_token):
        if not self._is_authorized(provided_token):
            raise AuthorizationError("Operação administrativa não autorizada")
        self._system_repository.reset()

    @staticmethod
    def reject_arbitrary_query():
        raise AuthorizationError("Execução arbitrária de SQL desabilitada por segurança")

    def _is_authorized(self, provided_token):
        if not self._admin_token or not provided_token:
            return False
        return secrets.compare_digest(self._admin_token, provided_token)
