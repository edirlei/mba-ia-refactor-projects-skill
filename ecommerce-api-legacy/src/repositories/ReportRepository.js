class ReportRepository {
    constructor(database) {
        this.database = database;
    }

    financialRows() {
        return this.database.all(`
            SELECT
                courses.id AS course_id,
                courses.title AS course_title,
                enrollments.id AS enrollment_id,
                users.name AS student_name,
                payments.amount AS payment_amount,
                payments.status AS payment_status
            FROM courses
            LEFT JOIN enrollments ON enrollments.course_id = courses.id
            LEFT JOIN users ON users.id = enrollments.user_id
            LEFT JOIN payments ON payments.enrollment_id = enrollments.id
            ORDER BY courses.id, enrollments.id
        `);
    }
}

module.exports = { ReportRepository };
