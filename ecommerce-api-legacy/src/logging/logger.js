function createLogger(output = console) {
    return Object.freeze({
        info(event, context = {}) {
            output.info(JSON.stringify({ level: 'info', event, ...context }));
        },
        error(event, context = {}) {
            output.error(JSON.stringify({ level: 'error', event, ...context }));
        }
    });
}

module.exports = { createLogger };
