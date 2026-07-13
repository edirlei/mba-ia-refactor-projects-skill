class User {
    constructor({ id, name, email, pass }) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.passwordHash = pass;
    }

    toPublic() {
        return { id: this.id, name: this.name, email: this.email };
    }
}

module.exports = { User };
