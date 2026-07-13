# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

Defina um token administrativo e, opcionalmente, uma senha para o usuário de seed.

```powershell
$env:ADMIN_TOKEN = "defina-um-token-local"
$env:SEED_USER_PASSWORD = "defina-uma-senha-local"
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Para executar a suíte automatizada:

```powershell
npm test
```

Exemplos de requisições estão em `api.http`. As rotas administrativas exigem o header `x-admin-token` com o valor definido em `ADMIN_TOKEN`.
