# Relatório de auditoria arquitetural — Projeto 1

## 1. Identificação

| Campo | Valor |
|---|---|
| Projeto analisado | `code-smells-project` |
| Data da análise | 11/07/2026 |
| Fases executadas | Fase 1 — Análise; Fase 2 — Relatório e plano; Fase 3 — Refatoração e validação |
| Status da Fase 3 | Concluída após autorização explícita do usuário |
| Stack identificada | Python 3, Flask 3.1.1, Flask-CORS 5.0.1 e SQLite |
| Arquivos-fonte analisados | `app.py`, `controllers.py`, `models.py`, `database.py` |
| Volume analisado | 4 arquivos, 780 linhas de código-fonte |
| Ponto de entrada | `app.py` |
| Confiança da análise | Alta |

## 2. Resumo executivo

O projeto implementa uma API de loja virtual com produtos, usuários, pedidos e relatório de vendas. A organização nominal separa rotas, controladores, modelos e banco, mas as responsabilidades permanecem fortemente acopladas e há acessos ao banco fora da camada de dados.

Foram identificados **14 achados**: **4 críticos**, **3 altos**, **5 médios** e **2 baixos**. Os maiores riscos são execução remota de SQL, injeção de SQL, armazenamento e exposição de credenciais e segredos, ausência de autenticação em operações administrativas e fragilidade transacional no fluxo de pedidos.

Na conclusão das Fases 1 e 2, nenhuma alteração de código havia sido realizada. A Fase 3 começou somente após autorização explícita do usuário; seus resultados estão registrados na seção 12.

## 3. Inventário arquitetural

### 3.1 Componentes e responsabilidades atuais

| Componente | Responsabilidade observada | Observação |
|---|---|---|
| `app.py` | Configuração Flask, registro de rotas e endpoints administrativos | Também executa SQL e operações destrutivas diretamente |
| `controllers.py` | HTTP, validação parcial, regras de fluxo e respostas JSON | Também acessa banco e simula notificações |
| `models.py` | Consultas SQL, serialização, regras de negócio e transações | Módulo central com responsabilidades excessivas |
| `database.py` | Conexão global, criação do esquema e carga inicial | Mistura infraestrutura, migração e seed |

### 3.2 Fluxo principal observado

```text
Cliente HTTP
    -> app.py (rotas)
        -> controllers.py (HTTP + validação + orquestração)
            -> models.py (SQL + regras + serialização)
                -> database.py (conexão SQLite global)

Exceções ao fluxo:
app.py -> database.py       (/admin/reset-db e /admin/query)
controllers.py -> database.py  (/health)
```

### 3.3 Superfície funcional

- 19 endpoints HTTP: produtos, usuários, login, pedidos, relatório, saúde e administração.
- 4 tabelas: `produtos`, `usuarios`, `pedidos` e `itens_pedido`.
- Não foi localizada suíte automatizada de testes no projeto analisado.

## 4. Visão consolidada dos achados

