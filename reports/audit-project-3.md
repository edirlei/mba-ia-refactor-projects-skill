# Relatório de auditoria arquitetural — Projeto 3

## 1. Identificação

| Campo | Valor |
|---|---|
| Projeto analisado | `task-manager-api` |
| Data da análise | 12/07/2026 |
| Fases executadas | Fase 1 — Análise; Fase 2 — Auditoria e plano; Fase 3 — Refatoração e validação |
| Status da Fase 3 | Concluída após autorização explícita do usuário |
| Stack identificada | Python, Flask 3.0.0, Flask-SQLAlchemy 3.1.1 e SQLite |
| Dependências declaradas | Flask, Flask-SQLAlchemy, Flask-CORS, Marshmallow, Requests e python-dotenv |
| Arquivos-fonte analisados | `app.py`, `database.py`, `models/`, `routes/`, `services/`, `utils/` e `seed.py` |
| Volume analisado | 15 arquivos Python, 1.158 linhas de código-fonte |
| Ponto de entrada | `app.py` |
| Endpoints identificados | 22 |
| Confiança da análise | Alta |

Foram excluídos da contagem de fonte: `.agents`, `.venv`, caches, banco SQLite gerado e documentação. Os arquivos de dependências e configuração foram analisados separadamente.

## 2. Resumo executivo

O projeto implementa uma API de gerenciamento de tarefas, usuários, categorias e relatórios. A estrutura de diretórios sugere separação em models, routes, services e utils, mas as rotas concentram transporte HTTP, validação, autorização implícita, regras de negócio, consultas ORM, transações e serialização. O resultado é um monólito parcialmente organizado por pastas, sem fronteiras MVC efetivas.

Os riscos mais graves são de segurança: o login entrega um token fictício que nenhuma rota valida, clientes podem escolher ou alterar o próprio papel, senhas usam MD5 e o hash é devolvido pela API. Também existem segredos e credenciais no fonte, debug habilitado, CORS irrestrito e operações de leitura e escrita sem autenticação ou autorização.

Foram identificados **14 achados**: **3 críticos**, **2 altos**, **7 médios** e **2 baixos**. Nenhum arquivo-fonte do Projeto 3 foi modificado nas Fases 1 e 2. A Fase 3 começou somente após autorização explícita e seus resultados estão registrados na seção 12.

| Severidade | Quantidade |
|---|---:|
| CRÍTICO | 3 |
| ALTO | 2 |
| MÉDIO | 7 |
| BAIXO | 2 |
| **Total** | **14** |

## 3. Arquitetura observada

```text
Cliente HTTP
  -> app.py (Flask global + configuração + criação do schema)
    -> Blueprints em routes/
      -> validação + regra de negócio + serialização + transação
        -> models/ via Flask-SQLAlchemy
          -> SQLite (instance/tasks.db)

services/notification_service.py  (não conectado ao fluxo HTTP)
utils/helpers.py                  (majoritariamente não reutilizado pelas rotas)
```

- **Ponto de entrada e composition root:** `app.py`.
- **Modelos:** `User`, `Task` e `Category`.
- **Rotas:** 7 de tarefas, 7 de usuários, 6 de relatórios/categorias e 2 gerais.
- **Persistência:** SQLite pelo objeto global `db` do Flask-SQLAlchemy.
- **Arquitetura atual:** monólito Flask com separação nominal por pastas e God Controllers.
- **Testes:** nenhuma suíte automatizada localizada.
- **Fronteiras violadas:** handlers HTTP conhecem diretamente ORM, regras, transações e formato final das respostas.
- **Componente desconectado:** o serviço de notificações contém integração SMTP e estado em memória, mas não é utilizado pelas rotas.

## 4. Visão consolidada dos achados

