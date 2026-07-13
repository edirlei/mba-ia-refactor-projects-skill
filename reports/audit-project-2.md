# Relatório de auditoria arquitetural — Projeto 2

## 1. Identificação

| Campo | Valor |
|---|---|
| Projeto analisado | `ecommerce-api-legacy` |
| Data da análise | 12/07/2026 |
| Fases executadas | Fase 1 — Análise; Fase 2 — Auditoria e plano |
| Fase não executada | Fase 3 — Refatoração |
| Stack identificada | JavaScript/CommonJS, Node.js, Express 4.22.1 e SQLite 5.1.7 em memória |
| Dependências declaradas | Express `^4.18.2` e SQLite3 `^5.1.6` |
| Arquivos-fonte analisados | `src/app.js`, `src/AppManager.js`, `src/utils.js` |
| Volume analisado | 3 arquivos, 180 linhas de código-fonte |
| Ponto de entrada | `src/app.js` por `npm start` |
| Confiança da análise | Alta |

Escopo excluído da contagem de fonte: `node_modules`, lockfile, documentação e exemplos HTTP. O `package-lock.json` foi analisado separadamente para verificar versões e dependências obsoletas.

## 2. Resumo executivo

Apesar do nome do diretório, o código implementa uma API de LMS com cursos, usuários, matrículas, pagamentos, checkout e relatório financeiro. O projeto registra três endpoints e cria cinco tabelas SQLite em memória durante o boot.

A classe `AppManager` concentra criação do banco, seeds, rotas HTTP, validação, checkout, pagamento, auditoria, relatório e exclusão de usuários. Essa concentração combina riscos arquiteturais com problemas críticos de segurança: credenciais no fonte, dados financeiros em logs e autenticação baseada em transformação inadequada de senha.

Foram identificados **14 achados**: **3 críticos**, **4 altos**, **5 médios** e **2 baixos**. Nenhum arquivo-fonte foi modificado; a Fase 3 permanece bloqueada até autorização explícita.

| Severidade | Quantidade |
|---|---:|
| CRÍTICO | 3 |
| ALTO | 4 |
| MÉDIO | 5 |
| BAIXO | 2 |
| **Total** | **14** |

## 3. Arquitetura observada

```text
Cliente HTTP
  -> src/app.js (bootstrap Express)
    -> AppManager.setupRoutes(app)
      -> handlers inline
        -> validação parcial + pagamento + regra de checkout
          -> this.db (SQLite em memória)
            -> resposta HTTP e console/cache globais
```

- **Ponto de entrada:** `src/app.js`.
- **Componente central:** `src/AppManager.js`.
- **Utilidades e configuração:** `src/utils.js`.
- **Endpoints:** `POST /api/checkout`, `GET /api/admin/financial-report` e `DELETE /api/users/:id`.
- **Entidades/tabelas:** `users`, `courses`, `enrollments`, `payments` e `audit_logs`.
- **Arquitetura atual:** monólito procedural encapsulado em uma God Class.
- **Testes:** nenhuma suíte automatizada; `api.http` contém quatro cenários manuais.
- **Fronteiras violadas:** o mesmo módulo conhece Express, SQLite, regras de pagamento, persistência, logs e formatos de resposta.

## 4. Visão consolidada dos achados

| ID | Severidade | Achado | Evidência principal | Catálogo |
|---|---|---|---|---|
| AP2-001 | CRÍTICO | Credenciais e chaves hardcoded | `src/utils.js:1-6` | AP-SEC-03 |
| AP2-002 | CRÍTICO | Cartão e chave de pagamento expostos em log | `src/AppManager.js:43-46` | AP-SEC-03, AP-QUAL-03 |
| AP2-003 | CRÍTICO | Senha padrão e transformação criptográfica inadequada | `src/utils.js:17-22` | AP-SEC-04 |
| AP2-004 | ALTO | `AppManager` atua como God Class | `src/AppManager.js:4-138` | AP-ARC-01, AP-ARC-03 |
| AP2-005 | ALTO | Rotas administrativas sem autenticação/autorização | `src/AppManager.js:80-137` | AP-SEC-05 |
| AP2-006 | ALTO | Checkout sem transação atômica | `src/AppManager.js:50-61` | AP-DATA-01 |
| AP2-007 | ALTO | Estado global mutável e dependências rígidas | `src/utils.js:9-15` | AP-ARC-02 |
| AP2-008 | MÉDIO | Relatório financeiro executa consultas N+1 | `src/AppManager.js:83-127` | AP-PERF-01 |
| AP2-009 | MÉDIO | Erros de callbacks ignorados | `src/AppManager.js:54-61` | AP-ERR-01 |
| AP2-010 | MÉDIO | Schema sem integridade referencial | `src/AppManager.js:10-21` | AP-DATA-02 |
| AP2-011 | MÉDIO | Nove dependências transitivas marcadas deprecated | `package-lock.json:33-38` | AP-DEP-01 |
| AP2-012 | MÉDIO | Validação e decisão de pagamento superficiais | `src/AppManager.js:28-48` | AP-VAL-01 |
| AP2-013 | BAIXO | Nomes abreviados escondem o domínio | `src/AppManager.js:29-33` | AP-QUAL-02 |
| AP2-014 | BAIXO | Código morto, valores mágicos e logging improvisado | `src/utils.js:6-22` | AP-QUAL-01, AP-QUAL-02, AP-QUAL-03 |

