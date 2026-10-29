# Consolidação da revisão técnica do M2

Data: 29/10/2026. Branch: `feat/m2-tse-importer`. Importador: **0.2.1**;
SQLite schema **1**; avaliação de manifesto/relatório **2**.

## Histórico e conflitos

Fetch de origin confirmou `origin/main` em
`84e38c9e3c78e25cff42c4a4d8b6c42a6d0c51ee`, nove commits documentais após a base
`37c066b`. A main foi incorporada na branch M2 por merge não destrutivo, preservando
os históricos de ambos os lados. Nenhuma branch adicional, rebase ou force push.

| Commit local | Conteúdo |
| --- | --- |
| `10e19f9` | Merge de origin/main e resolução documental |
| `401bcf5` | Estados independentes, cobertura exigida, confiança do operador, caminhos e regressões |
| Commit documental seguinte | Guia operacional, critérios e comparação real desta revisão; SHA no histórico e no relatório de entrega |

Os commits originais M2 `32dbb02` e `17dad43` e os nove commits da main continuam
alcançáveis. Não houve integração da branch em main, push, abertura de PR ou exclusão.

| Arquivo com conflito | Resolução |
| --- | --- |
| README.md | Estratégia dos dois produtos da main, com estado efetivo da CLI/SC e mock Flutter preservado |
| docs/ARCHITECTURE.md | Diagrama e separação de perfis da main, acrescentando fluxo e evidências M2 |
| docs/DATA_ARCHITECTURE.md | Contrato e princípios da main preservados; detalhes operacionais M2 transferidos para DATA_ENGINE_OPERATIONS.md e vinculados |
| docs/ROADMAP.md | M2.1/M2.2/M2.3 e escopo M3 da main preservados; distinguir itens implementados, conferência de SC e expansão pendente |
| docs/adr/0003-public-data-and-auditor.md | Oito decisões, contrato e consequências da main preservados integralmente; atualização de estado e apêndice da implementação |
| pipelines/README.md | Motor único/defaults/proteção de originais da main e comandos/capacidade real do M2 |

DATA_POLICY.md mesclou automaticamente e foi revisado, preservando as dez regras
da main e explicitando promoção local versus publicação. VISION.md e backend/README.md
entraram sem conflitos. Flutter e seu workflow não foram modificados.

## Dimensões independentes da avaliação

O manifesto/relatório não usa mais `valid` como garantia global de dataset.
`assessment` distingue integridade física SQLite, integridade referencial,
matemática, cobertura, hashes das fontes, reconciliação, elegibilidade local e
prontidão pública. `structurally_valid` não inclui sucesso matemático, hashes ou
cobertura. Um banco com somas erradas continua fisicamente íntegro, mas falha na
dimensão matemática e não pode ser promovido.

Totais ausentes resultam em mathematics=partially_checked. Falta de BUs ou
ambiguidade de contexto é registrada como reconciliação parcial/não verificável,
sem impedir uma investigação local cuja fonte primária seja inequívoca.
O código de saída de validate não substitui public_readiness para distribuição.

Prontidão técnica pública exige natureza official-derived declarada, critérios
locais satisfeitos, cobertura territorial explícita atendida, todos os hashes
comparados com referências de confiança atribuída pelo operador, reconciliação
completa e matemática conferida. O estado ready_for_declared_scope limita a
afirmação ao recorte registrado; não verifica automaticamente licença, origem
criptográfica, todas as seções cadastrais ou integridade eleitoral.

ALL continua selecionando o disponível. `coverage_requirements` aceita lista de
UFs/ZZ e turnos; NATIONAL representa 27 UFs + ZZ, exigindo 56 pares com dois turnos.
Filtros incompatíveis são recusados. Falta de cobertura exigida bloqueia promoção,
com relatório e ponteiro anterior preservados. O contrato mede presença de
território/turno, não inventário exaustivo por seção; essa última garantia fica
explicitamente not_assessed. [Configuração nacional de exemplo](../config/national-2026.example.json).

`trusted` significa confiança **atribuída pelo operador** à referência. A
coincidência de digest é separada dessa declaração. O motor nunca autentica
automaticamente a origem só pelo domínio/HTTPS; origin_authentication e
signature_verification permanecem not_performed. O status legado verified de
uma fonte é qualificado por status_scope; o agregado diz matched_operator_trusted.
Na revalidação de uma release, evidências de fontes/reconciliação vêm do catálogo
e relatório retidos, explicitamente identificadas; fontes não são relidas.

JSON v2 altera a interface de consumo: a lista tabular é observed_coverage;
assessment.coverage descreve expectativas e lacunas. report separa import_report
de current_validation. Releases anteriores schema 1 são reavaliadas sem reescrita.

## Precedência de caminhos

O adaptador do teste oficial reutiliza a configuração da CLI. TSE_REAL_INPUT
substitui input_dir do JSON e é resolvido contra o diretório de execução.
TSE_REAL_CONFIG é o arquivo de configuração; seus caminhos relativos, inclusive
output_dir, são resolvidos contra a pasta dele. Apenas CONFIG usa seu input_dir;
apenas INPUT usa saída temporária/SC/dois turnos. Sem ambos, o teste é pulado.
Override inexistente falha, sem fallback silencioso. As variáveis não afetam
automaticamente a CLI fora desse adaptador.