| ID | Severidade | Achado | Local principal | Catálogo |
|---|---|---|---|---|
| AP-001 | CRÍTICO | Endpoint permite executar SQL arbitrário | `app.py:59` | AP-SEC-01 |
| AP-002 | CRÍTICO | SQL construído por concatenação de entradas | `models.py:28` | AP-SEC-02 |
| AP-003 | CRÍTICO | Senhas em texto puro e retornadas pela API | `database.py:27` | AP-SEC-03, AP-SEC-04 |
| AP-004 | CRÍTICO | Segredo e modo debug expostos | `app.py:7` | AP-SEC-03 |
| AP-005 | ALTO | Reset destrutivo do banco sem autenticação | `app.py:47` | AP-SEC-05 |
| AP-006 | ALTO | Módulos concentradores e violação de SRP/MVC | `models.py:4` | AP-ARC-01, AP-ARC-03 |
| AP-007 | ALTO | Conexão global e transação de pedido frágil | `database.py:4` | AP-ARC-02, AP-DATA-01 |
| AP-008 | MÉDIO | Consultas N+1 na listagem de pedidos | `models.py:171` | AP-PERF-01 |
| AP-009 | MÉDIO | Esquema sem restrições essenciais de integridade | `database.py:14` | AP-DATA-02 |
| AP-010 | MÉDIO | Validação inconsistente e erros internos expostos | `controllers.py:5` | AP-VAL-01, AP-ERR-01 |
| AP-011 | MÉDIO | Camadas ignoradas por acessos diretos ao banco | `app.py:47` | AP-ARC-03 |
| AP-012 | MÉDIO | Listagens sem paginação e consultas amplas | `models.py:4` | AP-PERF-01 |
| AP-013 | BAIXO | Constantes de negócio e execução espalhadas | `controllers.py:52` | AP-QUAL-01 |
| AP-014 | BAIXO | Higiene de código e observabilidade deficientes | `database.py:2` | AP-QUAL-02, AP-QUAL-03 |

## 5. Detalhamento dos achados

### AP-001 — Endpoint permite executar SQL arbitrário

- **Severidade:** CRÍTICO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-01
- **Evidência:** `app.py`, linhas 59–78.
- **Descrição:** o endpoint `POST /admin/query` recebe a propriedade `sql` do corpo da requisição e a entrega diretamente a `cursor.execute`. Aceita leitura e escrita e não exige autenticação ou autorização.
- **Impacto:** leitura, alteração ou exclusão integral do banco; comprometimento de confidencialidade, integridade e disponibilidade.
- **Recomendação:** remover o endpoint da superfície pública. Se houver necessidade operacional real, substituí-lo por operações administrativas fechadas, autenticadas, autorizadas e auditáveis.

### AP-002 — SQL construído por concatenação de entradas

- **Severidade:** CRÍTICO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-02
- **Evidência:** `models.py`, linhas 24–68, 89–129, 133–169, 171–233 e 275–299.
- **Descrição:** consultas, inclusões, atualizações e exclusões são montadas por concatenação de identificadores, textos, credenciais, filtros e valores numéricos.
- **Impacto:** injeção de SQL, alteração indevida de registros, vazamento de dados e erros de sintaxe com entradas legítimas contendo aspas.
- **Recomendação:** usar parâmetros posicionais do SQLite em todas as consultas e validar tipos e limites antes de acessar a camada de persistência.

### AP-003 — Senhas em texto puro e retornadas pela API

- **Severidade:** CRÍTICO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-03, AP-SEC-04
- **Evidência:** `database.py`, linhas 27–33 e 75–82; `models.py`, linhas 72–103 e 105–129.
- **Descrição:** o esquema e a carga inicial armazenam senhas sem hash; listagens e consultas de usuários incluem o campo de senha; a autenticação compara credenciais diretamente no SQL.
- **Impacto:** comprometimento imediato das contas em caso de vazamento e exposição desnecessária de credenciais em respostas HTTP.
- **Recomendação:** armazenar somente hashes com algoritmo apropriado, nunca serializar o campo de senha e separar o modelo público do registro persistido.

### AP-004 — Segredo e modo debug expostos

- **Severidade:** CRÍTICO
- **Categoria:** Segurança e configuração
- **Catálogo:** AP-SEC-03
- **Evidência:** `app.py`, linhas 7–9 e 80–88; `controllers.py`, linhas 264–292.
- **Descrição:** a chave secreta está fixa no fonte, o modo debug é ativado no código e o endpoint de saúde devolve informações internas, inclusive o segredo. O valor do segredo foi deliberadamente omitido deste relatório.
- **Impacto:** vazamento de segredo, aumento da superfície de ataque e exposição de detalhes operacionais.
- **Recomendação:** carregar configuração por ambiente, falhar com segurança quando o segredo estiver ausente, desativar debug fora do desenvolvimento e reduzir o health check a dados não sensíveis.

