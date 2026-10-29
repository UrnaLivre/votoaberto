# ADR 0003 — Data Engine compartilhado, Auditor e base pública

Estado: aceito para o M2. Data: 2026-10-29.

Este documento não existia na base `37c066b`. Foi criado nesta missão para
formalizar a decisão fornecida nos requisitos; não reconstruímos um ADR anterior.

## Decisão

Um único motor Python em `pipelines/tse_importer` detém inventário, integridade,
parsing, seleção, normalização, validação, reconciliação e exportação. A CLI
`apps/votoaberto_auditor` adapta argumentos e apresenta diagnósticos. Outros
programas podem importar o motor sem Flutter, CLI ou conexão de rede.

O perfil `public` exporta SQLite versionado com resultados presidenciais por
seção, hierarquia de consulta, candidatos, totais disponíveis, agregações e
proveniência. BWEB é fonte de conferência e de totais disponíveis, sem copiar
boletins completos, logs ou identificadores técnicos para a base pública.

O perfil `analyst` acrescenta registros presidenciais normalizados de cada fonte
e contexto técnico selecionado. Não é um arquivo completo de todos os BUs/cargos.
Os originais permanecem imutáveis e externos; o motor nunca os extrai em massa.

SQLite também serve como staging em disco e checkpoint por membro. Cada unidade
completa é transacional e identificada por hash da fonte, membro, regras, opções,
versão do importador e schema. Não introduzir DuckDB/Parquet agora: o processamento
observado é viável com streams e SQLite, sem dependências de runtime adicionais.
Reavaliar essas alternativas com medições nacionais e necessidades analíticas.

Cada release é imutável, validada e acompanhada de manifesto e relatórios.
`current.json` é o ponteiro local substituído atomicamente após conclusão.
Publicação aqui significa disponibilização **local** do derivado; não há deploy.
Falhas deixam diagnóstico no staging e preservam a release anterior.

## Semântica e consequências

- Presidente (`1`), ambos os turnos de 2026, são o recorte suportado. Não declarar
  outros cargos apenas porque seus registros foram encontrados e inventariados.
- Preservar códigos TSE como texto, inclusive zeros; município TSE não é IBGE.
- `ZZ` é exterior. `ALL` seleciona abrangências disponíveis, sem prometer cobertura
  nacional. Regras desconhecidas (`97`, BU não apurado etc.) bloqueiam a importação
  do recorte afetado com mensagem explícita.
- Chave tabular: eleição, UF, município, zona, seção e votável. Eleição identifica
  um turno. Contexto adicional distingue registros BWEB.
- Não somar automaticamente contextos concorrentes de uma seção. Múltiplos
  contextos impedem usar esse BU na conferência; sem fonte primária inequívoca,
  impedir publicação. Seções agregadas não são expandidas artificialmente.
- Ausência de categoria não equivale a zero. Totais desconhecidos são `NULL`, com
  estado de disponibilidade. Dados inválidos são recusados, sem correção inventada.
- Correspondência SHA refere-se a bytes sob a confiança declarada na referência.
  Correspondência de resultados refere-se às tabelas comparadas. Nenhuma dessas
  verificações certifica a integridade eleitoral.
- O Flutter M1 e seu `MockElectionRepository` permanecem intactos. Adaptação ao
  contrato público será uma entrega posterior, com revisão de cobertura/semântica.

Detalhes operacionais e limites: [DATA_ARCHITECTURE](../DATA_ARCHITECTURE.md).
