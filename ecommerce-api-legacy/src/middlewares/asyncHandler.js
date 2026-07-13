function asyncHandler(handler) {
    return function handledRoute(request, response, next) {
        Promise.resolve(handler(request, response, next)).catch(next);
    };
}

module.exports = { asyncHandler };