## 5. Detalhamento dos achados

### AP2-001 — Credenciais e chaves hardcoded

- **Severidade:** CRÍTICO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-03
- **Arquivo:** `src/utils.js`
- **Linhas:** 1–6
- **Confiança:** Alta

**Evidência:** o objeto `config` contém usuário e senha de banco, chave de gateway e usuário SMTP diretamente no fonte. Os valores foram deliberadamente omitidos deste relatório.

**Impacto:** qualquer pessoa com acesso ao repositório, histórico ou artefato obtém credenciais potencialmente utilizáveis. A mesma configuração é compartilhada por todos os ambientes.

**Recomendação:** retirar os valores do fonte, carregá-los de variáveis de ambiente validadas no boot e rotacionar qualquer credencial que tenha sido real.

### AP2-002 — Cartão e chave de pagamento expostos em log

- **Severidade:** CRÍTICO
- **Categoria:** Segurança e observabilidade
- **Catálogo:** AP-SEC-03, AP-QUAL-03
- **Arquivo:** `src/AppManager.js`
- **Linhas:** 43–46
- **Confiança:** Alta

**Evidência:** o checkout registra no console o número integral recebido no campo de cartão e a chave configurada do gateway.

**Impacto:** dados financeiros e credenciais podem persistir em terminais, coletores de logs, backups e ferramentas de observabilidade.

**Recomendação:** remover o log sensível, registrar somente identificador de correlação e, se indispensável, os quatro últimos dígitos mascarados; nunca registrar chaves ou payloads financeiros.

### AP2-003 — Senha padrão e transformação criptográfica inadequada

- **Severidade:** CRÍTICO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-04
- **Arquivos:** `src/AppManager.js`, `src/utils.js`
- **Linhas:** `src/AppManager.js:18`, `src/AppManager.js:66-70`, `src/utils.js:17-22`
- **Confiança:** Alta

**Evidência:** o seed armazena senha legível, o checkout adota uma senha padrão quando o campo está vazio e `badCrypto` repete Base64 antes de truncar o resultado.

**Impacto:** Base64 não é algoritmo de hash de senha, entradas diferentes podem produzir valores fracos e contas podem ser criadas com credencial previsível.

**Recomendação:** exigir senha válida, usar `scrypt`, `bcrypt` ou `argon2` com salt e custo adequados e nunca manter senha legível em seed de produção.

### AP2-004 — `AppManager` atua como God Class

- **Severidade:** ALTO
- **Categoria:** MVC/SOLID
- **Catálogo:** AP-ARC-01, AP-ARC-03
- **Arquivos:** `src/AppManager.js`, `src/app.js`
- **Linhas:** `src/AppManager.js:4-138`, `src/app.js:5-13`
- **Confiança:** Alta

**Evidência:** uma classe cria a conexão e o schema, insere seeds, registra rotas, valida requests, decide pagamentos, executa SQL, monta relatórios e formata respostas.

**Impacto:** testes isolados são difíceis, alterações têm grande raio de impacto e Express, negócio e SQLite permanecem rigidamente acoplados.

**Recomendação:** extrair application factory, routers, controllers, services de checkout/pagamento, repositories, models e configuração, preservando os endpoints.

### AP2-005 — Rotas administrativas sem autenticação/autorização

- **Severidade:** ALTO
- **Categoria:** Segurança
- **Catálogo:** AP-SEC-05
- **Arquivo:** `src/AppManager.js`
- **Linhas:** 80–137
- **Confiança:** Alta

**Evidência:** o relatório financeiro e a exclusão de usuários estão publicamente registrados, sem middleware de identidade, papel ou escopo.

