const sqlite3 = require('sqlite3');

class DatabaseConnection {
    constructor(database) {
        this.database = database;
    }

    static open(filename) {
        return new Promise((resolve, reject) => {
            const database = new sqlite3.Database(filename, error => {
                if (error) return reject(error);
                return resolve(new DatabaseConnection(database));
            });
        });
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.database.exec(sql, error => {
                if (error) return reject(error);
                return resolve();
            });
        });
    }

    run(sql, parameters = []) {
        return new Promise((resolve, reject) => {
            this.database.run(sql, parameters, function onRun(error) {
                if (error) return reject(error);
                return resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, parameters = []) {
        return new Promise((resolve, reject) => {
            this.database.get(sql, parameters, (error, row) => {
                if (error) return reject(error);
                return resolve(row);
            });
        });
    }

    all(sql, parameters = []) {
        return new Promise((resolve, reject) => {
            this.database.all(sql, parameters, (error, rows) => {
                if (error) return reject(error);
                return resolve(rows);
            });
        });
    }

    close() {
        return new Promise((resolve, reject) => {
            this.database.close(error => {
                if (error) return reject(error);
                return resolve();
            });
        });
    }
}

module.exports = { DatabaseConnection };