## Verificações executadas

- Ruff format --check e Ruff check: aprovados, 16 arquivos Python.
- Pytest final Windows/Python 3.12.10: **59 passaram em 70,94 s**, incluindo
  integração com os três ZIPs reais. Sem opt-in oficial: **58 passaram, 1 pulado**.
- Regressões acrescentadas: BU parcial com estrutura íntegra; manifestação das
  dimensões; ALL versus NATIONAL; presença completa de 56 pares sem inferir seções;
  exigências incompatíveis com filtros; hashes coincidentes com/sem confiança
  atribuída; prontidão restrita ao recorte; precedência e override inexistente;
  releases preservadas em falha de cobertura; evidência retida; retry Windows limitado.
- Wheel 0.2.1 construído e instalado na venv local. Executável instalado validado
  com help, import help, inventory, inspect, verify --crc, import idempotente,
  validate e report. validate também executado sobre a release histórica 0.2.0.
- git diff --check aprovado. Ancestralidade de origin/main confirmada. Sem mudanças
  no Flutter/workflow Flutter e nos dois arquivos da investigação original de SC.

O [workflow 40911141158](https://github.com/UrnaLivre/votoaberto/actions/runs/40911141158)
foi consultado via GitHub CLI: success nas quatro combinações Windows/Linux ×
Python 3.11/3.12, sobre `17dad43301afa5348fffb06b95181564734fcad4`. Isso confirma
o CI anterior, **não o CI dos novos commits locais**. Não foi disparado novo CI
nem executado Linux localmente nesta revisão.

Durante testes locais ocorreram negações intermitentes WinError 5 na promoção de
diretório, também no baseline antes das mudanças. Um teste isolado repetido passou.
Foi acrescentado retry limitado para WinError 5/32/33, mantendo os.replace atômico,
sem sobrescrever destino existente; erro persistente propaga e preserva ponteiro.
Não foi identificada a causa externa específica. Os testes finais passaram.

## Comparação real de SC

Os três ZIPs originais continuam acessíveis e foram processados novamente em
streams, sem alteração, movimentação ou extração integral. O derivado desta revisão
ficou em diretório separado; a release histórica e seu relatório não foram alterados.

| Métrica | Primeiro turno | Segundo turno |
| --- | ---: | ---: |
| Código de eleição | 6257 | 6258 |
| Chaves de seção | 17.326 | 17.326 |
| Registros presidenciais | 136.979 | 67.266 |
| Votos contabilizados | 4.648.159 | 4.762.303 |
| Votos nominais | 4.501.081 | 4.638.385 |
| Brancos | 69.007 | 48.674 |
| Nulos | 78.071 | 75.244 |

**204.245 linhas coincidentes**, sem divergências nem linhas exclusivas no recorte
SC; 34.652 pares seção/turno matched. Comparados com o resumo anterior: SHA-256 e
SHA-512 dos três ZIPs, cobertura, **todos** os totais por candidato, contadores de
reconciliação e totais/ausências por seção permaneceram idênticos. Diferença de
36 aptos entre turnos e categorias sem linha permanecem observações originais,
sem explicação ou correção inventada.

A avaliação atual informa integridade física/referencial/matemática passada,
cobertura completa **do recorte SC × dois turnos**, presença nacional incompleta,
completude cadastral de seções não avaliada e reconciliação completa no recorte.
As referências BWEB coincidem sob confiança atribuída pelo operador, mas falta
referência suficiente para o ZIP nacional. Consequentemente local_release=eligible
e public_readiness=not_ready, motivo operator_trusted_hashes_incomplete.

Release da revisão: `ff0ed50275a4a67f17842c35` em
`data/processed/sc-2026-review/releases/ff0ed50275a4a67f17842c35/` (ignorado pelo Git).
SQLite: **30.089.216 bytes / 28,70 MiB**. Execução medida até validação: **62,844 s**,
pico do processo pytest **82.522.112 bytes / 78,70 MiB**, zero checkpoints reutilizados.
Suíte completa e processamento têm tempos diferentes. Hash do SQLite pode mudar
com metadados/versões/regras, sem mudar resultados.

[Comparação legível por máquina](M2_REVIEW_REAL_VALIDATION.json) ·
[Investigação original preservada](TSE_2026_FORMAT_INVESTIGATION.md) ·
[Guia operacional e exemplos](DATA_ENGINE_OPERATIONS.md).

## Prontidão para PR e limites

A revisão está pronta para **submissão a PR/revisão humana**, com main incorporada,
histórico preservado, regressões locais e integração real aprovadas. O novo CI
Windows/Linux deve ser confirmado após envio autorizado, antes da integração.
Não houve publicação nem merge para main.

Isso não equivale a prontidão de distribuição de uma base pública nacional:
faltam referências suficientes para todas as fontes, BWEB das outras UFs/ZZ e
conferência nacional/por seção. Formatos/casos não suportados permanecem recusados.
Não foi validada interface Flutter real, assinatura digital, equipamento físico,
RDV/log ou regularidade eleitoral. Dados reais volumosos continuam fora do Git.