**Impacto:** clientes anônimos podem consultar dados financeiros e excluir usuários arbitrários.

**Recomendação:** autenticar o principal e autorizar permissões administrativas específicas antes de executar controller ou repository.

### AP2-006 — Checkout sem transação atômica

- **Severidade:** ALTO
- **Categoria:** Dados
- **Catálogo:** AP-DATA-01
- **Arquivo:** `src/AppManager.js`
- **Linhas:** 50–61
- **Confiança:** Alta

**Evidência:** matrícula, pagamento e auditoria são gravados por callbacks sucessivos, sem `BEGIN`, `COMMIT` e `ROLLBACK` comuns.

**Impacto:** uma falha após a matrícula pode deixar pagamento ou auditoria ausentes, resultando em estado parcial.

**Recomendação:** encapsular o checkout em uma unidade de trabalho transacional e reverter todas as escritas em qualquer falha intermediária.

### AP2-007 — Estado global mutável e dependências rígidas

- **Severidade:** ALTO
- **Categoria:** Arquitetura
- **Catálogo:** AP-ARC-02
- **Arquivos:** `src/utils.js`, `src/AppManager.js`
- **Linhas:** `src/utils.js:9-15`, `src/AppManager.js:5-8`
- **Confiança:** Alta

**Evidência:** `globalCache` é mutado entre chamadas e a conexão SQLite é criada diretamente no construtor da classe central.

**Impacto:** requisições e testes compartilham estado, o cache não possui política de expiração e a persistência não pode ser substituída ou isolada facilmente.

**Recomendação:** injetar database, repositories e logger; encapsular cache com ciclo de vida e limites explícitos ou removê-lo se não houver consumidor real.

### AP2-008 — Relatório financeiro executa consultas N+1

- **Severidade:** MÉDIO
- **Categoria:** Desempenho
- **Catálogo:** AP-PERF-01
- **Arquivo:** `src/AppManager.js`
- **Linhas:** 83–127
- **Confiança:** Alta

**Evidência:** após listar cursos, o código consulta matrículas por curso e, para cada matrícula, busca usuário e pagamento separadamente.

**Impacto:** o número de consultas cresce como `1 + cursos + 2 × matrículas`, elevando latência e complexidade assíncrona.

**Recomendação:** obter cursos, matrículas, usuários e pagamentos com JOIN/agregação e montar o formato final em uma única passagem.

### AP2-009 — Erros de callbacks ignorados

- **Severidade:** MÉDIO
- **Categoria:** Tratamento de erros
- **Catálogo:** AP-ERR-01
- **Arquivo:** `src/AppManager.js`
- **Linhas:** 54–61, 92–126 e 131–136
- **Confiança:** Alta

**Evidência:** o callback do audit log não verifica `err`; consultas internas do relatório assumem arrays/objetos válidos; a exclusão responde sucesso mesmo quando SQLite informa erro.

**Impacto:** podem ocorrer respostas de sucesso falsas, exceções por valores ausentes, requests sem resposta e ausência de rollback.

**Recomendação:** converter a API de banco para Promises, propagar erros ao middleware central e responder sucesso somente após confirmação da operação.

### AP2-010 — Schema sem integridade referencial

- **Severidade:** MÉDIO
- **Categoria:** Dados
- **Catálogo:** AP-DATA-02
- **Arquivo:** `src/AppManager.js`
- **Linhas:** 10–21 e 131–136
- **Confiança:** Alta

**Evidência:** as tabelas não declaram foreign keys, e-mail único, campos obrigatórios ou domínios de status. A própria resposta de exclusão informa que matrículas e pagamentos permanecem órfãos.

**Impacto:** duplicidades, referências quebradas e relatórios financeiros inconsistentes.

**Recomendação:** criar migrations com `NOT NULL`, `UNIQUE`, `CHECK` e foreign keys, ativar `PRAGMA foreign_keys` e definir políticas de exclusão.

### AP2-011 — Nove dependências transitivas marcadas deprecated

- **Severidade:** MÉDIO
- **Categoria:** Obsolescência
- **Catálogo:** AP-DEP-01
- **Arquivo:** `package-lock.json`
- **Linhas:** 33–38, 160–164, 763–767, 827–831, 1074–1078, 1478–1482, 1569–1573, 1718–1722 e 2113–2117
- **Confiança:** Alta

**Evidência:** o lockfile marca como deprecated `@npmcli/move-file`, `are-we-there-yet`, `gauge`, `glob`, `inflight`, `npmlog`, `prebuild-install`, `rimraf` e `tar`. A árvore instalada mostra que todos chegam transitivamente por `sqlite3`, principalmente por `node-gyp` e `prebuild-install`.