### AP-005 — Reset destrutivo do banco sem autenticação

- **Severidade:** ALTO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-05
- **Evidência:** `app.py`, linhas 47–57.
- **Descrição:** `POST /admin/reset-db` remove os dados das quatro tabelas sem verificar identidade, papel ou ambiente.
- **Impacto:** perda total de dados por qualquer cliente com acesso à API.
- **Recomendação:** remover o endpoint da aplicação; se indispensável em desenvolvimento, isolá-lo por ambiente e exigir autenticação e autorização explícitas.

### AP-006 — Módulos concentradores e violação de SRP/MVC

- **Severidade:** ALTO
- **Categoria:** Arquitetura
- **Catálogo:** AP-ARC-01, AP-ARC-03
- **Evidência:** `models.py`, linhas 4–314; `controllers.py`, linhas 5–292; `app.py`, linhas 47–78.
- **Descrição:** `models.py` reúne acesso a dados, regras de estoque e desconto, transação, autenticação e serialização. `controllers.py` reúne HTTP, validação, orquestração e efeitos de notificação. `app.py` contém lógica administrativa de persistência.
- **Impacto:** mudanças com alto raio de impacto, baixa testabilidade e maior risco de regressão.
- **Recomendação:** separar por domínio e por responsabilidade: rotas/controladores, serviços de aplicação, repositórios e modelos de resposta.

### AP-007 — Conexão global e transação de pedido frágil

- **Severidade:** ALTO
- **Categoria:** Arquitetura e dados
- **Catálogo:** AP-ARC-02, AP-DATA-01
- **Evidência:** `database.py`, linhas 4–11; `models.py`, linhas 133–169.
- **Descrição:** uma conexão SQLite global é compartilhada com `check_same_thread=False`. O pedido consulta itens, cria cabeçalho, cria detalhes e reduz estoque sem bloco transacional explícito, rollback ou tratamento de concorrência.
- **Impacto:** estado inconsistente, estoque incorreto, conexão compartilhada entre requisições e dificuldade de recuperação em falhas intermediárias.
- **Recomendação:** usar conexão por requisição/unidade de trabalho, transação explícita com rollback e atualização de estoque protegida por condição de disponibilidade.

### AP-008 — Consultas N+1 na listagem de pedidos

- **Severidade:** MÉDIO
- **Categoria:** Performance
- **Catálogo:** AP-PERF-01
- **Evidência:** `models.py`, linhas 171–233.
- **Descrição:** para cada pedido é feita uma consulta de itens e, para cada item, outra consulta do produto. O padrão aparece nas listagens geral e por usuário.
- **Impacto:** quantidade de consultas cresce proporcionalmente a pedidos e itens, elevando latência e carga do banco.
- **Recomendação:** obter pedidos, itens e produtos com `JOIN` ou consultas em lote e agrupar o resultado em memória.

### AP-009 — Esquema sem restrições essenciais de integridade

- **Severidade:** MÉDIO
- **Categoria:** Dados
- **Catálogo:** AP-DATA-02
- **Evidência:** `database.py`, linhas 14–53.
- **Descrição:** campos essenciais aceitam `NULL`; e-mail não é único; não há chaves estrangeiras; preço, estoque, quantidade, total e status não possuem restrições de domínio.
- **Impacto:** registros órfãos, duplicados e valores inválidos podem ser persistidos mesmo que a API tente validar parte das entradas.
- **Recomendação:** adicionar `NOT NULL`, `UNIQUE`, `FOREIGN KEY` e `CHECK` por migrações graduais, após saneamento dos dados existentes.

### AP-010 — Validação inconsistente e erros internos expostos