| ID | Severidade | Achado | Evidência principal | Catálogo |
|---|---|---|---|---|
| AP3-001 | CRÍTICO | Autenticação fictícia permite elevação de privilégio | `routes/user_routes.py:42-86`, `185-210` | AP-SEC-04, AP-SEC-05 |
| AP3-002 | CRÍTICO | Senhas usam MD5 e o hash é exposto pela API | `models/user.py:16-32` | AP-SEC-03, AP-SEC-04 |
| AP3-003 | CRÍTICO | Segredos, credenciais e debug estão hardcoded | `app.py:11-15`, `33-34`; `services/notification_service.py:7-10` | AP-SEC-03 |
| AP3-004 | ALTO | Endpoints não aplicam autorização nem isolamento | `routes/user_routes.py:92-151`; `routes/task_routes.py:156-238`; `routes/report_routes.py:12-155` | AP-SEC-05 |
| AP3-005 | ALTO | Blueprints atuam como God Controllers | `routes/task_routes.py:1-299`; `routes/report_routes.py:1-223`; `routes/user_routes.py:1-211` | AP-ARC-01, AP-ARC-03 |
| AP3-006 | MÉDIO | Listagens e relatórios executam consultas N+1 | `routes/task_routes.py:14-57`; `routes/report_routes.py:53-68`, `157-165` | AP-PERF-01 |
| AP3-007 | MÉDIO | Coleções são carregadas sem paginação | `routes/task_routes.py:11-14`; `routes/user_routes.py:10-12`; `routes/report_routes.py:30` | AP-PERF-01 |
| AP3-008 | MÉDIO | Exceções genéricas ou silenciosas ocultam falhas | `routes/task_routes.py:61-63`, `225-238`; `utils/helpers.py:43-50` | AP-ERR-01, AP-QUAL-03 |
| AP3-009 | MÉDIO | Validação é duplicada e helpers permanecem sem uso | `utils/helpers.py:57-116`; `routes/task_routes.py:85-223`; `routes/user_routes.py:42-78` | AP-VAL-01, AP-ARC-03 |
| AP3-010 | MÉDIO | Parâmetros inválidos podem resultar em HTTP 500 | `routes/task_routes.py:240-271`; `routes/report_routes.py:190-209` | AP-VAL-01, AP-ERR-01 |
| AP3-011 | MÉDIO | Código usa APIs legadas ou depreciadas | `routes/task_routes.py:67`; `routes/user_routes.py:29`; `models/task.py:15-16`; `routes/report_routes.py:35-45` | AP-DEP-01 |
| AP3-012 | MÉDIO | Importar a aplicação cria o schema no banco | `app.py:30-31` | AP-ARC-02, AP-DATA-01 |
| AP3-013 | BAIXO | Valores de domínio são duplicados como literais | `models/task.py:38-48`; `routes/task_routes.py:102-114`; `utils/helpers.py:110-116` | AP-QUAL-01 |
| AP3-014 | BAIXO | Há imports, funções e serviço sem uso efetivo | `app.py:7`; `routes/task_routes.py:7`; `utils/helpers.py:1-7`; `services/notification_service.py:1-48` | AP-QUAL-02, AP-QUAL-03 |

## 5. Detalhamento dos achados

### AP3-001 — Autenticação fictícia permite elevação de privilégio

- **Severidade:** CRÍTICO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-04, AP-SEC-05
- **Arquivo:** `routes/user_routes.py`
- **Linhas:** 42–86, 92–129, 185–210
- **Confiança:** Alta

**Evidência:** o cadastro aceita `role` enviado pelo cliente, inclusive `admin`; a atualização também permite trocar o papel sem autenticação. O login valida a senha, mas devolve `fake-jwt-token-<id>`, previsível e sem assinatura, expiração ou verificação por qualquer endpoint.

**Impacto:** um cliente anônimo pode criar uma conta administrativa ou promover qualquer usuário. O token não estabelece identidade e transmite uma falsa sensação de proteção.

**Recomendação:** impedir escolha de papel no cadastro público, implementar sessão ou token assinado com expiração, criar middleware de autenticação e aplicar autorização por papel e por proprietário.

### AP3-002 — Senhas usam MD5 e o hash é exposto pela API

- **Severidade:** CRÍTICO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-03, AP-SEC-04
- **Arquivos:** `models/user.py`, `routes/user_routes.py`
- **Linhas:** `models/user.py:16-32`; `routes/user_routes.py:27-40`, `85-86`, `207-210`
- **Confiança:** Alta

**Evidência:** `set_password` usa MD5 sem salt e `to_dict()` inclui o campo `password`. Esse serializador é usado em criação, leitura, atualização e login.

