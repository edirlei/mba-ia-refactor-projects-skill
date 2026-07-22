class AuthController:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def login(self, data):
        user, token = self.auth_service.login(data["email"], data["password"])
        return {
            "message": "Login realizado com sucesso",
            "user": user.to_dict(),
            "token": token,
        }
