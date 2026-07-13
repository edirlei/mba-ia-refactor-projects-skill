const { User } = require('../models/User');

class UserRepository {
    constructor(database) {
        this.database = database;
    }

    async findByEmail(email) {
        const row = await this.database.get(
            'SELECT id, name, email, pass FROM users WHERE email = ?',
            [email]
        );
        return row ? new User(row) : null;
    }

    async create({ name, email, passwordHash }) {
        const result = await this.database.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash]
        );
        return new User({ id: result.lastID, name, email, pass: passwordHash });
    }

    async deleteById(userId) {
        return this.database.run('DELETE FROM users WHERE id = ?', [userId]);
    }
}

module.exports = { UserRepository };