**Impacto:** hashes capturados podem ser quebrados por força bruta ou tabelas pré-computadas, e a própria API facilita sua coleta.

**Recomendação:** migrar para função adaptativa como Argon2, scrypt ou bcrypt, aplicar rehash gradual no login e criar DTO/serializer público que nunca contenha senha ou hash.

### AP3-003 — Segredos, credenciais e debug estão hardcoded

- **Severidade:** CRÍTICO
- **Categoria:** Segurança e configuração
- **Catálogo:** AP-SEC-03
- **Arquivos:** `app.py`, `services/notification_service.py`
- **Linhas:** `app.py:11-15`, `app.py:33-34`, `services/notification_service.py:7-10`
- **Confiança:** Alta

**Evidência:** a chave da aplicação e as credenciais SMTP estão no fonte. A aplicação habilita CORS sem restrição, debug e exposição em todas as interfaces de rede. Os valores sensíveis não são reproduzidos neste relatório.

**Impacto:** o histórico Git e os artefatos podem revelar credenciais; debug remoto aumenta a superfície de ataque e configurações de desenvolvimento podem alcançar produção.

**Recomendação:** ler configuração validada de variáveis de ambiente, rotacionar credenciais reais, separar perfis de ambiente, limitar origens CORS e desabilitar debug por padrão.

### AP3-004 — Endpoints não aplicam autorização nem isolamento

- **Severidade:** ALTO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-05
- **Arquivos:** `routes/user_routes.py`, `routes/task_routes.py`, `routes/report_routes.py`
- **Linhas:** `routes/user_routes.py:10-183`; `routes/task_routes.py:11-299`; `routes/report_routes.py:12-223`
- **Confiança:** Alta

**Evidência:** listagem e alteração de usuários, CRUD de tarefas e categorias e relatórios são públicos. Nenhuma rota valida o token retornado pelo login, o papel do usuário ou a propriedade do recurso.

**Impacto:** clientes anônimos podem ler dados pessoais e operacionais, alterar tarefas de terceiros, desativar usuários, trocar papéis e excluir registros.

**Recomendação:** aplicar autenticação transversal, definir matriz de permissões e checar propriedade antes dos casos de uso; retornar 401 para identidade ausente e 403 para ação proibida.

### AP3-005 — Blueprints atuam como God Controllers

- **Severidade:** ALTO
- **Categoria:** MVC/SOLID
- **Catálogo:** AP-ARC-01, AP-ARC-03
- **Arquivos:** `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- **Linhas:** arquivos completos
- **Confiança:** Alta

**Evidência:** os três módulos de rotas combinam parsing HTTP, validação, regra de atraso, autorização implícita, acesso ORM, commit/rollback, agregação, serialização e logging.

**Impacto:** handlers ficam extensos e acoplados ao Flask e ao banco, regras são duplicadas e testes unitários exigem contexto completo da aplicação.

**Recomendação:** manter blueprints finos, extrair controllers, services/casos de uso, repositories e schemas/DTOs, com dependências montadas por uma application factory.

### AP3-006 — Listagens e relatórios executam consultas N+1

- **Severidade:** MÉDIO
- **Categoria:** Desempenho
- **Catálogo:** AP-PERF-01
- **Arquivos:** `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- **Linhas:** `routes/task_routes.py:14-57`; `routes/user_routes.py:10-23`; `routes/report_routes.py:53-68`, `157-165`
- **Confiança:** Alta

**Evidência:** a listagem de tarefas consulta usuário e categoria dentro do loop; a listagem de usuários acessa tarefas por usuário; relatórios consultam tarefas ou contagens para cada usuário/categoria.

**Impacto:** o número de consultas cresce linearmente com a coleção e pode provocar alta latência e carga excessiva no banco.

**Recomendação:** usar eager loading seletivo, JOINs e agregações `GROUP BY`, medindo a quantidade de consultas nos testes.

### AP3-007 — Coleções são carregadas sem paginação

