from errors import NotFoundError


class UserController:
    def __init__(self, user_repository, user_service, auth_service):
        self._user_repository = user_repository
        self._user_service = user_service
        self._auth_service = auth_service

    def list_all(self, *, limit, offset):
        return [
            user.to_public_dict()
            for user in self._user_repository.list_all(limit=limit, offset=offset)
        ]

    def get_by_id(self, user_id):
        user = self._user_repository.find_by_id(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return user.to_public_dict()

    def create(self, user_data):
        return self._user_service.create(user_data)

    def login(self, credentials):
        user = self._auth_service.authenticate(
            credentials["email"],
            credentials["senha"],
        )
        return user.to_login_dict()
