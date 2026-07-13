const { AppError } = require('../errors/AppError');

function createErrorHandler(logger) {
    return function errorHandler(error, request, response, _next) {
        if (error && error.type === 'entity.parse.failed') {
            return response.status(400).send('Bad Request');
        }
        if (error instanceof AppError) {
            return response.status(error.statusCode).send(error.message);
        }

        logger.error('request_failed', {
            method: request.method,
            path: request.path,
            errorType: error.name || 'Error'
        });
        return response.status(500).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
