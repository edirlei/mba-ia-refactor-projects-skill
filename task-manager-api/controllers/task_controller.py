class TaskController:
    def __init__(self, task_service):
        self.task_service = task_service

    def list(self, actor, page, per_page):
        return self.task_service.list_tasks(actor, page, per_page)

    def get(self, actor, task_id):
        return self.task_service.get_task(actor, task_id)

    def create(self, actor, data):
        return self.task_service.create_task(actor, data)

    def update(self, actor, task_id, data):
        return self.task_service.update_task(actor, task_id, data)

    def delete(self, actor, task_id):
        return self.task_service.delete_task(actor, task_id)

    def search(self, actor, filters, page, per_page):
        return self.task_service.search_tasks(actor, filters, page, per_page)

    def stats(self, actor):
        return self.task_service.task_stats(actor)
