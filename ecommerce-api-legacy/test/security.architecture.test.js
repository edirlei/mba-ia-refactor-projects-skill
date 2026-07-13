const assert = require('node:assert/strict');
const { existsSync, readFileSync } = require('node:fs');
const path = require('node:path');
const { after, before, test } = require('node:test');

const { createApplication } = require('../src/app');

const ADMIN_TOKEN = 'test-admin-token';
const logEntries = [];
const logger = {
    info(event, context = {}) {
        logEntries.push({ level: 'info', event, context });
    },
    error(event, context = {}) {
        logEntries.push({ level: 'error', event, context });
    }
};

let runtime;
let server;
let baseUrl;

async function request(pathname, options = {}) {
    return fetch(`${baseUrl}${pathname}`, {
        ...options,
        headers: {
            ...(options.body ? { 'content-type': 'application/json' } : {}),
            ...(options.headers || {})
        }
    });
}

before(async () => {
    runtime = await createApplication({
        config: {
            adminToken: ADMIN_TOKEN,
            seedUserPassword: 'seed-password-for-tests',
            databasePath: ':memory:'
        },
        logger
    });
    server = await new Promise((resolve, reject) => {
        const listeningServer = runtime.app.listen(0, '127.0.0.1', () => {
            resolve(listeningServer);
        });
        listeningServer.once('error', reject);
    });
    baseUrl = `http://127.0.0.1:${server.address().port}`;
});

after(async () => {
    if (server) {
        await new Promise((resolve, reject) => {
            server.close(error => (error ? reject(error) : resolve()));
        });
    }
    if (runtime) await runtime.close();
});

