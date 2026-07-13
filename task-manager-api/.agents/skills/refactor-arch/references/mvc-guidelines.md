# Diretrizes da arquitetura MVC alvo

## Sumário

1. [Objetivo](#objetivo)
2. [Princípios de fronteira](#princípios-de-fronteira)
3. [Responsabilidades por camada](#responsabilidades-por-camada)
4. [Fluxo de uma requisição](#fluxo-de-uma-requisição)
5. [Estrutura de diretórios](#estrutura-de-diretórios)
6. [Configuração e composition root](#configuração-e-composition-root)
7. [Erros, segurança e transações](#erros-segurança-e-transações)
8. [Adaptação por tecnologia](#adaptação-por-tecnologia)
9. [Migração incremental](#migração-incremental)
10. [Critérios de aceite](#critérios-de-aceite)

## Objetivo

Organizar o projeto para separar entrada/saída, orquestração e dados sem alterar contratos públicos. Tratar MVC como fronteiras de responsabilidade, não como uma árvore rígida de nomes.

Para APIs:

- **View/Route:** traduz HTTP para uma chamada de aplicação e formata a resposta.
- **Controller:** coordena o caso de uso e decide o fluxo.
- **Model:** representa dados, invariantes e persistência.
- **Service:** encapsula regra de negócio ou integração que não pertence a uma entidade.
- **Repository:** opcionalmente abstrai consultas quando o ORM/model não fornece fronteira suficiente.

## Princípios de fronteira

- Fazer dependências apontarem da entrada para o domínio, não do domínio para HTTP.
- Manter uma única fonte de verdade para cada regra.
- Injetar dependências externas em vez de criá-las dentro do controller.
- Manter o ponto de entrada pequeno e explícito.
- Evitar abstrações sem uso; extrair apenas responsabilidades observadas.
- Preservar nomes de endpoints, métodos, códigos e schemas durante a migração.
- Adaptar a estrutura ao tamanho atual; não transformar um projeto pequeno em um framework interno.

## Responsabilidades por camada

### Routes ou Views

Permitir:

- declarar método, caminho e middleware;
- ler parâmetros, headers e body já validados;
- chamar exatamente um controller/caso de uso;
- converter resultado em status e payload.

Proibir:

- SQL ou ORM direto;
- cálculo de negócio;
- envio de e-mail ou pagamento;
- commit/rollback;
- leitura direta de secrets.

### Controllers

Permitir:

- orquestrar o caso de uso;
- chamar services e models/repositories;
- aplicar autorização contextual;
- retornar um resultado independente do framework quando viável.

Evitar:

- construir conexão de banco;
- conhecer detalhes de SQL;
- repetir validação já executada por schema;
- formatar profundamente objetos de resposta.

### Models

Permitir:

- representar entidades e relações;
- manter invariantes locais;
- mapear persistência quando o framework usar Active Record;
- serializar somente campos seguros e estáveis.

Proibir:

- importar request/response HTTP;
- devolver senha, token ou segredo;
- enviar notificações;
- misturar várias entidades sem uma relação de domínio.

### Services

Usar para:

- checkout, pagamento, autenticação e notificação;
- regras que coordenam múltiplos models;
- integrações externas;
- cálculos de domínio reutilizados.

Manter serviços pequenos, com entradas e saídas explícitas. Não criar um novo God Service.

### Repositories

Usar quando houver:

- SQL complexo;
- consultas repetidas;
- necessidade de trocar ou simular persistência;
- N+1 a resolver com operações em lote.

Não adicionar repository apenas para envolver uma chamada trivial do ORM sem ganho de fronteira.

## Fluxo de uma requisição

```text
HTTP request
  -> middleware/autenticação
  -> schema de validação
  -> route/view
  -> controller
  -> service (quando necessário)
  -> model/repository
  -> resultado de aplicação
  -> route/view
  -> HTTP response
```

Erros devem seguir um fluxo paralelo para um handler central, com rollback e resposta segura.

## Estrutura de diretórios

Usar como referência, adaptando nomes idiomáticos da stack:

```text
src/
├── app.<ext>                 # composition root/application factory
├── config/
│   └── settings.<ext>
├── models/
├── controllers/
├── routes/                   # views para APIs
├── services/
├── repositories/            # somente se necessário
├── schemas/                  # validação/serialização
├── middlewares/
│   └── error_handler.<ext>
└── database/
    ├── connection.<ext>
    └── migrations/
```

Projetos parcialmente organizados devem evoluir a estrutura existente. Não mover arquivos apenas para igualar essa árvore se as fronteiras já estiverem corretas.

## Configuração e composition root

- Ler ambiente em um único módulo de configuração.
- Validar variáveis obrigatórias no boot.
- Manter defaults apenas para valores não sensíveis e desenvolvimento local.
- Criar banco, services e controllers no composition root.
- Registrar rotas e error handlers no ponto de entrada.
- Evitar criar schema, executar seed ou abrir conexão como efeito colateral de importação.
- Manter seed e migrations como comandos explícitos.

## Erros, segurança e transações

- Definir erros de domínio independentes de HTTP.
- Traduzir erros para 4xx/5xx em um handler central.
- Não retornar stack trace ou mensagem de driver ao cliente.
- Fazer rollback para qualquer falha depois do início de uma unidade de trabalho.
- Autenticar antes de autorizar.
- Autorizar por ação e recurso, não apenas por role global.
- Remover campos sensíveis de serializers.
- Parametrizar consultas e validar caminhos/comandos.
- Mascarar dados sensíveis em logs.

## Adaptação por tecnologia

### Python/Flask

- Usar application factory quando melhorar testes e configuração.
- Usar Blueprints como routes/views, não como controllers completos.
- Gerenciar conexão/sessão pelo contexto da aplicação/requisição.
- Usar error handlers do Flask para tradução central.

### Node.js/Express

- Usar `Router` para rotas e handlers finos.
- Encaminhar erros para middleware com `next(error)`.
- Encapsular callbacks/promises de banco em repositories ou services.
- Encerrar recursos no shutdown da aplicação.

### Outras stacks

Mapear os mesmos papéis para os mecanismos idiomáticos: controllers do framework podem atuar como routes/views, desde que deleguem orquestração; entidades/ORM podem atuar como models; middleware/filtros podem centralizar autenticação e erros.

## Migração incremental

1. Congelar contratos com testes de caracterização.
2. Extrair configuração e composition root.
3. Centralizar validação e erros.
4. Separar rotas de controllers por domínio.
5. Extrair services para regras multi-entidade/integrações.
6. Encapsular persistência complexa e transações.
7. Corrigir segurança e desempenho preservando respostas.
8. Remover código antigo somente após testes verdes.

Executar testes após cada transformação. Evitar reescrever todos os módulos simultaneamente.

## Critérios de aceite

- [ ] Routes não acessam banco diretamente.
- [ ] Controllers não conhecem detalhes de SQL ou transporte externo.
- [ ] Models não dependem de HTTP.
- [ ] Regras têm uma única fonte de verdade.
- [ ] Configuração sensível vem do ambiente.
- [ ] Erros são tratados centralmente.
- [ ] Transações possuem rollback.
- [ ] Autenticação e autorização estão aplicadas às rotas necessárias.
- [ ] Ponto de entrada está claro e pequeno.
- [ ] Aplicação inicia sem erros.
- [ ] Testes existentes passam.
- [ ] Endpoints e formatos originais permanecem compatíveis.