- **Severidade:** MÉDIO
- **Categoria:** Validação e tratamento de erros
- **Catálogo:** AP-VAL-01, AP-ERR-01
- **Evidência:** `controllers.py`, linhas 5–22, 24–96, 111–126, 146–220 e 237–292; `app.py`, linhas 59–78.
- **Descrição:** vários endpoints assumem JSON em formato esperado, validações se repetem ou ficam incompletas e exceções são devolvidas ao cliente por `str(e)`.
- **Impacto:** respostas 500 para erros de cliente, contratos inconsistentes e vazamento de detalhes internos.
- **Recomendação:** centralizar validação e mapeamento de erros, definir schema por entrada e devolver mensagens públicas estáveis com correlação para logs internos.

### AP-011 — Camadas ignoradas por acessos diretos ao banco

- **Severidade:** MÉDIO
- **Categoria:** Arquitetura
- **Catálogo:** AP-ARC-03
- **Evidência:** `app.py`, linhas 47–78; `controllers.py`, linhas 264–292.
- **Descrição:** endpoints administrativos e de saúde acessam `database.py` diretamente, contornando a camada de persistência nominal.
- **Impacto:** regras de acesso e tratamento de falhas ficam duplicadas e a arquitetura não possui um sentido estável de dependências.
- **Recomendação:** manter rotas finas, colocar casos de uso em serviços e encapsular SQL em repositórios/health adapters.

### AP-012 — Listagens sem paginação e consultas amplas

- **Severidade:** MÉDIO
- **Categoria:** Performance
- **Catálogo:** AP-PERF-01
- **Evidência:** `models.py`, linhas 4–22, 72–87, 203–233 e 285–314.
- **Descrição:** listagens usam `SELECT *`, carregam todos os registros e materializam toda a resposta; a busca não limita quantidade nem define paginação.
- **Impacto:** consumo de memória e latência crescentes, além de transferência desnecessária de colunas sensíveis no caso de usuários.
- **Recomendação:** selecionar apenas colunas necessárias e adotar paginação com limite máximo e ordenação determinística.

### AP-013 — Constantes de negócio e execução espalhadas

- **Severidade:** BAIXO
- **Categoria:** Qualidade
- **Catálogo:** AP-QUAL-01
- **Evidência:** `controllers.py`, linhas 41, 52–54 e 237–250; `models.py`, linhas 247–262; `app.py`, linha 88.
- **Descrição:** categorias, status, faixas de desconto, host e porta aparecem como literais em funções distintas.
- **Impacto:** regras divergentes e alterações repetitivas em múltiplos pontos.
- **Recomendação:** consolidar regras de domínio em tipos/constantes apropriados e configuração de execução fora do fonte.

### AP-014 — Higiene de código e observabilidade deficientes

- **Severidade:** BAIXO
- **Categoria:** Qualidade
- **Catálogo:** AP-QUAL-02, AP-QUAL-03
- **Evidência:** `database.py`, linha 2; `models.py`, linha 2; `controllers.py`, linhas 8–12, 56–62, 160–165 e 208–220.
- **Descrição:** existem imports não utilizados, parâmetros e variáveis chamados `id`, espaços e linhas supérfluos e uso de `print` para eventos e erros.
- **Impacto:** ruído de manutenção, logs sem estrutura e investigação operacional mais difícil.
- **Recomendação:** remover código morto, evitar sombrear nomes internos e usar logging estruturado sem dados sensíveis.

## 6. Cobertura do catálogo de antipadrões

