class AppError extends Error {
    constructor(message, statusCode = 400, code = 'application_error') {
        super(message);
        this.name = this.constructor.name;
        this.statusCode = statusCode;
        this.code = code;
    }
}

class ValidationError extends AppError {
    constructor(message) {
        super(message, 400, 'validation_error');
    }
}

class AuthorizationError extends AppError {
    constructor(message = 'Forbidden') {
        super(message, 403, 'authorization_error');
    }
}

class NotFoundError extends AppError {
    constructor(message) {
        super(message, 404, 'not_found');
    }
}

class ConflictError extends AppError {
    constructor(message) {
        super(message, 409, 'conflict');
    }
}

module.exports = {
    AppError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError
};
