# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Análise Manual

Esta seção registra a análise estática manual dos três projetos fornecidos. Cada achado foi classificado conforme a escala de severidade do desafio e contém uma localização verificável no código. Nesta etapa, as aplicações ainda não foram executadas; os resultados abaixo formam a linha de base que será usada para avaliar a capacidade de detecção da Skill.

### Resumo dos achados

| Projeto | CRÍTICO | ALTO | MÉDIO | BAIXO | Total |
|---|---:|---:|---:|---:|---:|
| `code-smells-project` | 4 | 3 | 3 | 2 | 12 |
| `ecommerce-api-legacy` | 3 | 4 | 5 | 2 | 14 |
| `task-manager-api` | 3 | 2 | 7 | 2 | 14 |
| **Total** | **10** | **9** | **15** | **6** | **40** |

Todos os projetos superam o mínimo individual de cinco problemas e contêm, no mínimo, um achado CRÍTICO ou ALTO, dois MÉDIOS e dois BAIXOS.

### Projeto 1 — `code-smells-project`

Stack identificada: Python, Flask 3.1.1, Flask-CORS e SQLite. O projeto é uma API de e-commerce com 19 endpoints e quatro tabelas. A arquitetura possui uma separação apenas nominal entre `app.py`, `controllers.py`, `models.py` e `database.py`, pois regras de negócio, acesso a dados, serialização e operações administrativas continuam misturados.