| Código | Antipadrão verificado | Resultado | Achado relacionado |
|---|---|---|---|
| AP-SEC-01 | Execução arbitrária de comandos/consultas | Encontrado | AP-001 |
| AP-SEC-02 | Injeção por concatenação | Encontrado | AP-002 |
| AP-SEC-03 | Segredos ou credenciais expostos | Encontrado | AP-003, AP-004 |
| AP-SEC-04 | Armazenamento inseguro de senha | Encontrado | AP-003 |
| AP-ARC-01 | God Object/Module | Encontrado | AP-006 |
| AP-SEC-05 | Operação sensível sem autorização | Encontrado | AP-005 |
| AP-ARC-02 | Estado/conexão global mutável | Encontrado | AP-007 |
| AP-DATA-01 | Transação sem atomicidade clara | Encontrado | AP-007 |
| AP-PERF-01 | N+1 ou acesso excessivo a dados | Encontrado | AP-008, AP-012 |
| AP-VAL-01 | Validação ausente ou inconsistente | Encontrado | AP-010 |
| AP-ERR-01 | Tratamento genérico/exposição de erros | Encontrado | AP-010 |
| AP-DATA-02 | Integridade não garantida no banco | Encontrado | AP-009 |
| AP-DEP-01 | API ou dependência obsoleta | Verificado; não evidenciado | — |
| AP-ARC-03 | Violação de fronteira entre camadas | Encontrado | AP-006, AP-011 |
| AP-QUAL-01 | Magic numbers/strings | Encontrado | AP-013 |
| AP-QUAL-02 | Código morto ou nomes problemáticos | Encontrado | AP-014 |
| AP-QUAL-03 | Observabilidade inadequada | Encontrado | AP-014 |

## 7. Plano de refatoração proposto

> Este plano é somente uma proposta da Fase 2. Nenhum item foi executado.

### Onda 0 — Preservar comportamento observável

1. Criar testes de caracterização para os 19 endpoints e registrar os contratos atuais.
2. Criar banco temporário por teste e impedir que testes usem `loja.db` de desenvolvimento.
3. Registrar explicitamente comportamentos inseguros que devem ser removidos, sem tratá-los como contratos a preservar.

### Onda 1 — Conter riscos críticos

1. Remover ou isolar `/admin/query` e `/admin/reset-db`.
2. Externalizar configuração, retirar segredos das respostas e desativar debug por padrão.
3. Parametrizar todas as consultas SQL.
4. Introduzir hash de senha e excluir senha de qualquer representação pública.

### Onda 2 — Estabilizar persistência e transações

1. Implementar conexão por requisição/unidade de trabalho.
2. Encapsular o caso de uso de criação de pedido em transação atômica com rollback.
3. Adicionar restrições e migrações de integridade de modo compatível com dados existentes.
4. Eliminar N+1 e introduzir paginação.

### Onda 3 — Separar responsabilidades

1. Organizar módulos por domínio: produtos, usuários, pedidos e relatórios.
2. Manter controladores responsáveis apenas por HTTP e delegar casos de uso a serviços.
3. Encapsular persistência em repositórios e respostas em mapeadores/DTOs.
4. Centralizar validação, erros e logging.

### Onda 4 — Limpeza e endurecimento

1. Consolidar constantes e regras de domínio.
2. Remover imports/código morto e corrigir nomes.
3. Executar testes de regressão, segurança e performance comparativa.
4. Atualizar documentação da arquitetura resultante.

## 8. Contratos que precisam ser protegidos

| Contrato | Proteção recomendada antes da mudança |
|---|---|
| Métodos, caminhos e códigos HTTP dos endpoints legítimos | Testes de caracterização por endpoint |
| Formato das respostas de produtos, pedidos e relatórios | Asserções de schema e campos |
| Cálculo de total, desconto e ticket médio | Testes unitários de regras e limites |
| Atualização de estoque ao criar pedido | Testes transacionais de sucesso e falha |
| Busca por termo, categoria e faixa de preço | Casos parametrizados com entradas válidas e adversariais |
| Autenticação e representação pública de usuário | Testes de segurança garantindo ausência de senha |

Não devem ser preservados como contrato: execução arbitrária de SQL, reset público, exposição de segredo, senhas em texto puro, detalhes internos de exceção e dependência de debug ativo.

## 9. Critérios sugeridos para validar uma futura Fase 3

