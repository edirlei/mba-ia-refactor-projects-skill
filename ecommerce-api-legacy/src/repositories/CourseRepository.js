const { Course } = require('../models/Course');

class CourseRepository {
    constructor(database) {
        this.database = database;
    }

    async findActiveById(courseId) {
        const row = await this.database.get(
            'SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1',
            [courseId]
        );
        return row ? new Course(row) : null;
    }
}

module.exports = { CourseRepository };
