const { timingSafeEqual } = require('node:crypto');

const { AuthorizationError } = require('../errors/AppError');

function safeTokenEquals(expected, received) {
    if (!expected || !received) return false;
    const expectedBuffer = Buffer.from(expected);
    const receivedBuffer = Buffer.from(received);
    if (expectedBuffer.length !== receivedBuffer.length) return false;
    return timingSafeEqual(expectedBuffer, receivedBuffer);
}

function createRequireAdmin(adminToken) {
    return function requireAdmin(request, _response, next) {
        const receivedToken = request.get('x-admin-token');
        if (!safeTokenEquals(adminToken, receivedToken)) {
            return next(new AuthorizationError());
        }
        return next();
    };
}

module.exports = { createRequireAdmin };
