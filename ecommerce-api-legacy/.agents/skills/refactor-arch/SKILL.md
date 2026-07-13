---
name: refactor-arch
description: Auditar projetos legados, detectar stack e arquitetura, classificar problemas de MVC, SOLID, segurança, desempenho e APIs obsoletas, gerar um relatório com arquivos e linhas exatas e, somente após confirmação explícita, refatorar para uma arquitetura MVC preservando o comportamento. Usar quando o usuário solicitar análise arquitetural, auditoria de code smells ou refatoração MVC em projetos de qualquer linguagem ou framework.
---

# Auditoria e Refatoração Arquitetural

Executar as três fases em ordem. Tratar a confirmação humana entre as Fases 2 e 3 como uma barreira obrigatória.

## Contrato de execução

- Trabalhar a partir da raiz do projeto-alvo atual.
- Detectar a tecnologia por evidências do repositório, sem assumir linguagem ou framework.
- Preservar contratos públicos, endpoints, formatos de resposta e regras observáveis.
- Informar arquivo e linha exata para cada achado.
- Não modificar arquivos durante as Fases 1 e 2.
- Encerrar a Fase 2 pedindo confirmação explícita.
- Não interpretar silêncio, contexto anterior ou uma solicitação genérica como autorização para a Fase 3.
- Executar a Fase 3 somente depois de receber uma resposta afirmativa inequívoca.

## Fase 1 — Análise do projeto

1. Inventariar arquivos-fonte, manifestos, dependências, testes e configurações.
2. Detectar linguagem, framework, banco de dados, domínio e arquitetura atual.
3. Mapear pontos de entrada, rotas, camadas, entidades e fluxos principais.
4. Imprimir um resumo objetivo com a stack e a quantidade de arquivos analisados.

## Fase 2 — Auditoria arquitetural

1. Avaliar o código contra o catálogo de antipadrões e as diretrizes MVC.
2. Classificar os achados como CRÍTICO, ALTO, MÉDIO ou BAIXO.
3. Ordenar os achados da maior para a menor severidade.
4. Registrar descrição, impacto, evidência e recomendação com arquivo e linha exata.
5. Gerar o relatório no caminho solicitado pelo usuário.
6. Exibir o resumo das severidades e o total de achados.
7. Perguntar se o usuário autoriza a Fase 3 e parar a execução.

## Fase 3 — Refatoração e validação

1. Confirmar que o usuário autorizou explicitamente a refatoração.
2. Registrar a linha de base disponível antes de modificar o código.
3. Aplicar transformações incrementais para separar Models, Views/Routes e Controllers.
4. Extrair configuração, serviços e tratamento de erros quando o contexto exigir.
5. Preservar endpoints e comportamento externo.
6. Iniciar a aplicação e validar os endpoints originais.
7. Relatar a nova estrutura, arquivos alterados, testes executados e problemas remanescentes.

## Referências

- Antes da Fase 1, ler [project-analysis.md](references/project-analysis.md).
- Antes da Fase 2, ler [anti-pattern-catalog.md](references/anti-pattern-catalog.md) e [audit-report-template.md](references/audit-report-template.md).
- Antes da Fase 3, ler [mvc-guidelines.md](references/mvc-guidelines.md) e [refactoring-playbook.md](references/refactoring-playbook.md).