- Todos os testes de caracterização aprovados ou mudanças de contrato justificadas.
- Nenhum endpoint aceita SQL arbitrário ou operação administrativa sem autorização.
- Zero consulta construída por concatenação de entrada externa.
- Nenhuma senha ou segredo armazenado, registrado ou retornado em texto puro.
- Criação de pedido é atômica e reverte integralmente em falha.
- Restrições de integridade cobrem relações e domínios essenciais.
- Listagens usam paginação e consultas de pedidos não apresentam N+1.
- Rotas/controladores não acessam SQLite diretamente.
- Erros públicos não incluem detalhes internos; logs são estruturados.

## 10. Limitações da análise

- As Fases 1 e 2 foram estáticas e restritas aos arquivos do projeto `code-smells-project` e às referências da Skill.
- O banco existente não foi alterado nem usado para validar qualidade dos dados históricos.
- Nenhuma dependência adicional foi instalada.
- A Fase 3 criou uma suíte automatizada e executou validações dinâmicas em banco temporário; o banco local `loja.db` não foi usado nos testes.

## 11. Confirmação obrigatória antes da Fase 3 — registro histórico

**Fases 1 e 2 concluídas. Nenhum código da aplicação foi modificado. Deseja autorizar explicitamente a Fase 3 — Refatoração? Sem uma resposta afirmativa, nenhuma refatoração deve ser iniciada.**

A autorização afirmativa foi recebida antes da primeira alteração da Fase 3. A pergunta acima foi preservada como evidência da barreira humana prevista na Skill.

## 12. Resultado da Fase 3

### 12.1 Resumo da transformação

A aplicação foi reorganizada para uma arquitetura MVC adaptada a APIs Flask. O ponto de entrada passou a atuar como composition root, as rotas foram convertidas em Blueprints finos, controladores coordenam os casos de uso, serviços concentram regras multi-entidade, repositórios encapsulam SQL parametrizado e models expõem somente representações seguras.

```text
app.py                         # application factory e composição
config.py                      # configuração por ambiente
database.py                    # conexão por contexto, schema e seed
errors.py                      # tradução central de erros
controllers/                   # coordenação dos casos de uso
models/                        # entidades e serialização segura
repositories/                  # persistência e consultas SQL
routes/                        # Views/Routes HTTP com Blueprints
schemas/                       # validação central de entrada
services/                      # autenticação, pedidos, relatórios e administração
tests/                         # caracterização, segurança e arquitetura
```

Os antigos módulos concentradores `controllers.py` e `models.py` foram substituídos pelas respectivas estruturas em diretórios.

### 12.2 Tratamento dos achados

| Achado | Resultado da Fase 3 |
|---|---|
| AP-001 | Resolvido: `/admin/query` permanece identificável, mas rejeita qualquer SQL com `403`. |
| AP-002 | Resolvido: valores externos usam placeholders; busca dinâmica concatena somente cláusulas internas fixas. |
| AP-003 | Resolvido: novos usuários e seeds usam hash; serializers não expõem senha; login atualiza registros legados após autenticação válida. |
| AP-004 | Resolvido: segredo, debug, host, porta e CORS vêm da configuração; health check não expõe segredo ou caminho do banco. |
| AP-005 | Resolvido: reset exige `X-Admin-Token` configurado no ambiente e usa comparação segura. |
| AP-006 | Resolvido: responsabilidades separadas em routes, controllers, models, services e repositories. |
| AP-007 | Resolvido: conexão por contexto Flask, teardown e transação explícita com rollback na criação de pedidos. |
| AP-008 | Resolvido: pedidos, itens e produtos são carregados por uma consulta com JOIN. |
| AP-009 | Parcial: novos bancos possuem `NOT NULL`, `UNIQUE`, `CHECK`, foreign keys e índices; um `loja.db` legado exige migração explícita para receber constraints estruturais. |
| AP-010 | Resolvido: schemas centralizam validação e handlers não devolvem mensagens do SQLite ou stack trace. |
| AP-011 | Resolvido: routes e controllers não acessam SQLite diretamente. |
| AP-012 | Resolvido: listagens têm paginação com limite máximo de 100 e seleção explícita de colunas. |
| AP-013 | Resolvido: categorias e status foram centralizados; descontos ficaram em um único serviço. |
| AP-014 | Resolvido: imports legados e `print` foram removidos; logging estruturado registra apenas identificadores operacionais. |

