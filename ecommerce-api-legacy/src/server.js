const { createApplication } = require('./app');

async function startServer() {
    const runtime = await createApplication();
    const server = runtime.app.listen(runtime.config.port, () => {
        console.info(`LMS API rodando na porta ${runtime.config.port}.`);
    });

    async function shutdown() {
        server.close(async () => {
            await runtime.close();
            process.exitCode = 0;
        });
    }

    process.once('SIGINT', shutdown);
    process.once('SIGTERM', shutdown);
    return { ...runtime, server };
}

if (require.main === module) {
    startServer().catch(error => {
        console.error(`Falha ao iniciar aplicação: ${error.name}`);
        process.exitCode = 1;
    });
}

module.exports = { startServer };
