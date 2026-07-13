# Playbook de refatoração

## Sumário

1. [Regras de aplicação](#regras-de-aplicação)
2. [Matriz de cobertura](#matriz-de-cobertura)
3. [T01 — Substituir executor genérico e injection](#t01--substituir-executor-genérico-e-injection)
4. [T02 — Extrair segredos e proteger logs](#t02--extrair-segredos-e-proteger-logs)
5. [T03 — Corrigir senha e autenticação](#t03--corrigir-senha-e-autenticação)
6. [T04 — Aplicar autorização por recurso](#t04--aplicar-autorização-por-recurso)
7. [T05 — Dividir God Module em MVC](#t05--dividir-god-module-em-mvc)
8. [T06 — Remover estado global e controlar recursos](#t06--remover-estado-global-e-controlar-recursos)
9. [T07 — Tornar operações atômicas e íntegras](#t07--tornar-operações-atômicas-e-íntegras)
10. [T08 — Eliminar N+1 e paginar](#t08--eliminar-n1-e-paginar)
11. [T09 — Centralizar validação](#t09--centralizar-validação)
12. [T10 — Centralizar erros](#t10--centralizar-erros)
13. [T11 — Migrar APIs e dependências obsoletas](#t11--migrar-apis-e-dependências-obsoletas)
14. [T12 — Consolidar constantes, nomes e logging](#t12--consolidar-constantes-nomes-e-logging)

## Regras de aplicação

- Aplicar uma transformação por vez e executar testes logo depois.
- Preservar endpoints, códigos HTTP e formatos observáveis, salvo correção de segurança explicitamente aprovada.
- Criar testes de caracterização antes de mover lógica sem cobertura.
- Não atualizar dependências junto com uma grande mudança estrutural.
- Não remover código aparentemente morto sem busca de referências e teste.
- Fazer rollback da própria mudança quando a validação falhar e não houver correção segura imediata.

## Matriz de cobertura

| Transformação | Antipadrões cobertos |
|---|---|
| T01 | AP-SEC-01, AP-SEC-02 |
| T02 | AP-SEC-03, AP-QUAL-03 |
| T03 | AP-SEC-04 |
| T04 | AP-SEC-05 |
| T05 | AP-ARC-01, AP-ARC-03 |
| T06 | AP-ARC-02, AP-DATA-01 |
| T07 | AP-DATA-01, AP-DATA-02 |
| T08 | AP-PERF-01 |
| T09 | AP-VAL-01, AP-ARC-03 |
| T10 | AP-ERR-01 |
| T11 | AP-DEP-01 |
| T12 | AP-QUAL-01, AP-QUAL-02, AP-QUAL-03 |

## T01 — Substituir executor genérico e injection

Remover endpoints que recebem consultas/comandos completos. Parametrizar valores em operações necessárias.

**Antes — Python/SQLite**

```python
query = request.json["sql"]
cursor.execute(query)

cursor.execute(
    "SELECT * FROM users WHERE email = '" + email + "'"
)
```

**Depois**

```python
@admin_routes.get("/users/<int:user_id>")
@require_permission("users:read")
def get_user(user_id):
    return user_controller.get_by_id(user_id)

cursor.execute(
    "SELECT id, name, email FROM users WHERE email = ?",
    (email,),
)
```

**Validar:** procurar sinks restantes, testar caracteres especiais e confirmar que não existe rota genérica de SQL/shell.

## T02 — Extrair segredos e proteger logs

Centralizar configuração e nunca registrar valores sensíveis.

**Antes — JavaScript**

```javascript
const gatewayKey = "pk_live_real";
console.log(`Charging ${cardNumber} with ${gatewayKey}`);
```

**Depois**

```javascript
const config = {
  gatewayKey: requireEnv("PAYMENT_GATEWAY_KEY"),
};

logger.info("Processing payment", {
  cardLast4: cardNumber.slice(-4),
});
```

**Validar:** buscar padrões de secret, verificar `.env` ignorado e confirmar que respostas/logs não contêm cartões, tokens ou senhas.

## T03 — Corrigir senha e autenticação

Usar biblioteca específica para senha, serializer seguro e token/sessão verificável.

**Antes — Python**

```python
self.password = hashlib.md5(password.encode()).hexdigest()

def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}

token = "fake-token-" + str(user.id)
```

**Depois**

```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, password):
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    return check_password_hash(self.password_hash, password)

def to_public_dict(self):
    return {"id": self.id, "email": self.email, "role": self.role}

token = token_service.issue(subject=str(user.id), role=user.role)
```

**Validar:** testar senha correta/incorreta, ausência do hash nas respostas, expiração e rejeição de token adulterado.

## T04 — Aplicar autorização por recurso

Não aceitar role privilegiada do cliente e validar ação, principal e recurso.

**Antes — Express**

```javascript
router.delete("/users/:id", (req, res) => userController.remove(req.params.id, res));
router.post("/users", (req, res) => userController.create(req.body, res));
```

**Depois**

```javascript
router.delete(
  "/users/:id",
  authenticate,
  authorize("users:delete"),
  userController.remove,
);

async function createUser(input) {
  return userRepository.create({ ...input, role: "user" });
}
```

**Validar:** testar anônimo, usuário comum, proprietário e administrador; tentar alterar `role` e IDs de terceiros.

## T05 — Dividir God Module em MVC

Extrair por responsabilidade mantendo o endpoint estável.

**Antes — rota com tudo**

```python
@app.post("/orders")
def create_order():
    data = request.get_json()
    # validação, SQL, estoque, pagamento, e-mail e resposta
```

**Depois**

```python
# routes/order_routes.py
@order_bp.post("/orders")
def create_order_route():
    command = order_schema.load(request.get_json())
    result = order_controller.create(command)
    return jsonify(result), 201

# controllers/order_controller.py
class OrderController:
    def __init__(self, checkout_service):
        self.checkout_service = checkout_service

    def create(self, command):
        return self.checkout_service.checkout(command)
```

**Validar:** comparar request/response antes/depois e confirmar que route não importa banco nem integração.

## T06 — Remover estado global e controlar recursos

Substituir conexão/cache global por dependência com ciclo de vida explícito.

**Antes — Python**

```python
db_connection = sqlite3.connect("app.db", check_same_thread=False)

def list_items():
    return db_connection.execute("SELECT * FROM items").fetchall()
```

**Depois**

```python
from flask import g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

**Validar:** executar requisições concorrentes, testes isolados e confirmar fechamento no teardown.

## T07 — Tornar operações atômicas e íntegras

Envolver escritas dependentes em transação e reforçar constraints.

**Antes — JavaScript/SQLite**

```javascript
await db.run("INSERT INTO enrollments ...");
await db.run("INSERT INTO payments ...");
await db.run("INSERT INTO audit_logs ...");
```

**Depois**

```javascript
await db.exec("BEGIN");
try {
  const enrollment = await enrollmentRepository.create(input);
  await paymentRepository.create(enrollment.id, payment);
  await auditRepository.record("checkout", enrollment.id);
  await db.exec("COMMIT");
  return enrollment;
} catch (error) {
  await db.exec("ROLLBACK");
  throw error;
}
```

Migration complementar:

```sql
CREATE UNIQUE INDEX ux_users_email ON users(email);
-- Adicionar foreign keys e política de exclusão compatíveis com o banco.
```

**Validar:** forçar falha em cada etapa e confirmar ausência de gravação parcial ou órfãos.

## T08 — Eliminar N+1 e paginar

Carregar relações em lote e limitar listagens.

**Antes — SQLAlchemy**

```python
tasks = Task.query.all()
for task in tasks:
    task.user_name = User.query.get(task.user_id).name
```

**Depois**

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

statement = (
    select(Task)
    .options(selectinload(Task.user), selectinload(Task.category))
    .limit(page_size)
    .offset((page - 1) * page_size)
)
tasks = db.session.scalars(statement).all()
```

**Validar:** contar consultas, testar páginas vazias/limites e comparar ordenação e payload.

## T09 — Centralizar validação

Definir schema único reutilizado por create/update.

**Antes**

```python
if not data.get("title"):
    return {"error": "required"}, 400
if data.get("status") not in ["pending", "done"]:
    return {"error": "invalid"}, 400
```

**Depois**

```python
class TaskSchema(Schema):
    title = fields.String(required=True, validate=Length(min=3, max=200))
    status = fields.String(validate=OneOf(["pending", "in_progress", "done", "cancelled"]))
    priority = fields.Integer(validate=Range(min=1, max=5))

command = TaskSchema().load(request.get_json() or {})
```

**Validar:** executar tabela de casos com ausente, nulo, tipo errado, limite e valor válido.

## T10 — Centralizar erros

Transformar erros de domínio em respostas HTTP num único boundary.

**Antes — Express**

```javascript
db.get(sql, params, (err, row) => {
  if (err) return res.status(500).send(err.message);
  // callbacks seguintes também tratam erro
});
```

**Depois**

```javascript
router.get("/items/:id", asyncHandler(itemController.get));

app.use((error, req, res, next) => {
  logger.error("request_failed", { error: error.name, requestId: req.id });
  const mapped = mapApplicationError(error);
  res.status(mapped.status).json({ error: mapped.code, message: mapped.safeMessage });
});
```

**Validar:** testar not-found, validação, conflito e falha inesperada; não expor stack/driver ao cliente.

## T11 — Migrar APIs e dependências obsoletas

Migrar uma API por vez, seguindo documentação da versão instalada.

**Antes — SQLAlchemy/Python**

```python
user = User.query.get(user_id)
created_at = datetime.utcnow()
```

**Depois**

```python
from datetime import UTC, datetime

user = db.session.get(User, user_id)
created_at = datetime.now(UTC)
```

Para pacote transitivo deprecated:

1. identificar a dependência direta que o introduz;
2. consultar changelog e compatibilidade;
3. atualizar somente a dependência direta necessária;
4. regenerar lockfile com o gerenciador correto;
5. executar boot, testes e auditoria novamente.

**Validar:** ausência do warning, lockfile consistente e nenhuma mudança de contrato.

## T12 — Consolidar constantes, nomes e logging

Aplicar limpeza mecânica depois das mudanças funcionais.

**Antes**

```javascript
let u = req.body.usr;
if (s === "P") console.log("ok");
```

**Depois**

```javascript
const userName = request.body.userName;
const ORDER_STATUS = Object.freeze({ PENDING: "pending" });

if (status === ORDER_STATUS.PENDING) {
  logger.info("order_pending", { orderId });
}
```

**Validar:** executar lint/testes, buscar imports mortos e confirmar que logs não carregam dados sensíveis.