test('segurança, transações e fronteiras arquiteturais', async t => {
    await t.test('rotas administrativas exigem token válido', async () => {
        const anonymous = await request('/api/admin/financial-report');
        assert.equal(anonymous.status, 403);

        const invalid = await request('/api/admin/financial-report', {
            headers: { 'x-admin-token': 'invalid-token' }
        });
        assert.equal(invalid.status, 403);

        const authorized = await request('/api/admin/financial-report', {
            headers: { 'x-admin-token': ADMIN_TOKEN }
        });
        assert.equal(authorized.status, 200);
    });

    await t.test('seed usa scrypt e senha não é valor legível', async () => {
        const row = await runtime.database.get('SELECT pass FROM users WHERE id = ?', [1]);
        assert.match(row.pass, /^scrypt\$[a-f0-9]+\$[a-f0-9]+$/);
        assert.notEqual(row.pass, 'seed-password-for-tests');
    });

    await t.test('checkout não registra cartão ou senha', async () => {
        const cardNumber = '4111222233334444';
        const password = 'sensitive-test-password';
        const response = await request('/api/checkout', {
            method: 'POST',
            body: JSON.stringify({
                usr: 'Safe Logger',
                eml: 'safe-logger@example.com',
                pwd: password,
                c_id: 1,
                card: cardNumber
            })
        });
        assert.equal(response.status, 200);
        const serializedLogs = JSON.stringify(logEntries);
        assert.doesNotMatch(serializedLogs, new RegExp(cardNumber));
        assert.doesNotMatch(serializedLogs, new RegExp(password));
    });

    await t.test('falha intermediária reverte usuário, matrícula e pagamento', async () => {
        const service = runtime.services.checkoutService;
        const originalAuditRepository = service.auditRepository;
        const email = 'rollback@example.com';
        service.auditRepository = {
            async record() {
                throw new Error('forced_audit_failure');
            }
        };

        try {
            await assert.rejects(
                service.checkout({
                    userName: 'Rollback User',
                    email,
                    password: 'rollback-password',
                    courseId: 1,
                    cardNumber: '4111111111111111'
                }),
                /forced_audit_failure/
            );
        } finally {
            service.auditRepository = originalAuditRepository;
        }

        const user = await runtime.database.get(
            'SELECT id FROM users WHERE email = ?',
            [email]
        );
        const orphanEnrollments = await runtime.database.get(`
            SELECT COUNT(enrollments.id) AS count
            FROM enrollments
            LEFT JOIN users ON users.id = enrollments.user_id
            WHERE users.id IS NULL
        `);
        assert.equal(user, undefined);
        assert.equal(orphanEnrollments.count, 0);
    });

    await t.test('relatório financeiro executa uma única consulta', async () => {
        const originalAll = runtime.database.all.bind(runtime.database);
        let queryCount = 0;
        runtime.database.all = async (...argumentsList) => {
            queryCount += 1;
            return originalAll(...argumentsList);
        };
        try {
            const report = await runtime.services.reportService.financialReport();
            assert.ok(report.length >= 2);
        } finally {
            runtime.database.all = originalAll;
        }
        assert.equal(queryCount, 1);
    });

    await t.test('exclusão autorizada remove relações sem órfãos', async () => {
        const checkout = await request('/api/checkout', {
            method: 'POST',
            body: JSON.stringify({
                usr: 'Cascade User',
                eml: 'cascade@example.com',
                pwd: 'cascade-password',
                c_id: 2,
                card: '4111111111111111'
            })
        });
        assert.equal(checkout.status, 200);
        const enrollmentId = (await checkout.json()).enrollment_id;
        const user = await runtime.database.get(
            'SELECT id FROM users WHERE email = ?',
            ['cascade@example.com']
        );

        const deleted = await request(`/api/users/${user.id}`, {
            method: 'DELETE',
            headers: { 'x-admin-token': ADMIN_TOKEN }
        });
        assert.equal(deleted.status, 200);

        const enrollment = await runtime.database.get(
            'SELECT id FROM enrollments WHERE id = ?',
            [enrollmentId]
        );
        const payment = await runtime.database.get(
            'SELECT id FROM payments WHERE enrollment_id = ?',
            [enrollmentId]
        );
        assert.equal(enrollment, undefined);
        assert.equal(payment, undefined);
    });

    await t.test('validação e middleware retornam 400 e 404 seguros', async () => {
        const malformed = await fetch(`${baseUrl}/api/checkout`, {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: '{'
        });
        assert.equal(malformed.status, 400);
        assert.equal(await malformed.text(), 'Bad Request');

        const missing = await request('/missing-route');
        assert.equal(missing.status, 404);
        assert.equal(await missing.text(), 'Not Found');
    });

    await t.test('schema possui foreign keys e e-mail único', async () => {
        const enrollmentKeys = await runtime.database.all(
            'PRAGMA foreign_key_list(enrollments)'
        );
        const paymentKeys = await runtime.database.all(
            'PRAGMA foreign_key_list(payments)'
        );
        const userIndexes = await runtime.database.all('PRAGMA index_list(users)');
        assert.equal(enrollmentKeys.length, 2);
        assert.equal(paymentKeys.length, 1);
        assert.ok(userIndexes.some(index => index.unique === 1));
    });

    await t.test('routes, controllers e models respeitam fronteiras', () => {
        const sourceRoot = path.resolve(__dirname, '..', 'src');
        const expectedDirectories = [
            'config',
            'controllers',
            'database',
            'errors',
            'middlewares',
            'models',
            'repositories',
            'routes',
            'schemas',
            'services'
        ];
        for (const directory of expectedDirectories) {
            assert.equal(existsSync(path.join(sourceRoot, directory)), true);
        }
        assert.equal(existsSync(path.join(sourceRoot, 'AppManager.js')), false);
        assert.equal(existsSync(path.join(sourceRoot, 'utils.js')), false);

        for (const routeFile of ['adminRoutes.js', 'checkoutRoutes.js']) {
            const source = readFileSync(path.join(sourceRoot, 'routes', routeFile), 'utf8');
            assert.doesNotMatch(source, /sqlite3|SELECT |INSERT |DELETE FROM/);
        }
        for (const controllerFile of [
            'CheckoutController.js',
            'ReportController.js',
            'UserController.js'
        ]) {
            const source = readFileSync(
                path.join(sourceRoot, 'controllers', controllerFile),
                'utf8'
            );
            assert.doesNotMatch(source, /express|sqlite3|SELECT |INSERT |DELETE FROM/);
        }
        for (const modelFile of ['Course.js', 'Enrollment.js', 'User.js']) {
            const source = readFileSync(path.join(sourceRoot, 'models', modelFile), 'utf8');
            assert.doesNotMatch(source, /express|sqlite3/);
        }
    });
});