### 12.3 Testes automatizados

Comando executado:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: **9 testes aprovados**, cobrindo:

- inventário e contratos dos 19 endpoints;
- hash e ausência de senha nas respostas;
- neutralização de entrada de SQL Injection;
- rollback de cabeçalho, itens e estoque após falha intermediária;
- listagem de pedidos em uma consulta;
- foreign keys em bancos novos;
- conflito de e-mail e erros públicos seguros;
- bloqueio de SQL arbitrário e proteção do reset;
- fronteiras entre routes, controllers, models e persistência.

A compilação estática também foi validada:

```powershell
.\.venv\Scripts\python.exe -m compileall -q app.py config.py database.py errors.py controllers models repositories routes schemas services tests
```

### 12.4 Boot e validação HTTP real

A aplicação foi iniciada em `127.0.0.1:5089` com SQLite temporário, debug desativado e configuração de teste. O processo foi encerrado e os arquivos temporários removidos após a validação.

| Endpoint | Status |
|---|---:|
| `GET /` | 200 |
| `GET /produtos` | 200 |
| `GET /produtos/busca` | 200 |
| `GET /produtos/1` | 200 |
| `POST /produtos` | 201 |
| `PUT /produtos/1` | 200 |
| `DELETE /produtos/<id>` | 200 |
| `GET /usuarios` | 200 |
| `GET /usuarios/1` | 200 |
| `POST /usuarios` | 201 |
| `POST /login` | 200 |
| `POST /pedidos` | 201 |
| `GET /pedidos` | 200 |
| `GET /pedidos/usuario/1` | 200 |
| `PUT /pedidos/<id>/status` | 200 |
| `GET /relatorios/vendas` | 200 |
| `GET /health` | 200 |
| `POST /admin/query` | 403 — bloqueado por segurança |
| `POST /admin/reset-db` sem token | 403 — bloqueado por segurança |

Resultado: **19/19 endpoints originais responderam**, com mudanças de segurança justificadas para as duas operações administrativas.

### 12.5 Checklist de validação

#### Fase 1 — Análise

- [x] Linguagem detectada corretamente.
- [x] Framework detectado corretamente.
- [x] Domínio da aplicação descrito corretamente.
- [x] Número de arquivos analisados condizente com a linha de base.

#### Fase 2 — Auditoria

- [x] Relatório segue o template da Skill.
- [x] Cada finding registra arquivo e linhas.
- [x] Findings ordenados de CRÍTICO a BAIXO.
- [x] Mais de cinco findings identificados.
- [x] APIs deprecated verificadas e ausência registrada.
- [x] Skill pausou e pediu confirmação antes da Fase 3.

#### Fase 3 — Refatoração

- [x] Estrutura de diretórios segue o padrão MVC adaptado à API.
- [x] Configuração extraída para módulo próprio, sem segredo hardcoded.
- [x] Models criados para representar e serializar dados com segurança.
- [x] Views/Routes separadas em Blueprints.
- [x] Controllers concentram o fluxo da aplicação.
- [x] Tratamento de erros centralizado.
- [x] Entry point claro com application factory.
- [x] Aplicação inicia sem erros.
- [x] Todos os endpoints originais respondem.

### 12.6 Riscos remanescentes

- Criar uma migração explícita para aplicar constraints aos bancos `loja.db` já existentes; `CREATE TABLE IF NOT EXISTS` protege bancos novos, mas não altera tabelas legadas.
- Substituir o token administrativo simples por autenticação e autorização completas caso as rotas administrativas sejam mantidas em um ambiente real.
- Ampliar testes concorrentes de estoque se a aplicação evoluir de SQLite para um banco multiusuário de produção.
