class UserController:
    def __init__(self, user_service):
        self.user_service = user_service

    def list(self, page, per_page):
        return self.user_service.list_users(page, per_page)

    def get(self, actor, user_id, page, per_page):
        return self.user_service.get_user(actor, user_id, page, per_page)

    def create(self, data):
        return self.user_service.create_user(data)

    def update(self, actor, user_id, data):
        return self.user_service.update_user(actor, user_id, data)

    def delete(self, user_id):
        return self.user_service.delete_user(user_id)

    def tasks(self, actor, user_id, page, per_page):
        return self.user_service.list_user_tasks(actor, user_id, page, per_page)