| Severidade | Problema e localização | Por que é relevante |
|---|---|---|
| **CRÍTICO** | Execução arbitrária de SQL em [`app.py:59-76`](code-smells-project/app.py#L59-L76) | O endpoint `/admin/query` executa diretamente uma string SQL recebida na requisição, sem autenticação. Um cliente pode ler, alterar ou excluir qualquer dado e até remover a estrutura do banco. |
| **CRÍTICO** | SQL Injection generalizada em [`models.py:47-60`](code-smells-project/models.py#L47-L60), [`models.py:105-129`](code-smells-project/models.py#L105-L129) e [`models.py:285-299`](code-smells-project/models.py#L285-L299) | Dados de produtos, credenciais e filtros são concatenados em SQL. Isso permite modificar a consulta, burlar autenticação e acessar ou corromper dados. |
| **CRÍTICO** | Senhas armazenadas e devolvidas em texto puro em [`database.py:27-33`](code-smells-project/database.py#L27-L33), [`database.py:75-82`](code-smells-project/database.py#L75-L82) e [`models.py:72-129`](code-smells-project/models.py#L72-L129) | As senhas são gravadas sem hash e aparecem nas respostas de listagem e consulta de usuários. Um acesso à API ou ao banco expõe credenciais diretamente reutilizáveis. |
| **CRÍTICO** | Chave secreta e debug expostos em [`app.py:7-9`](code-smells-project/app.py#L7-L9), [`app.py:88`](code-smells-project/app.py#L88) e [`controllers.py:285-290`](code-smells-project/controllers.py#L285-L290) | A chave é literal, o debug permanece habilitado e o endpoint `/health` devolve a própria chave. Isso expõe configuração sensível e amplia a superfície de ataque. |
| **ALTO** | Reset completo do banco sem autenticação em [`app.py:47-57`](code-smells-project/app.py#L47-L57) | Qualquer cliente pode chamar `/admin/reset-db` e apagar pedidos, itens, produtos e usuários. |
| **ALTO** | God Modules e violação de MVC/SRP em [`models.py:4-314`](code-smells-project/models.py#L4-L314), [`controllers.py:5-292`](code-smells-project/controllers.py#L5-L292) e [`app.py:47-78`](code-smells-project/app.py#L47-L78) | Os módulos misturam múltiplos domínios, SQL, regras, serialização, validação, notificações e administração. Isso gera forte acoplamento e dificulta testes isolados. |
| **ALTO** | Gerenciamento inseguro de conexão e transações em [`database.py:4-10`](code-smells-project/database.py#L4-L10) e [`models.py:133-169`](code-smells-project/models.py#L133-L169) | Uma única conexão global é compartilhada com a proteção de thread desabilitada. A criação de pedidos executa várias escritas sem rollback explícito, permitindo estado parcial após falhas. |
| **MÉDIO** | Consultas N+1 em [`models.py:171-233`](code-smells-project/models.py#L171-L233) | Para cada pedido são consultados os itens e, para cada item, o produto. A quantidade de consultas cresce rapidamente com o volume de dados. |
| **MÉDIO** | Banco sem restrições de integridade em [`database.py:14-53`](code-smells-project/database.py#L14-L53) | Faltam chaves estrangeiras, unicidade de e-mail e restrições de nulidade, permitindo registros órfãos e estados inválidos. |
| **MÉDIO** | Validação e tratamento de erros inconsistentes em [`controllers.py:5-22`](code-smells-project/controllers.py#L5-L22), [`controllers.py:167-220`](code-smells-project/controllers.py#L167-L220) e [`controllers.py:237-292`](code-smells-project/controllers.py#L237-L292) | Exceções genéricas são devolvidas com detalhes internos e alguns handlers acessam JSON sem validar sua existência ou os tipos recebidos. |
| **BAIXO** | Valores mágicos e regras espalhadas em [`controllers.py:52-54`](code-smells-project/controllers.py#L52-L54), [`controllers.py:242`](code-smells-project/controllers.py#L242) e [`models.py:256-262`](code-smells-project/models.py#L256-L262) | Categorias, status e faixas de desconto estão codificados em vários pontos, elevando o risco de alterações inconsistentes. |
| **BAIXO** | Higiene e nomenclatura em [`database.py:2`](code-smells-project/database.py#L2), [`models.py:2`](code-smells-project/models.py#L2) e [`controllers.py:14`](code-smells-project/controllers.py#L14) | Há imports não utilizados, parâmetros chamados `id` que ocultam o built-in do Python e logging feito com `print`, reduzindo legibilidade e observabilidade. |

Não foi identificada uma API claramente obsoleta no código-fonte deste projeto. A ausência desse achado é intencional: a auditoria não deve fabricar problemas apenas para atingir uma quantidade mínima.

### Projeto 2 — `ecommerce-api-legacy`

Stack identificada: JavaScript, Node.js, Express 4.18.2 e SQLite em memória. Apesar do nome do diretório, o domínio é uma API de LMS com checkout, cursos, matrículas e pagamentos. A classe `AppManager` concentra inicialização, rotas, persistência, pagamento, relatórios e exclusões.

| Severidade | Problema e localização | Por que é relevante |
|---|---|---|
| **CRÍTICO** | Credenciais e chaves hardcoded em [`utils.js:1-6`](ecommerce-api-legacy/src/utils.js#L1-L6) | Usuário e senha de banco, chave de gateway e usuário SMTP estão no código. Isso expõe segredos e impede a separação segura entre ambientes. |
| **CRÍTICO** | Cartão completo e chave do gateway registrados em log em [`AppManager.js:43-46`](ecommerce-api-legacy/src/AppManager.js#L43-L46) | Dados financeiros e credenciais podem ser armazenados em logs, observabilidade e backups, ampliando o impacto de qualquer vazamento. |
| **CRÍTICO** | Função de senha insegura e senha padrão em [`utils.js:17-22`](ecommerce-api-legacy/src/utils.js#L17-L22) e [`AppManager.js:66-69`](ecommerce-api-legacy/src/AppManager.js#L66-L69) | A função repete Base64, trunca o resultado e usa `123456` quando a senha não é informada. Base64 não é um hash adequado para senhas. |
| **ALTO** | God Class em [`AppManager.js:4-138`](ecommerce-api-legacy/src/AppManager.js#L4-L138) | A classe cria e popula o banco, registra rotas, processa checkout, pagamento, usuários, auditoria e relatórios. A concentração viola MVC/SRP e impede testes isolados. |
| **ALTO** | Rotas administrativas sem autenticação em [`AppManager.js:80-137`](ecommerce-api-legacy/src/AppManager.js#L80-L137) | Qualquer cliente pode consultar dados financeiros e excluir usuários, expondo informações e permitindo operações destrutivas. |
| **ALTO** | Checkout sem transação atômica em [`AppManager.js:50-61`](ecommerce-api-legacy/src/AppManager.js#L50-L61) | Matrícula, pagamento e auditoria são gravados sequencialmente sem rollback. Uma falha intermediária deixa o banco inconsistente. |
| **ALTO** | Estado global mutável em [`utils.js:9-15`](ecommerce-api-legacy/src/utils.js#L9-L15) | Cache e receita global são compartilhados entre requisições, dificultando isolamento, testes e controle de memória. |
| **MÉDIO** | Consultas N+1 no relatório em [`AppManager.js:83-127`](ecommerce-api-legacy/src/AppManager.js#L83-L127) | Cada curso consulta matrículas e cada matrícula consulta usuário e pagamento, fazendo o custo crescer com a base. |
| **MÉDIO** | Erros de callbacks ignorados em [`AppManager.js:57-61`](ecommerce-api-legacy/src/AppManager.js#L57-L61), [`AppManager.js:92-126`](ecommerce-api-legacy/src/AppManager.js#L92-L126) e [`AppManager.js:131-136`](ecommerce-api-legacy/src/AppManager.js#L131-L136) | Diversos callbacks recebem `err`, mas continuam a execução. Isso pode causar exceções, respostas penduradas e respostas de sucesso após falhas. |
| **MÉDIO** | Banco sem integridade referencial em [`AppManager.js:12-16`](ecommerce-api-legacy/src/AppManager.js#L12-L16) e [`AppManager.js:131-136`](ecommerce-api-legacy/src/AppManager.js#L131-L136) | Não existem foreign keys ou unicidade de e-mail, e a exclusão de usuário deixa matrículas e pagamentos órfãos. |
| **MÉDIO** | Dependências transitivas obsoletas em [`package-lock.json:33-38`](ecommerce-api-legacy/package-lock.json#L33-L38), [`package-lock.json:827-832`](ecommerce-api-legacy/package-lock.json#L827-L832), [`package-lock.json:1074-1079`](ecommerce-api-legacy/package-lock.json#L1074-L1079) e [`package-lock.json:2113-2118`](ecommerce-api-legacy/package-lock.json#L2113-L2118) | O lockfile registra nove pacotes transitivos como deprecated, incluindo `glob`, `inflight`, `rimraf` e `tar`. A cadeia precisa ser revisada sem atualizações cegas. |
| **MÉDIO** | Validação e pagamento superficiais em [`AppManager.js:28-48`](ecommerce-api-legacy/src/AppManager.js#L28-L48) | Senha, e-mail, IDs e cartão não são devidamente validados. O pagamento é decidido apenas pelo primeiro dígito do cartão e está acoplado à rota. |
| **BAIXO** | Nomes abreviados em [`AppManager.js:28-35`](ecommerce-api-legacy/src/AppManager.js#L28-L35) | Variáveis como `u`, `e`, `p`, `cid` e `cc` escondem a intenção e tornam o fluxo mais difícil de revisar. |
| **BAIXO** | Código morto e valores mágicos em [`AppManager.js:2`](ecommerce-api-legacy/src/AppManager.js#L2) e [`utils.js:6-22`](ecommerce-api-legacy/src/utils.js#L6-L22) | `totalRevenue` não é utilizado e valores como `10000`, `10`, `3000` e o prefixo `4` aparecem sem abstração ou explicação. |

As consultas que recebem dados externos utilizam placeholders `?`; portanto, não foi registrado um achado de SQL Injection neste projeto.

### Projeto 3 — `task-manager-api`

Stack identificada: Python, Flask 3.0.0, Flask-SQLAlchemy 3.1.1 e SQLite. O projeto possui Blueprints, models e uma separação parcial em `routes`, `services` e `utils`, mas os arquivos de rotas ainda concentram regras, persistência e serialização.

| Severidade | Problema e localização | Por que é relevante |
|---|---|---|
| **CRÍTICO** | Autenticação fictícia e elevação de privilégio em [`user_routes.py:42-86`](task-manager-api/routes/user_routes.py#L42-L86) e [`user_routes.py:185-210`](task-manager-api/routes/user_routes.py#L185-L210) | O cliente pode se cadastrar como `admin`, e o login retorna um token previsível que não é assinado nem validado pelas rotas. |
| **CRÍTICO** | MD5 para senhas e hash exposto nas respostas em [`user.py:16-32`](task-manager-api/models/user.py#L16-L32), [`user_routes.py:27-40`](task-manager-api/routes/user_routes.py#L27-L40) e [`user_routes.py:207-210`](task-manager-api/routes/user_routes.py#L207-L210) | MD5 sem salt é inadequado para senhas, e `to_dict()` inclui o hash em respostas de consulta, criação, atualização e login. |
| **CRÍTICO** | Segredos e credenciais hardcoded em [`app.py:11-15`](task-manager-api/app.py#L11-L15), [`app.py:33-34`](task-manager-api/app.py#L33-L34) e [`notification_service.py:7-10`](task-manager-api/services/notification_service.py#L7-L10) | A chave Flask e as credenciais SMTP estão no fonte, enquanto o servidor inicia com debug habilitado. |
| **ALTO** | Ausência de autorização e isolamento entre usuários em [`user_routes.py:92-151`](task-manager-api/routes/user_routes.py#L92-L151), [`task_routes.py:156-238`](task-manager-api/routes/task_routes.py#L156-L238) e [`report_routes.py:12-155`](task-manager-api/routes/report_routes.py#L12-L155) | Qualquer cliente pode alterar usuários e roles, editar ou excluir tarefas e consultar relatórios de terceiros. |
| **ALTO** | Rotas atuando como God Controllers em [`task_routes.py:1-299`](task-manager-api/routes/task_routes.py#L1-L299), [`report_routes.py:1-223`](task-manager-api/routes/report_routes.py#L1-L223) e [`user_routes.py:1-211`](task-manager-api/routes/user_routes.py#L1-L211) | As rotas acumulam HTTP, validação, regras, acesso ao ORM, transações, cálculos e serialização. A estrutura em pastas não completa a separação MVC. |
| **MÉDIO** | Consultas N+1 em [`task_routes.py:14-57`](task-manager-api/routes/task_routes.py#L14-L57), [`report_routes.py:53-68`](task-manager-api/routes/report_routes.py#L53-L68) e [`report_routes.py:157-165`](task-manager-api/routes/report_routes.py#L157-L165) | Cada tarefa busca usuário e categoria, cada usuário busca suas tarefas e cada categoria executa uma contagem separada. |
| **MÉDIO** | Listagens sem paginação em [`task_routes.py:11-14`](task-manager-api/routes/task_routes.py#L11-L14), [`user_routes.py:10-12`](task-manager-api/routes/user_routes.py#L10-L12) e [`report_routes.py:30`](task-manager-api/routes/report_routes.py#L30) | As consultas carregam todos os registros na memória, degradando latência e consumo conforme a base cresce. |
| **MÉDIO** | Exceções genéricas e silenciosas em [`task_routes.py:61-63`](task-manager-api/routes/task_routes.py#L61-L63), [`task_routes.py:225-238`](task-manager-api/routes/task_routes.py#L225-L238) e [`helpers.py:43-50`](task-manager-api/utils/helpers.py#L43-L50) | Blocos `except:` escondem tanto erros esperados quanto falhas de programação, prejudicando diagnóstico e observabilidade. |
| **MÉDIO** | Validação duplicada e helpers não utilizados em [`helpers.py:57-116`](task-manager-api/utils/helpers.py#L57-L116), [`task_routes.py:85-223`](task-manager-api/routes/task_routes.py#L85-L223) e [`user_routes.py:42-78`](task-manager-api/routes/user_routes.py#L42-L78) | Helpers e constantes já existem, mas as rotas reimplementam as mesmas regras. O Marshmallow está declarado, porém não é utilizado. |
| **MÉDIO** | Parâmetros inválidos podem gerar erro 500 em [`task_routes.py:240-271`](task-manager-api/routes/task_routes.py#L240-L271) e [`report_routes.py:190-209`](task-manager-api/routes/report_routes.py#L190-L209) | Conversões para inteiro e acesso a JSON ocorrem sem tratamento, transformando erros do cliente em falhas internas. |
| **MÉDIO** | APIs legadas/depreciadas em [`task_routes.py:67`](task-manager-api/routes/task_routes.py#L67), [`user_routes.py:29`](task-manager-api/routes/user_routes.py#L29), [`task.py:15-16`](task-manager-api/models/task.py#L15-L16) e [`report_routes.py:35-45`](task-manager-api/routes/report_routes.py#L35-L45) | `Query.get()` é legado no SQLAlchemy 2.x, e `datetime.utcnow()` está depreciado desde Python 3.12. O uso dificulta evolução para APIs atuais e datas conscientes de timezone. |
| **MÉDIO** | Criação do banco como efeito colateral de importação em [`app.py:30-31`](task-manager-api/app.py#L30-L31) | `db.create_all()` roda sempre que `app.py` é importado, dificultando testes, configuração de bancos alternativos e adoção de migrations. |
| **BAIXO** | Valores e regras mágicas duplicadas em [`task.py:38-48`](task-manager-api/models/task.py#L38-L48), [`task_routes.py:102-114`](task-manager-api/routes/task_routes.py#L102-L114), [`user_routes.py:64-72`](task-manager-api/routes/user_routes.py#L64-L72) e [`helpers.py:110-116`](task-manager-api/utils/helpers.py#L110-L116) | Status, roles, limites de senha, prioridades e cores aparecem tanto em constantes quanto em literais, permitindo divergências. |
| **BAIXO** | Imports, métodos e serviços não utilizados em [`app.py:7`](task-manager-api/app.py#L7), [`task_routes.py:7`](task-manager-api/routes/task_routes.py#L7), [`helpers.py:1-7`](task-manager-api/utils/helpers.py#L1-L7) e [`notification_service.py:1-48`](task-manager-api/services/notification_service.py#L1-L48) | Há imports e helpers não consumidos; o serviço de notificação não está integrado às rotas, gerando ruído e falsa expectativa de funcionalidade. |

Não foi identificada SQL Injection evidente neste projeto, pois o acesso ao banco é realizado pelo ORM. Como pontos positivos, o projeto já utiliza Blueprints, models separados, foreign keys em `Task`, e-mail único e rollback em vários handlers de escrita. A refatoração deverá preservar esses avanços e melhorar a separação existente, não reconstruir o sistema sem necessidade.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.
