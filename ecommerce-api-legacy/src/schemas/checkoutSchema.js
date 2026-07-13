const { ValidationError } = require('../errors/AppError');

function requireNonEmptyString(value, message) {
    if (typeof value !== 'string' || value.trim().length === 0) {
        throw new ValidationError(message);
    }
    return value.trim();
}

function parseCheckout(body) {
    if (!body || typeof body !== 'object' || Array.isArray(body)) {
        throw new ValidationError('Bad Request');
    }

    const userName = requireNonEmptyString(body.usr, 'Bad Request');
    const email = requireNonEmptyString(body.eml, 'Bad Request').toLowerCase();
    const cardNumber = requireNonEmptyString(body.card, 'Bad Request');
    const courseId = Number(body.c_id);
    const password = body.pwd;

    if (!/^\S+@\S+\.\S+$/.test(email)) {
        throw new ValidationError('Email inválido');
    }
    if (!Number.isInteger(courseId) || courseId <= 0) {
        throw new ValidationError('Curso inválido');
    }
    if (!/^\d{12,19}$/.test(cardNumber)) {
        throw new ValidationError('Cartão inválido');
    }
    if (password !== undefined && (typeof password !== 'string' || password.length < 8)) {
        throw new ValidationError('Senha deve ter pelo menos 8 caracteres');
    }

    return { userName, email, password, courseId, cardNumber };
}

module.exports = { parseCheckout };