- **Severidade:** MÉDIO
- **Categoria:** Desempenho e contrato HTTP
- **Catálogo:** AP-PERF-01
- **Arquivos:** `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- **Linhas:** `routes/task_routes.py:11-14`, `240-271`; `routes/user_routes.py:10-12`; `routes/report_routes.py:30`, `53`, `159`
- **Confiança:** Alta

**Evidência:** endpoints usam `.all()` e materializam listas inteiras; estatísticas também carregam todas as tarefas para contar atrasos.

**Impacto:** consumo de memória e tempo de resposta crescem sem limite, permitindo requests caros e instabilidade com volume real.

**Recomendação:** introduzir paginação com limites máximos, metadados de navegação e agregações no banco; preservar temporariamente o formato legado por estratégia de compatibilidade.

### AP3-008 — Exceções genéricas ou silenciosas ocultam falhas

- **Severidade:** MÉDIO
- **Categoria:** Tratamento de erros e observabilidade
- **Catálogo:** AP-ERR-01, AP-QUAL-03
- **Arquivos:** `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`, `utils/helpers.py`
- **Linhas:** `routes/task_routes.py:61-63`, `225-238`; `routes/user_routes.py:127-151`; `routes/report_routes.py:182-223`; `utils/helpers.py:43-50`
- **Confiança:** Alta

**Evidência:** há múltiplos `except:` sem tipo, contexto ou log. Outros blocos capturam `Exception`, imprimem a mensagem diretamente e devolvem um 500 genérico.

**Impacto:** erros de programação, infraestrutura e validação tornam-se indistinguíveis, dificultando diagnóstico e podendo mascarar regressões.

**Recomendação:** capturar exceções específicas, centralizar mapeamento de erros, manter rollback onde necessário e adotar logging estruturado sem dados sensíveis.

### AP3-009 — Validação é duplicada e helpers permanecem sem uso

- **Severidade:** MÉDIO
- **Categoria:** Validação e arquitetura
- **Catálogo:** AP-VAL-01, AP-ARC-03
- **Arquivos:** `routes/task_routes.py`, `routes/user_routes.py`, `utils/helpers.py`
- **Linhas:** `routes/task_routes.py:85-223`; `routes/user_routes.py:42-125`; `utils/helpers.py:19-23`, `43-116`
- **Confiança:** Alta

**Evidência:** regras de título, prioridade, status, email, senha, data e tags são implementadas diretamente e repetidas entre create/update. `process_task_data`, constantes e outros helpers equivalentes não são consumidos.

**Impacto:** regras divergem entre endpoints, mensagens e formatos aceitos variam e mudanças precisam ser repetidas em vários pontos.

**Recomendação:** definir schemas de entrada por operação, reutilizar validadores puros e manter regras de domínio nos services/models apropriados.

### AP3-010 — Parâmetros inválidos podem resultar em HTTP 500

- **Severidade:** MÉDIO
- **Categoria:** Validação e erros
- **Catálogo:** AP-VAL-01, AP-ERR-01
- **Arquivos:** `routes/task_routes.py`, `routes/report_routes.py`
- **Linhas:** `routes/task_routes.py:240-271`; `routes/report_routes.py:190-209`
- **Confiança:** Alta

**Evidência:** a busca converte `priority` e `user_id` com `int()` sem tratamento. A atualização de categoria usa `data` sem primeiro confirmar que JSON válido foi recebido.

**Impacto:** erros do cliente viram falhas internas, quebram o contrato HTTP e poluem monitoramento com 500 evitáveis.

**Recomendação:** validar tipos e presença do corpo antes do caso de uso e retornar 400 com erro estável por campo.

### AP3-011 — Código usa APIs legadas ou depreciadas

- **Severidade:** MÉDIO
- **Categoria:** Dependências e compatibilidade
- **Catálogo:** AP-DEP-01
- **Arquivos:** `models/category.py`, `models/task.py`, `models/user.py`, `routes/`
- **Linhas:** usos de `Query.get()` e `datetime.utcnow()`
- **Confiança:** Alta

**Evidência:** o código usa `Model.query.get()`, parte da API legada do SQLAlchemy, em vez de `Session.get()`. Também usa `datetime.utcnow()`, depreciado desde o Python 3.12 em favor de datas UTC conscientes de fuso.

**Impacto:** warnings se acumulam e futuras versões podem remover os caminhos legados, além de datas ingênuas causarem comparações ambíguas.

**Recomendação:** migrar consultas para `db.session.get(Model, id)` e padronizar timestamps UTC timezone-aware, validando compatibilidade de schema e serialização. Referências: [SQLAlchemy Legacy Query API](https://docs.sqlalchemy.org/en/20/orm/queryguide/query.html) e [Python 3.12 — `datetime.utcnow()` depreciado](https://docs.python.org/3.12/whatsnew/3.12.html).

### AP3-012 — Importar a aplicação cria o schema no banco

- **Severidade:** MÉDIO
- **Categoria:** Arquitetura e ciclo de vida de dados
- **Catálogo:** AP-ARC-02, AP-DATA-01
- **Arquivo:** `app.py`
- **Linhas:** 9–31
- **Confiança:** Alta

**Evidência:** `app` e extensões são globais e `db.create_all()` é executado no corpo do módulo, durante qualquer import.

**Impacto:** testes e ferramentas têm efeitos colaterais inesperados, configuração é rígida e criação de tabelas substitui migrations versionadas.

**Recomendação:** criar `create_app(config)`, inicializar extensões sem efeito colateral e mover evolução do schema para migrations e comandos explícitos.

### AP3-013 — Valores de domínio são duplicados como literais

- **Severidade:** BAIXO
- **Categoria:** Qualidade
- **Catálogo:** AP-QUAL-01
- **Arquivos:** `models/task.py`, `routes/task_routes.py`, `routes/user_routes.py`, `utils/helpers.py`
- **Linhas:** `models/task.py:38-48`; `routes/task_routes.py:102-114`, `176-183`; `routes/user_routes.py:64-72`, `114-121`; `utils/helpers.py:110-116`
- **Confiança:** Alta

**Evidência:** status, papéis, prioridades, tamanhos e cores são repetidos em models, rotas e constantes não utilizadas.

**Impacto:** alterações podem atualizar apenas uma cópia e produzir regras conflitantes.

**Recomendação:** definir enums/constantes de domínio em uma fonte única e fazer schemas e models reutilizarem essa definição.

### AP3-014 — Há imports, funções e serviço sem uso efetivo

- **Severidade:** BAIXO
- **Categoria:** Qualidade e observabilidade
- **Catálogo:** AP-QUAL-02, AP-QUAL-03
- **Arquivos:** `app.py`, `routes/task_routes.py`, `routes/user_routes.py`, `utils/helpers.py`, `services/notification_service.py`
- **Linhas:** arquivos completos conforme a visão consolidada
- **Confiança:** Alta

**Evidência:** diversos imports não são referenciados; vários helpers não são chamados; `NotificationService` não integra o fluxo da aplicação e mantém notificações em lista de instância; mensagens operacionais usam `print`.

**Impacto:** o código sugere capacidades que não existem no runtime, aumenta a área de manutenção e não oferece logging consistente.

**Recomendação:** confirmar usos por testes e busca, remover código morto, integrar somente serviços necessários por interface injetável e substituir `print` por logger configurado.

## 6. Matriz de cobertura do catálogo

| Antipadrão | Verificado | Encontrado | Achados relacionados |
|---|---:|---:|---|
| AP-SEC-01 — Execução arbitrária | Sim | Não | — |
| AP-SEC-02 — Injection | Sim | Não | Consultas ORM parametrizam valores; não foi localizado SQL textual concatenado |
| AP-SEC-03 — Segredos/dados expostos | Sim | Sim | AP3-002, AP3-003 |
| AP-SEC-04 — Credenciais fracas | Sim | Sim | AP3-001, AP3-002 |
| AP-ARC-01 — God Class/Module | Sim | Sim | AP3-005 |
| AP-SEC-05 — Autorização ausente | Sim | Sim | AP3-001, AP3-004 |
| AP-ARC-02 — Estado global/dependência rígida | Sim | Sim | AP3-012, AP3-014 |
| AP-DATA-01 — Transação/recurso inseguro | Sim | Sim | AP3-012 |
| AP-PERF-01 — N+1 | Sim | Sim | AP3-006, AP3-007 |
| AP-VAL-01 — Validação inconsistente | Sim | Sim | AP3-009, AP3-010 |
| AP-ERR-01 — Erros genéricos/ignorados | Sim | Sim | AP3-008, AP3-010 |
| AP-DATA-02 — Integridade insuficiente | Sim | Não | Chaves estrangeiras e unicidade básicas foram identificadas; política de acesso é tratada em AP3-004 |
| AP-DEP-01 — API/dependência obsoleta | Sim | Sim | AP3-011 |
| AP-ARC-03 — Violação de fronteira | Sim | Sim | AP3-005, AP3-009 |
| AP-QUAL-01 — Valores mágicos | Sim | Sim | AP3-013 |
| AP-QUAL-02 — Nomes/código morto | Sim | Sim | AP3-014 |
| AP-QUAL-03 — Logging improvisado | Sim | Sim | AP3-008, AP3-014 |

## 7. Plano proposto de refatoração

> Plano da Fase 2; nenhum item abaixo foi executado.

### Onda 0 — Congelar contratos

1. Criar testes de caracterização para os 22 endpoints, incluindo sucesso, validação, ausência e conflitos.
2. Criar application factory configurável e cliente Flask de teste, preservando o boot atual durante a transição.
3. Usar banco temporário por teste e fixtures determinísticas, sem depender de `instance/tasks.db`.

### Onda 1 — Conter riscos críticos

1. Externalizar configuração, remover segredos do fonte, desabilitar debug padrão e restringir CORS.
2. Remover hash de todos os serializers e migrar MD5 para hash adaptativo.
3. Implementar autenticação verificável, impedir papel administrativo no cadastro público e adicionar autorização/ownership.

### Onda 2 — Consolidar MVC e casos de uso

1. Manter blueprints responsáveis apenas por HTTP e controllers finos.
2. Extrair services de usuários, tarefas, categorias, autenticação e relatórios.
3. Encapsular queries e transações em repositories/unidades de trabalho injetáveis.
4. Centralizar schemas, DTOs e tratamento de erros.

### Onda 3 — Estabilizar desempenho e compatibilidade

1. Eliminar N+1 com eager loading e consultas agregadas.
2. Adicionar paginação limitada sem quebrar consumidores legados de forma abrupta.
3. Substituir APIs legadas e padronizar datas UTC timezone-aware.
4. Introduzir migrations e remover criação automática de schema no import.

### Onda 4 — Limpeza e validação final

1. Consolidar constantes de domínio e remover duplicação comprovada.
2. Remover imports, helpers e serviços mortos ou conectá-los por interfaces testáveis quando necessários.
3. Substituir `print` por logging estruturado e seguro.
4. Executar testes automatizados, boot real e smoke test dos 22 endpoints.

## 8. Contratos a preservar

- Ponto de entrada funcional equivalente a `python app.py` e porta configurável equivalente à atual 5000.
- Os 22 caminhos e métodos HTTP existentes durante a migração.
- Códigos de sucesso, validação, conflito e recurso ausente já observados, salvo correções de segurança explícitas.
- Campos públicos de tarefas, categorias, relatórios e usuários, exceto `password`, que não é contrato legítimo e deve ser removido.
- Valores aceitos de status (`pending`, `in_progress`, `done`, `cancelled`), prioridades de 1 a 5 e papéis válidos internamente.
- Semântica de cálculo de tarefas atrasadas e taxas de conclusão.
- Persistência SQLite como configuração padrão do exercício, mas substituível em testes.

Não devem ser preservados como contratos: MD5, hash na resposta, token fictício, escolha pública de papel, endpoints anônimos, segredos hardcoded, debug habilitado, CORS irrestrito, efeitos colaterais no import e respostas 500 para entrada inválida.

## 9. Plano de validação da Fase 3

- [ ] Aplicação inicia sem erro e sem criar schema apenas por ser importada.
- [ ] Suíte automatizada roda em banco temporário isolado.
- [ ] Os 22 endpoints possuem testes de caracterização e continuam respondendo.
- [ ] Cadastro público não permite escolher `admin` ou `manager`.
- [ ] Login fornece credencial verificável, expira e não retorna hash.
- [ ] Endpoints protegidos retornam 401/403 conforme identidade e permissão.
- [ ] Usuários não alteram recursos de terceiros sem permissão.
- [ ] Configuração sensível não permanece no fonte.
- [ ] Debug e CORS têm defaults seguros.
- [ ] Parâmetros inválidos retornam 400 estável, não 500.
- [ ] Exceções passam por tratamento central, com rollback e log seguro.
- [ ] Listagens possuem paginação e limite máximo.
- [ ] Consultas críticas não apresentam padrão N+1.
- [ ] `Query.get()` e `datetime.utcnow()` deixam de ser usados.
- [ ] Migrations controlam o schema.
- [ ] Smoke test HTTP real cobre os 22 endpoints após a refatoração.

## 10. Limitações da auditoria

- As Fases 1 e 2 foram estáticas; a Fase 3 registrou baseline e validação posterior dos 22 endpoints por HTTP real.
- O projeto não possuía testes automatizados; a Fase 3 criou uma suíte de caracterização, segurança e arquitetura antes das mudanças estruturais.
- Não foram instaladas, removidas ou atualizadas dependências.
- O serviço SMTP desconectado foi removido após busca de referências e testes verdes; nenhuma conexão externa foi realizada.
- Nenhum segredo ou hash encontrado foi reproduzido no relatório.
- A matriz implementada considera `admin` e `manager` como equipe, reserva exclusão de usuários para `admin` e restringe usuários comuns à própria conta e às próprias tarefas.

## 11. Confirmação obrigatória antes da Fase 3

**Fase 2 concluída. Foram encontrados 14 achados: 3 CRÍTICOS, 2 ALTOS, 7 MÉDIOS e 2 BAIXOS.**

**Deseja autorizar a Fase 3 e permitir a modificação dos arquivos do Projeto 3 para executar a refatoração proposta? Responda explicitamente com “sim” ou “não”. Sem resposta afirmativa, nenhuma refatoração deve ser iniciada.**

A autorização afirmativa foi recebida antes da primeira alteração da Fase 3. A pergunta acima foi preservada como evidência da barreira humana prevista na Skill.

## 12. Resultado da Fase 3

### 12.1 Resumo da transformação

O Projeto 3 passou a usar uma application factory e um composition root explícito. Os Blueprints agora tratam somente HTTP, validação já carregada e chamada a um controller. Controllers coordenam services; services aplicam autenticação, autorização, propriedade e transações; repositories concentram SQLAlchemy, paginação e agregações; models mantêm entidades e serializers públicos seguros.

```text
HTTP request
  -> middleware de autenticação
    -> schema Marshmallow
      -> route Blueprint
        -> controller
          -> service
            -> repository
              -> model / SQLite
  -> error handler central