**Impacto:** manutenção bloqueada, warnings de instalação, vazamento de memória declarado em `inflight` e riscos conhecidos em versões antigas de `glob` e `tar`.

**Recomendação:** avaliar uma versão direta de `sqlite3` cuja árvore remova os pacotes obsoletos ou adotar driver mantido compatível; atualizar somente após consultar compatibilidade e executar regressão completa.

### AP2-012 — Validação e decisão de pagamento superficiais

- **Severidade:** MÉDIO
- **Categoria:** Validação
- **Catálogo:** AP-VAL-01
- **Arquivo:** `src/AppManager.js`
- **Linhas:** 28–48
- **Confiança:** Alta

**Evidência:** os campos têm nomes abreviados e apenas presença parcial é verificada; e-mail, senha, curso e cartão não têm schema de tipo/formato. O pagamento é decidido somente pelo primeiro caractere do cartão.

**Impacto:** entradas inválidas podem persistir, erros de tipo podem virar falhas internas e o fluxo representa pagamento aprovado sem integração verificável.

**Recomendação:** definir schema central, normalizar nomes e tipos e isolar um `PaymentService` com contrato explícito e adapter de teste.

### AP2-013 — Nomes abreviados escondem o domínio

- **Severidade:** BAIXO
- **Categoria:** Qualidade
- **Catálogo:** AP-QUAL-02
- **Arquivo:** `src/AppManager.js`
- **Linhas:** 29–33, 52, 89–106 e 132–133
- **Confiança:** Alta

**Evidência:** variáveis como `u`, `e`, `p`, `cid`, `cc`, `enrId`, `c` e `enr` exigem reconstruir mentalmente seu significado.

**Impacto:** revisão e manutenção ficam mais lentas, especialmente no fluxo assíncrono aninhado.

**Recomendação:** adotar nomes de domínio completos durante a extração incremental, sem alterar o payload externo antes dos testes de caracterização.

### AP2-014 — Código morto, valores mágicos e logging improvisado

- **Severidade:** BAIXO
- **Categoria:** Qualidade
- **Catálogo:** AP-QUAL-01, AP-QUAL-02, AP-QUAL-03
- **Arquivos:** `src/utils.js`, `src/AppManager.js`, `src/app.js`
- **Linhas:** `src/utils.js:6-22`, `src/AppManager.js:45-46`, `src/AppManager.js:68`, `src/app.js:12-13`
- **Confiança:** Alta

**Evidência:** `totalRevenue` não é consumido, porta, quantidade de iterações, senha padrão e prefixo de cartão são literais, e `console.log` é usado como logging da aplicação.

**Impacto:** regras ficam implícitas, componentes parecem ter funções inexistentes e logs não possuem nível, contexto ou política de proteção.

**Recomendação:** remover código comprovadamente morto, consolidar constantes/configuração e injetar logger estruturado com política de dados sensíveis.

## 6. Matriz de cobertura do catálogo

| Antipadrão | Verificado | Encontrado | Achados relacionados |
|---|---:|---:|---|
| AP-SEC-01 — Execução arbitrária | Sim | Não | — |
| AP-SEC-02 — Injection | Sim | Não | Consultas externas usam placeholders |
| AP-SEC-03 — Segredos/dados expostos | Sim | Sim | AP2-001, AP2-002 |
| AP-SEC-04 — Credenciais fracas | Sim | Sim | AP2-003 |
| AP-ARC-01 — God Class/Module | Sim | Sim | AP2-004 |
| AP-SEC-05 — Autorização ausente | Sim | Sim | AP2-005 |
| AP-ARC-02 — Estado global/dependência rígida | Sim | Sim | AP2-007 |
| AP-DATA-01 — Transação/recurso inseguro | Sim | Sim | AP2-006 |
| AP-PERF-01 — N+1 | Sim | Sim | AP2-008 |
| AP-VAL-01 — Validação inconsistente | Sim | Sim | AP2-012 |
| AP-ERR-01 — Erros genéricos/ignorados | Sim | Sim | AP2-009 |
| AP-DATA-02 — Integridade insuficiente | Sim | Sim | AP2-010 |
| AP-DEP-01 — API/dependência obsoleta | Sim | Sim | AP2-011 |
| AP-ARC-03 — Violação de fronteira | Sim | Sim | AP2-004 |
| AP-QUAL-01 — Valores mágicos | Sim | Sim | AP2-014 |
| AP-QUAL-02 — Nomes/código morto | Sim | Sim | AP2-013, AP2-014 |
| AP-QUAL-03 — Logging improvisado | Sim | Sim | AP2-002, AP2-014 |

