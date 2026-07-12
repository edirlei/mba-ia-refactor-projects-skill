# Catálogo de antipadrões

## Sumário

1. [Como usar](#como-usar)
2. [Calibração de severidade](#calibração-de-severidade)
3. [Antipadrões críticos](#antipadrões-críticos)
4. [Antipadrões altos](#antipadrões-altos)
5. [Antipadrões médios](#antipadrões-médios)
6. [Antipadrões baixos](#antipadrões-baixos)

## Como usar

- Procurar sinais em qualquer linguagem sem depender apenas de nomes de arquivos.
- Confirmar o fluxo de dados antes de registrar uma vulnerabilidade.
- Registrar caminho e linhas de cada evidência.
- Agrupar ocorrências com a mesma causa e correção; separar causas independentes.
- Informar confiança e falsos positivos considerados.
- Ajustar a severidade para cima somente com impacto demonstrável no contexto.
- Não registrar um achado apenas para cumprir uma quantidade mínima.

## Calibração de severidade

| Severidade | Usar quando |
|---|---|
| **CRÍTICO** | Permitir comprometimento, perda ampla de dados, exposição de segredos ou quebra completa das fronteiras arquiteturais. |
| **ALTO** | Violar fortemente MVC/SOLID, autorização ou consistência, tornando mudanças e testes muito arriscados. |
| **MÉDIO** | Causar duplicação, validação frágil, degradação de desempenho ou risco moderado de manutenção. |
| **BAIXO** | Prejudicar legibilidade, padronização ou evolução sem risco funcional imediato. |

## Antipadrões críticos

### AP-SEC-01 — Execução arbitrária de comando, código ou consulta [CRÍTICO]

- **Sinais:** receber código, comando shell ou SQL completo da requisição e encaminhar a `eval`, shell, interpreter ou executor de banco.
- **Confirmar:** entrada controlável externamente, ausência de allowlist e capacidade de leitura/escrita.
- **Falso positivo:** console administrativo isolado, autenticado, autorizado e com operações restritas.
- **Impacto:** execução remota, perda de dados ou comprometimento total.
- **Correção:** remover a interface genérica e expor operações explícitas com autorização e parâmetros.

### AP-SEC-02 — Injection em SQL, shell, template ou caminho [CRÍTICO]

- **Sinais:** concatenação, interpolação ou formatação de entrada em consultas/comandos; caminhos usados sem validação.
- **Confirmar:** seguir a origem do valor até o sink e verificar se existe parametrização real.
- **Falso positivo:** query builder que produz bind parameters; valores constantes não controláveis.
- **Impacto:** leitura, alteração, exclusão, execução ou acesso indevido.
- **Correção:** usar parâmetros, APIs estruturadas, allowlists e normalização de caminhos.

### AP-SEC-03 — Segredos ou dados sensíveis expostos [CRÍTICO]

- **Sinais:** senhas, tokens, chaves, cartões, conexão ou PII no fonte, resposta, log, seed ou exemplo realista.
- **Confirmar:** diferenciar placeholder evidente de segredo utilizável; verificar `.env`, config e histórico.
- **Falso positivo:** valor de teste claramente inválido em fixture isolada, ainda assim evitar aparência de segredo real.
- **Impacto:** invasão de serviços, fraude, vazamento e incidente de compliance.
- **Correção:** usar secret manager/variáveis de ambiente, rotacionar valores e mascarar logs.

### AP-SEC-04 — Autenticação ou credenciais fundamentalmente fracas [CRÍTICO]

- **Sinais:** senha em texto puro, MD5/SHA simples, token previsível, senha padrão, login sem verificação ou role fornecida pelo cliente.
- **Confirmar:** verificar geração, armazenamento, validação e uso do token nas rotas protegidas.
- **Falso positivo:** token explicitamente fictício em teste que não faz parte da aplicação executável.
- **Impacto:** tomada de conta, escalada de privilégio e acesso irrestrito.
- **Correção:** usar algoritmo específico para senhas, token assinado/sessão segura e política de roles no servidor.

## Antipadrões altos

### AP-ARC-01 — God Class, God Module ou God Method [ALTO]

- **Sinais:** um componente concentra HTTP, regras, persistência, integração, configuração e múltiplos domínios.
- **Confirmar:** mapear responsabilidades e dependências; tamanho isolado não é prova suficiente.
- **Falso positivo:** composition root longo que apenas conecta componentes sem regras.
- **Impacto:** acoplamento, baixa testabilidade e alto risco de regressão.
- **Correção:** extrair rotas, controllers, services, repositories/models e configuração por responsabilidade.

### AP-SEC-05 — Autorização ausente ou IDOR [ALTO]

- **Sinais:** endpoints administrativos sem guard; acesso por ID sem validar proprietário; cliente escolhe role ou tenant.
- **Confirmar:** verificar middleware, decorators, policies e filtros de escopo.
- **Falso positivo:** API deliberadamente pública e somente leitura, documentada como tal.
- **Impacto:** leitura ou mutação de recursos de terceiros e escalada vertical/horizontal.
- **Correção:** autenticar, autorizar por ação e filtrar recursos pelo principal/tenant.

### AP-ARC-02 — Estado global mutável ou dependência rígida [ALTO]

- **Sinais:** cache, conexão, sessão ou serviço mutável em escopo global; singleton oculto; imports com estado.
- **Confirmar:** verificar compartilhamento entre requisições, threads e testes.
- **Falso positivo:** constante imutável ou pool thread-safe administrado pelo framework.
- **Impacto:** corrida, vazamento entre requisições, testes não determinísticos e acoplamento.
- **Correção:** injetar dependências, definir ciclos de vida e usar componentes thread-safe.

### AP-DATA-01 — Transação ou ciclo de vida de recurso inseguro [ALTO]

- **Sinais:** várias escritas dependentes sem transação; commit sem rollback; conexão nunca fechada; recurso criado no import.
- **Confirmar:** simular mentalmente falha em cada passo e observar o estado resultante.
- **Falso positivo:** operação idempotente ou transação garantida por unidade externa documentada.
- **Impacto:** dados parciais, locks, corrupção lógica e falhas intermitentes.
- **Correção:** delimitar unidade de trabalho com begin/commit/rollback e gerenciar recurso por contexto.

## Antipadrões médios

### AP-PERF-01 — Consulta N+1 ou carregamento repetitivo [MÉDIO]

- **Sinais:** consulta dentro de loop; acesso lazy por item; contagem individual para cada entidade.
- **Confirmar:** estimar consultas como `1 + N` ou `1 + N + itens`.
- **Falso positivo:** coleção pequena e fixa não elimina o padrão, mas pode reduzir prioridade.
- **Impacto:** latência e carga de banco crescentes.
- **Correção:** join, eager loading, agregação ou busca em lote.

### AP-VAL-01 — Validação ausente, duplicada ou inconsistente [MÉDIO]

- **Sinais:** acesso a campos sem conferir JSON/tipo; regras repetidas; conversões sem tratamento; schemas declarados e não usados.
- **Confirmar:** comparar create/update e testar entradas vazias, tipos errados e limites.
- **Falso positivo:** validação central executada antes do handler.
- **Impacto:** respostas 500, dados inválidos e contratos divergentes.
- **Correção:** centralizar schemas/validators e devolver erros 4xx previsíveis.

### AP-ERR-01 — Tratamento de erro genérico, silencioso ou vazando detalhes [MÉDIO]

- **Sinais:** `catch/except` genérico, bloco vazio, erro interno retornado ao cliente, callback `err` ignorado.
- **Confirmar:** verificar logs, rollback e resposta em todos os caminhos.
- **Falso positivo:** boundary global que captura genericamente depois de handlers específicos.
- **Impacto:** diagnóstico difícil, respostas penduradas e exposição de internals.
- **Correção:** capturar tipos esperados, centralizar tradução HTTP, registrar contexto seguro e garantir cleanup.

### AP-DATA-02 — Integridade de dados insuficiente [MÉDIO]

- **Sinais:** ausência de foreign keys, unique, not-null ou validação de domínio; exclusão deixa órfãos.
- **Confirmar:** comparar invariantes de negócio com schema e código.
- **Falso positivo:** integridade garantida por datastore externo com contrato verificável.
- **Impacto:** duplicidades, referências quebradas e relatórios incorretos.
- **Correção:** aplicar constraints/migrations e definir cascades ou políticas explícitas.

### AP-DEP-01 — API ou dependência obsoleta [MÉDIO]

- **Sinais:** aviso `deprecated`, pacote sem suporte, API marcada legacy, lockfile com dependência vulnerável ou removida na versão-alvo.
- **Confirmar:** consultar manifesto, lockfile, warning de execução e documentação oficial da versão utilizada.
- **Falso positivo:** API antiga ainda suportada e não marcada como legacy; idade isolada não basta.
- **Impacto:** vulnerabilidades, incompatibilidade futura e manutenção bloqueada.
- **Correção:** migrar para a API recomendada, atualizar a dependência direta responsável e executar testes de regressão.

### AP-ARC-03 — Violação de fronteira ou lógica duplicada entre camadas [MÉDIO]

- **Sinais:** rota acessa banco diretamente; model conhece HTTP; mesmas regras em helper, controller e model.
- **Confirmar:** desenhar o fluxo e localizar a fonte de verdade da regra.
- **Falso positivo:** acesso simples em projeto mínimo, quando explicitamente aceito; ainda registrar trade-off se crescer.
- **Impacto:** divergência de regras e mudanças espalhadas.
- **Correção:** definir ownership por camada e mover cada regra para uma única fonte.

## Antipadrões baixos

### AP-QUAL-01 — Números, strings ou status mágicos [BAIXO]

- **Sinais:** limites, roles, estados, portas ou percentuais repetidos como literais.
- **Confirmar:** procurar repetição e significado de domínio.
- **Falso positivo:** literal local óbvio usado uma única vez.
- **Impacto:** intenção oculta e alterações inconsistentes.
- **Correção:** usar constantes, enums ou configuração no escopo adequado.

### AP-QUAL-02 — Nomenclatura fraca, código morto ou imports inúteis [BAIXO]

- **Sinais:** nomes de uma letra fora de loops, parâmetros genéricos, imports/métodos nunca usados, branches inalcançáveis.
- **Confirmar:** usar busca de referências e entender APIs públicas antes de remover.
- **Falso positivo:** parâmetro exigido por interface ou callback.
- **Impacto:** maior custo cognitivo e falsa expectativa de funcionalidade.
- **Correção:** renomear por intenção e remover somente após confirmação de não uso.

### AP-QUAL-03 — Logging improvisado ou inconsistente [BAIXO]

- **Sinais:** `print`/`console.log` dispersos, mensagens sem nível/contexto, logs duplicados.
- **Confirmar:** verificar se existe logger central ou interceptação do runtime.
- **Falso positivo:** utilitário de linha de comando simples onde stdout é a interface.
- **Impacto:** observabilidade fraca e dificuldade de correlação.
- **Correção:** adotar logger estruturado, níveis e política de dados sensíveis.
