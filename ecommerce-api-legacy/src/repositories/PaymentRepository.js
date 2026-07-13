class PaymentRepository {
    constructor(database) {
        this.database = database;
    }

    create(enrollmentId, amount, status) {
        return this.database.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]
        );
    }
}

module.exports = { PaymentRepository };
