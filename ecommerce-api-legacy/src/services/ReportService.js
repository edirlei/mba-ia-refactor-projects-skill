class ReportService {
    constructor(reportRepository) {
        this.reportRepository = reportRepository;
    }

    async financialReport() {
        const rows = await this.reportRepository.financialRows();
        const courses = new Map();

        for (const row of rows) {
            if (!courses.has(row.course_id)) {
                courses.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: []
                });
            }
            if (row.enrollment_id === null) continue;

            const course = courses.get(row.course_id);
            if (row.payment_status === 'PAID') {
                course.revenue += row.payment_amount;
            }
            course.students.push({
                student: row.student_name || 'Unknown',
                paid: row.payment_amount || 0
            });
        }
        return [...courses.values()];
    }
}

module.exports = { ReportService };
