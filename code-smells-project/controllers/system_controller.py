class SystemController:
    def __init__(self, system_service):
        self._system_service = system_service

    def health(self):
        return self._system_service.health()

    def reset_database(self, admin_token):
        self._system_service.reset_database(admin_token)

    def reject_arbitrary_query(self):
        self._system_service.reject_arbitrary_query()
