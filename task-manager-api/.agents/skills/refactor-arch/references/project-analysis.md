# Heurísticas de análise de projeto

## Sumário

1. [Princípios](#princípios)
2. [Sequência de análise](#sequência-de-análise)
3. [Inventário e escopo](#inventário-e-escopo)
4. [Detecção de linguagem e framework](#detecção-de-linguagem-e-framework)
5. [Detecção de banco e persistência](#detecção-de-banco-e-persistência)
6. [Mapeamento da arquitetura](#mapeamento-da-arquitetura)
7. [Inferência do domínio](#inferência-do-domínio)
8. [Dependências e APIs obsoletas](#dependências-e-apis-obsoletas)
9. [Linha de base funcional](#linha-de-base-funcional)
10. [Saída da Fase 1](#saída-da-fase-1)

## Princípios

- Basear toda conclusão em arquivos observados no repositório.
- Separar fatos, inferências e pontos ainda não verificados.
- Não instalar dependências nem iniciar serviços durante o inventário sem autorização.
- Não modificar arquivos nas Fases 1 e 2.
- Excluir dependências vendorizadas, artefatos de build, caches e bancos gerados da contagem de fonte.
- Não considerar o nome de uma pasta como prova suficiente de tecnologia ou domínio.
- Registrar caminhos relativos à raiz do projeto.

## Sequência de análise

1. Localizar a raiz do projeto e os manifestos.
2. Enumerar arquivos relevantes e diretórios ignorados.
3. Detectar linguagens por manifestos, extensões e imports.
4. Detectar frameworks por dependências e padrões de bootstrap.
5. Detectar bancos, ORMs, migrations e entidades.
6. Mapear pontos de entrada, rotas, módulos e fluxo de dependências.
7. Inferir o domínio por rotas, entidades e vocabulário recorrente.
8. Contar arquivos-fonte e linhas sem incluir artefatos gerados.
9. Identificar comandos de boot e teste já declarados.
10. Produzir o resumo da Fase 1 com evidências e nível de confiança.

## Inventário e escopo

Usar ferramentas de busca disponíveis no ambiente. Preferir `rg` quando existir:

```powershell
rg --files -uu -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/.venv/**'
rg -n "scripts|dependencies|require|import|route|router|Blueprint|CREATE TABLE" .
```

Ignorar na análise de arquitetura, salvo quando forem relevantes para dependências:

- `.git/`, `.venv/`, `venv/`, `node_modules/`;
- `dist/`, `build/`, `coverage/`, `.pytest_cache/`, `__pycache__/`;
- arquivos binários, bancos gerados e bundles minificados;
- lockfiles ao contar linhas de código, mas não ao auditar dependências.

Registrar separadamente:

- fontes de aplicação;
- testes;
- configuração e infraestrutura;
- migrations e seeds;
- documentação;
- arquivos gerados.

## Detecção de linguagem e framework

Exigir pelo menos duas evidências quando possível: manifesto mais padrão de código, por exemplo.

| Sinal | Inferência provável | Confirmação complementar |
|---|---|---|
| `requirements.txt`, `pyproject.toml`, `.py` | Python | imports e comando de boot |
| `package.json`, `.js`, `.ts` | Node.js/JavaScript/TypeScript | scripts, `require` ou `import` |
| `pom.xml`, `build.gradle` | Java/Kotlin | packages e classe de bootstrap |
| `.csproj`, `.sln` | .NET | `Program.cs`, controllers |
| `go.mod` | Go | packages e `main.go` |
| `Cargo.toml` | Rust | crates e `main.rs` |
| `composer.json` | PHP | front controller e framework |

Frameworks HTTP comuns:

| Sinais | Framework provável |
|---|---|
| `from flask import`, `Flask(__name__)`, `Blueprint` | Flask |
| `django`, `manage.py`, `settings.py`, `urls.py` | Django |
| `fastapi`, `FastAPI()`, decorators HTTP | FastAPI |
| `require('express')`, `express()`, `router.get` | Express |
| `@Controller`, `@GetMapping` | Spring |
| `ControllerBase`, `MapControllers` | ASP.NET Core |

Não declarar uma versão apenas pela memória. Ler a versão no manifesto, lockfile ou ferramenta instalada e informar a origem.

## Detecção de banco e persistência

Procurar:

- drivers: SQLite, PostgreSQL, MySQL, SQL Server, MongoDB;
- ORMs: SQLAlchemy, Django ORM, Prisma, Sequelize, TypeORM, Hibernate;
- strings de conexão e variáveis de ambiente;
- migrations, schemas, `CREATE TABLE`, models e repositories;
- conexão em memória versus persistente;
- chaves, índices, constraints e relacionamentos.

Mapear cada entidade ou tabela principal e suas relações. Distinguir:

- SQL parametrizado de SQL concatenado;
- acesso direto do controller de acesso encapsulado;
- conexão global de sessão por requisição;
- schema criado no boot de migrations controladas.

## Mapeamento da arquitetura

Identificar primeiro o fluxo real, não apenas os nomes dos diretórios.

Para cada endpoint ou caso de uso representativo, seguir:

```text
entrada -> rota/view -> controller/handler -> serviço -> persistência -> resposta
```

Classificar a arquitetura atual com evidências:

- monólito procedural;
- monólito modular;
- MVC completo ou apenas nominal;
- arquitetura em camadas;
- serviços independentes;
- organização por domínio ou por tipo técnico.

Registrar violações de fronteira, como:

- SQL em rotas;
- HTTP em models;
- regra de negócio em bootstrap;
- configuração e credenciais no código;
- módulos que concentram vários domínios;
- dependências circulares ou globais.

## Inferência do domínio

Usar, nesta ordem:

1. entidades e tabelas;
2. rotas e operações;
3. nomes de serviços e casos de uso;
4. seeds e exemplos HTTP;
5. README e nome do projeto.

Descrever o domínio em uma frase concreta, por exemplo: “API de cursos com checkout, matrículas e pagamentos”. Evitar descrições genéricas como “sistema web”. Se README e código divergirem, priorizar o comportamento observado e registrar a divergência.

## Dependências e APIs obsoletas

- Ler manifestos e lockfiles sem atualizar pacotes.
- Registrar pacotes marcados como deprecated no próprio lock ou no instalador.
- Procurar chamadas a APIs declaradas legadas pela documentação da versão usada.
- Distinguir dependência direta de transitiva.
- Não classificar uma API como obsoleta apenas por parecer antiga.
- Consultar documentação oficial quando a classificação depender de versão.
- Informar alternativa recomendada e compatibilidade necessária.

## Linha de base funcional

Quando o ambiente já estiver autorizado e preparado:

1. Executar o comando oficial de boot.
2. Registrar porta, código de saída e avisos.
3. Executar testes existentes antes de criar novos.
4. Exercitar endpoints públicos e códigos HTTP.
5. Registrar formatos essenciais de request e response sem copiar segredos.
6. Encerrar todos os processos iniciados.

Não usar a ausência de testes como justificativa para alterar comportamento. Criar testes de caracterização apenas na Fase 3 e após autorização.

## Saída da Fase 1

Imprimir o resumo neste formato:

```text
PHASE 1: PROJECT ANALYSIS
Project:       <nome>
Language:      <linguagem e evidência>
Framework:     <framework e versão>
Dependencies:  <principais>
Database:      <banco e mecanismo de acesso>
Domain:        <descrição objetiva>
Architecture:  <classificação atual>
Entry points:  <arquivos>
Source files:  <quantidade analisada>
Tests:         <existentes ou ausentes>
Confidence:    <alta, média ou baixa; justificar se não for alta>
```

Não iniciar a Fase 2 até concluir esse inventário.
