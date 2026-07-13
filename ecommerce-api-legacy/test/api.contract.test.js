const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { existsSync } = require('node:fs');
const { after, before, test } = require('node:test');

const BASE_URL = 'http://127.0.0.1:3000';
const ADMIN_HEADERS = { 'x-admin-token': 'test-admin-token' };

let server;
let serverErrors = '';

async function request(path, options = {}) {
    return fetch(`${BASE_URL}${path}`, {
        ...options,
        headers: {
            ...(options.body ? { 'content-type': 'application/json' } : {}),
            ...(options.headers || {})
        }
    });
}

async function waitForServer() {
    for (let attempt = 0; attempt < 40; attempt += 1) {
        if (server.exitCode !== null) {
            throw new Error(`Servidor encerrou no boot: ${serverErrors}`);
        }
        try {
            const response = await request('/api/admin/financial-report', {
                headers: ADMIN_HEADERS
            });
            if (response.status === 200) return;
        } catch {
            // O processo ainda está iniciando.
        }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error(`Servidor não iniciou no tempo esperado: ${serverErrors}`);
}

before(async () => {
    const entryPoint = existsSync('src/server.js') ? 'src/server.js' : 'src/app.js';
    server = spawn(process.execPath, [entryPoint], {
        cwd: process.cwd(),
        env: {
            ...process.env,
            ADMIN_TOKEN: 'test-admin-token',
            PORT: '3000'
        },
        stdio: ['ignore', 'ignore', 'pipe'],
        windowsHide: true
    });
    server.stderr.on('data', chunk => {
        serverErrors += chunk.toString();
    });
    await waitForServer();
});

after(async () => {
    if (server && server.exitCode === null) {
        server.kill();
        await new Promise(resolve => server.once('exit', resolve));
    }
});

test('os três endpoints preservam quatro cenários observáveis', async t => {
    await t.test('relatório financeiro retorna uma lista', async () => {
        const response = await request('/api/admin/financial-report', {
            headers: ADMIN_HEADERS
        });
        assert.equal(response.status, 200);
        const report = await response.json();
        assert.ok(Array.isArray(report));
        assert.ok(report.length >= 2);
        assert.deepEqual(
            Object.keys(report[0]).sort(),
            ['course', 'revenue', 'students']
        );
    });

    await t.test('checkout recusado mantém status e mensagem', async () => {
        const response = await request('/api/checkout', {
            method: 'POST',
            body: JSON.stringify({
                usr: 'Cliente Recusado',
                eml: 'recusado@example.com',
                pwd: 'senha-recusa-123',
                c_id: 1,
                card: '5111111111111111'
            })
        });
        assert.equal(response.status, 400);
        assert.equal(await response.text(), 'Pagamento recusado');
    });

    await t.test('checkout aprovado mantém o contrato JSON', async () => {
        const response = await request('/api/checkout', {
            method: 'POST',
            body: JSON.stringify({
                usr: 'Cliente Aprovado',
                eml: 'aprovado@example.com',
                pwd: 'senha-aprovada-123',
                c_id: 2,
                card: '4111111111111111'
            })
        });
        assert.equal(response.status, 200);
        const result = await response.json();
        assert.equal(result.msg, 'Sucesso');
        assert.ok(Number.isInteger(result.enrollment_id));
    });

    await t.test('exclusão de usuário mantém o endpoint e texto', async () => {
        const response = await request('/api/users/1', {
            method: 'DELETE',
            headers: ADMIN_HEADERS
        });
        assert.equal(response.status, 200);
        assert.match(await response.text(), /Usuário deletado/);
    });
});