## 7. Plano proposto de refatoração

> Plano da Fase 2; nenhum item abaixo foi executado.

### Onda 0 — Congelar contratos

1. Criar testes de caracterização para os três endpoints e quatro cenários do `api.http`.
2. Separar criação do servidor de `listen`, permitindo testes sem porta real.
3. Tornar a inicialização assíncrona determinística e expor encerramento do banco.

### Onda 1 — Conter riscos críticos

1. Externalizar configuração e remover credenciais/dados financeiros dos logs.
2. Substituir `badCrypto` por algoritmo de senha apropriado e eliminar senha padrão.
3. Adicionar autenticação e autorização às rotas administrativas.

### Onda 2 — Separar MVC e casos de uso

1. Extrair routers Express e controllers finos.
2. Criar `CheckoutService`, `PaymentService` e `ReportService`.
3. Encapsular SQLite em repositories injetáveis e manter models/DTOs seguros.
4. Centralizar validação e middleware de erros.

### Onda 3 — Estabilizar dados e desempenho

1. Envolver checkout em transação com rollback.
2. Introduzir migrations e constraints de integridade.
3. Substituir o N+1 do relatório por JOIN/agregação.
4. Definir política segura de exclusão de usuário.

### Onda 4 — Dependências e limpeza

1. Avaliar atualização/substituição do driver SQLite para remover transitivas deprecated.
2. Regenerar lockfile somente após decisão de compatibilidade.
3. Remover estado/código morto, consolidar constantes e logging.
4. Executar testes, boot e os três endpoints pela rede.

## 8. Contratos a preservar

- Comando de boot `npm start` e porta configurável equivalente à porta atual 3000.
- `POST /api/checkout` com payload legado `usr`, `eml`, `pwd`, `c_id` e `card` durante a migração.
- Checkout aprovado retorna JSON com `msg` e `enrollment_id`.
- Pagamento recusado, curso ausente e requests inválidos mantêm códigos 400/404 compatíveis.
- `GET /api/admin/financial-report` continua retornando array por curso com receita e estudantes, após exigir autorização.
- `DELETE /api/users/:id` continua existindo, mas deve adotar autorização e política de integridade segura.
- Seeds e banco em memória devem ser substituíveis em teste sem impedir o boot padrão.

Não devem ser preservados como contratos: credenciais no fonte, log de cartão/chave, senha padrão, hash inadequado, acesso administrativo anônimo, registros órfãos e respostas de sucesso após erro.

## 9. Plano de validação da Fase 3

- [ ] Aplicação inicia sem erros com `npm start`.
- [ ] Testes de caracterização passam.
- [ ] Os três endpoints originais respondem.
- [ ] Os quatro cenários de `api.http` permanecem cobertos.
- [ ] Configuração sensível não está no fonte.
- [ ] Logs não contêm cartão, senha, chave ou payload sensível.
- [ ] Checkout reverte matrícula, pagamento e auditoria em falha.
- [ ] Rotas administrativas rejeitam cliente não autorizado.
- [ ] Relatório usa consulta agregada sem N+1.
- [ ] Exclusão não produz registros órfãos.
- [ ] Erros chegam ao middleware central e não geram sucesso falso.
- [ ] Dependências deprecated são reavaliadas sem atualização cega.

## 10. Limitações da auditoria

- A auditoria desta etapa foi estática; o boot e os endpoints não foram reexecutados durante as Fases 1 e 2.
- O banco é criado em memória, portanto seu estado desaparece ao encerrar a aplicação.
- Não existe suíte automatizada para confirmar todos os contratos assíncronos antes da Fase 3.
- O lockfile prova os avisos deprecated, mas a escolha de atualização/substituição exige validação de compatibilidade durante a refatoração.
- Nenhum valor de segredo, chave ou cartão foi reproduzido neste relatório.

## 11. Confirmação obrigatória antes da Fase 3

**Fase 2 concluída. Foram encontrados 14 achados: 3 CRÍTICOS, 4 ALTOS, 5 MÉDIOS e 2 BAIXOS.**

**Deseja autorizar a Fase 3 e permitir a modificação dos arquivos do Projeto 2 para executar a refatoração proposta? Responda explicitamente com “sim” ou “não”. Sem resposta afirmativa, nenhuma refatoração deve ser iniciada.**
