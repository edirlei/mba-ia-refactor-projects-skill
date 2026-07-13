class ReportController:
    def __init__(self, report_service):
        self._report_service = report_service

    def sales_report(self):
        return self._report_service.sales_report()
