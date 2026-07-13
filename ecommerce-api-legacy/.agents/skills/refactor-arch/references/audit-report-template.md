# Template do relatório de auditoria

Usar este formato na Fase 2. Salvar em Markdown no caminho solicitado pelo usuário. Não alterar arquivos do projeto ao gerar o relatório.

## Sumário

1. [Modelo](#modelo)
2. [Regras de preenchimento](#regras-de-preenchimento)

## Modelo

````markdown
# Relatório de Auditoria Arquitetural

## Identificação

- **Projeto:** <nome>
- **Data:** <AAAA-MM-DD>
- **Stack:** <linguagem + framework + banco>
- **Arquitetura atual:** <descrição curta>
- **Arquivos analisados:** <quantidade>
- **Linhas analisadas:** <quantidade ou aproximação identificada>
- **Escopo excluído:** <dependências, build, gerados>

## Resumo executivo

<Descrever em 2 a 4 parágrafos os riscos dominantes, a maturidade arquitetural e a prioridade de correção. Separar fatos de inferências.>

| Severidade | Quantidade |
|---|---:|
| CRÍTICO | <n> |
| ALTO | <n> |
| MÉDIO | <n> |
| BAIXO | <n> |
| **Total** | **<n>** |

## Arquitetura observada

```text
<fluxo real: entrada -> rota -> controller -> serviço -> persistência>
```

- **Pontos de entrada:** <arquivos>
- **Camadas existentes:** <camadas>
- **Entidades principais:** <entidades>
- **Fronteiras violadas:** <resumo>

## Achados

### [CRÍTICO] <título objetivo>

- **ID:** AP-001
- **Categoria:** <Segurança | MVC | SOLID | Desempenho | Obsolescência | Qualidade>
- **Arquivo:** `caminho/arquivo.ext`
- **Linhas:** `<início>-<fim>`
- **Confiança:** <Alta | Média | Baixa>

**Evidência**

<Descrever o sinal observado. Incluir trecho mínimo quando ajudar, sem reproduzir senhas, tokens, cartões ou dados pessoais.>

**Descrição**

<Explicar o problema no contexto do projeto.>

**Impacto**

<Explicar consequência técnica, funcional ou de segurança.>

**Recomendação**

<Indicar transformação concreta, sem aplicá-la nesta fase.>

---

<Repetir para cada achado, ordenando CRÍTICO -> ALTO -> MÉDIO -> BAIXO.>

## Matriz de cobertura do catálogo

| Antipadrão | Verificado | Encontrado | Achados relacionados |
|---|---:|---:|---|
| <nome> | Sim/Não | Sim/Não | AP-001 |

## Plano proposto de refatoração

1. <mudança de menor risco>
2. <mudança seguinte>
3. <migração estrutural>
4. <validação final>

## Contratos a preservar

- <endpoint, comando, formato ou regra observável>
- <códigos HTTP e schemas relevantes>
- <comando de boot e testes>

## Plano de validação da Fase 3

- [ ] Aplicação inicia sem erros.
- [ ] Testes existentes passam.
- [ ] Endpoints originais respondem.
- [ ] Códigos HTTP permanecem compatíveis.
- [ ] Configuração sensível não está no fonte.
- [ ] Erros são tratados centralmente.
- [ ] Achados corrigidos são reavaliados.

## Limitações da auditoria

- <itens não executados ou não verificáveis>
- <dependências externas indisponíveis>
- <inferências que precisam de confirmação>

## Confirmação obrigatória

Fase 2 concluída. Foram encontrados <n> achados: <c> CRÍTICOS, <a> ALTOS, <m> MÉDIOS e <b> BAIXOS.

Deseja autorizar a Fase 3 e permitir a modificação dos arquivos para executar a refatoração proposta? Responda explicitamente com "sim" ou "não".
````

## Regras de preenchimento

- Criar um ID estável e único para cada achado.
- Não agrupar problemas sem relação apenas para reduzir a contagem.
- Agrupar ocorrências repetidas do mesmo padrão quando compartilharem causa e correção.
- Usar linhas exatas; não escrever apenas o nome do arquivo.
- Não inventar achados para atingir um mínimo.
- Informar confiança baixa quando a evidência depender de execução não realizada.
- Não expor o valor de segredos na evidência.
- Manter as recomendações específicas, incrementais e verificáveis.
- Não incluir afirmações como “zero problemas restantes” sem nova auditoria completa.
- Parar após a pergunta de confirmação, mesmo que o plano pareça seguro.
