const SCHEMA = `
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pass TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL UNIQUE,
    amount REAL NOT NULL CHECK (amount >= 0),
    status TEXT NOT NULL CHECK (status IN ('PAID', 'DENIED')),
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_enrollments_course_id ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS ix_enrollments_user_id ON enrollments(user_id);
`;

async function initializeDatabase(database, passwordService, seedPassword) {
    await database.exec(SCHEMA);
    const existing = await database.get('SELECT COUNT(id) AS count FROM courses');
    if (existing.count > 0) return;

    const passwordHash = await passwordService.hash(seedPassword);
    await database.exec('BEGIN IMMEDIATE');
    try {
        const user = await database.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Seed User', 'seed@example.invalid', passwordHash]
        );
        const firstCourse = await database.run(
            'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
            ['Clean Architecture', 997, 1]
        );
        await database.run(
            'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
            ['Docker', 497, 1]
        );
        const enrollment = await database.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [user.lastID, firstCourse.lastID]
        );
        await database.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollment.lastID, 997, 'PAID']
        );
        await database.exec('COMMIT');
    } catch (error) {
        await database.exec('ROLLBACK');
        throw error;
    }
}

module.exports = { initializeDatabase };