```

- `app.py` não cria schema durante import e não contém instância global da aplicação.
- `config/` lê ambiente e exige `SECRET_KEY` forte.
- `middlewares/` valida tokens assinados e temporários e centraliza erros.
- `schemas/` mantém uma fonte única para validação.
- `repositories/` usa a API moderna do SQLAlchemy e consultas agregadas.
- `tests/` cobre contratos, segurança, arquitetura e HTTP real.
- Nenhuma dependência foi adicionada ou atualizada.

### 12.2 Tratamento dos achados

| Achado | Resultado da Fase 3 |
|---|---|
| AP3-001 | Resolvido: token assinado e temporário, autenticação obrigatória e cadastro público limitado a `user`. |
| AP3-002 | Resolvido: hash adaptativo do Werkzeug, senha mínima de 12 caracteres e serializers sem senha/hash. |
| AP3-003 | Resolvido: configuração vem do ambiente; credenciais SMTP e debug hardcoded foram removidos; CORS é restrito por configuração. |
| AP3-004 | Resolvido: autorização por papel e por proprietário aplicada a usuários, tarefas, categorias e relatórios. |
| AP3-005 | Resolvido: routes, controllers, services, repositories, schemas e middlewares possuem fronteiras explícitas. |
| AP3-006 | Resolvido: relacionamentos são carregados por JOIN e relatórios/listagens usam agregações; teste limita a listagem de tarefas a duas consultas incluindo autenticação. |
| AP3-007 | Resolvido: listagens aceitam `page`/`per_page`, têm default 50 e máximo 100; detalhes de atraso do relatório também são limitados. |
| AP3-008 | Resolvido: erros de aplicação e validação são tratados centralmente; escritas fazem rollback. |
| AP3-009 | Resolvido: schemas Marshmallow substituíram validações duplicadas e os helpers mortos foram removidos. |
| AP3-010 | Resolvido: tipos inválidos e JSON ausente retornam 400, cobertos por testes. |
| AP3-011 | Resolvido: `Session.get()`/`select()` substituíram `Query.get()` e timestamps usam `datetime.now(UTC)`. |
| AP3-012 | Resolvido no escopo do achado: importar `app.py` não cria banco ou schema; o seed é um comando explícito. |
| AP3-013 | Resolvido: status, papéis, prioridades e limites estão centralizados em `models/constants.py`. |
| AP3-014 | Resolvido: imports, helpers e serviço SMTP sem uso foram removidos; logging inesperado usa o logger do Flask. |

### 12.3 Testes automatizados

Comando principal:

```powershell
.\.venv\Scripts\python.exe -W "error::DeprecationWarning" -m unittest discover -s tests -v
```

Resultado: **16 testes executados, 16 aprovados**. Warnings de depreciação foram promovidos a erro para provar que os usos legados foram removidos.

Cobertura funcional da suíte:

- seis testes de contratos cobrindo os 22 endpoints;
- token ausente, adulterado e expirado;
- ausência de senha/hash nas respostas;
- bloqueio de elevação de papel e acesso cruzado;
- validação de tipos e senha mínima;
- paginação e limite máximo;
- integridade em exclusões;
- contagem de consultas contra N+1;
- fronteiras arquiteturais e import sem efeito colateral;
- configuração obrigatória de segredo.

Validações complementares:

- `python -m compileall`: aprovado;
- `python -m pip check`: nenhuma dependência quebrada;
- seed em SQLite temporário: 3 usuários, 4 categorias e 10 tarefas;
- busca estática: nenhum `Query.get()`, `datetime.utcnow()`, MD5, token falso, segredo legado, `debug=True` ou `except:`;
- routes sem acesso direto a `db`/ORM;
- controllers, services, repositories e models sem dependência de Flask;
- nenhuma serialização de senha e nenhum whitespace residual.

### 12.4 Boot e validação HTTP real

O comando abaixo iniciou um servidor Werkzeug em porta efêmera, com SQLite temporário, e realizou requests reais pela rede:

```powershell
.\.venv\Scripts\python.exe -m tests.smoke_http
```

Resultado: **22/22 endpoints respondendo**, com os mesmos caminhos, métodos e códigos de sucesso observados no baseline. A diferença intencional é que operações protegidas agora exigem `Authorization: Bearer <token>`.

### 12.5 Checklist de validação

- [x] Baseline registrado no commit `4bc2107` antes das mudanças.
- [x] Testes de caracterização criados antes da separação de camadas.
- [x] Application factory sem criação de schema no import.
- [x] Routes sem acesso direto ao ORM.
- [x] Controllers, services, repositories e schemas separados.
- [x] Configuração sensível lida do ambiente.
- [x] Token assinado, temporário e rejeitado quando alterado/expirado.
- [x] Senha com hash adaptativo e nunca serializada.
- [x] Autenticação, papéis e propriedade cobertos por testes.
- [x] Erros e rollback centralizados.
- [x] Paginação e limite máximo aplicados.
- [x] N+1 removido dos fluxos auditados.
- [x] APIs depreciadas removidas.
- [x] Seed explícito e sem exposição de credenciais.
- [x] 16/16 testes automatizados aprovados.
- [x] 22/22 endpoints aprovados por HTTP real.
- [ ] Adotar ferramenta formal de migrations antes de evolução de schema em produção.

### 12.6 Riscos e decisões remanescentes

- O exercício continua usando SQLite e criação explícita via `seed.py`; uma aplicação real deve adotar migrations versionadas antes de alterar o schema.
- Bancos locais criados pelo legado contêm hashes MD5 incompatíveis com o novo verificador. No exercício, execute novamente o seed; com dados reais seria necessária uma migração/reset de senha controlado.
- Tokens assinados expiram e verificam o estado atual do usuário, mas não há lista de revogação antecipada nem rate limiting de login.
- A política de autorização implementada deve ser validada com o responsável de negócio antes de uso produtivo.
- Atualizações de dependências foram deliberadamente excluídas desta refatoração estrutural.
