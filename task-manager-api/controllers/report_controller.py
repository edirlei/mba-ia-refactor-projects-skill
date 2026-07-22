class ReportController:
    def __init__(self, report_service):
        self.report_service = report_service

    def summary(self):
        return self.report_service.summary()

    def user(self, actor, user_id):
        return self.report_service.user_report(actor, user_id)
