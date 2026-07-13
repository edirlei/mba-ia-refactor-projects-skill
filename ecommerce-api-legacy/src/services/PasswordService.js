const { randomBytes, scrypt, timingSafeEqual } = require('node:crypto');
const { promisify } = require('node:util');

const scryptAsync = promisify(scrypt);

class PasswordService {
    async hash(password) {
        const salt = randomBytes(16);
        const derivedKey = await scryptAsync(password, salt, 64);
        return `scrypt$${salt.toString('hex')}$${derivedKey.toString('hex')}`;
    }

    async verify(password, encodedHash) {
        const [algorithm, saltHex, hashHex] = String(encodedHash).split('$');
        if (algorithm !== 'scrypt' || !saltHex || !hashHex) return false;
        const expected = Buffer.from(hashHex, 'hex');
        const actual = await scryptAsync(password, Buffer.from(saltHex, 'hex'), expected.length);
        return actual.length === expected.length && timingSafeEqual(actual, expected);
    }
}

module.exports = { PasswordService };
