class Course {
    constructor({ id, title, price, active }) {
        this.id = id;
        this.title = title;
        this.price = price;
        this.active = Boolean(active);
    }
}

module.exports = { Course };
