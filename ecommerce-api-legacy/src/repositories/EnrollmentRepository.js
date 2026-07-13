const { Enrollment } = require('../models/Enrollment');

class EnrollmentRepository {
    constructor(database) {
        this.database = database;
    }

    async create(userId, courseId) {
        const result = await this.database.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId]
        );
        return new Enrollment({ id: result.lastID, userId, courseId });
    }
}

module.exports = { EnrollmentRepository };
