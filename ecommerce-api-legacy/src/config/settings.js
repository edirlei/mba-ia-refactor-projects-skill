const { randomBytes } = require('node:crypto');

function parsePort(value) {
    const port = Number.parseInt(value, 10);
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
        throw new Error('PORT deve ser um inteiro entre 1 e 65535');
    }
    return port;
}

function loadConfig(overrides = {}) {
    return Object.freeze({
        port: overrides.port ?? parsePort(process.env.PORT || '3000'),
        databasePath: overrides.databasePath ?? process.env.DATABASE_PATH ?? ':memory:',
        adminToken: overrides.adminToken ?? process.env.ADMIN_TOKEN ?? null,
        approvedCardPrefix:
            overrides.approvedCardPrefix ?? process.env.PAYMENT_APPROVED_PREFIX ?? '4',
        seedUserPassword:
            overrides.seedUserPassword ??
            process.env.SEED_USER_PASSWORD ??
            randomBytes(24).toString('base64url')
    });
}

module.exports = { loadConfig };
