# Operação do Data Engine e VotoAberto Auditor — M2 / M3.1

Biblioteca Python 3.11+ e CLI Windows/Linux, independentes do Flutter. Runtime
sem dependências externas: `csv`, `zipfile`, `hashlib` e SQLite. O mock M1 permanece
intacto. Decisão: [ADR 0003](adr/0003-public-data-and-auditor.md). Evidências:
[investigação real de SC](TSE_2026_FORMAT_INVESTIGATION.md).

## Instalação e comandos

Na raiz, PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install ".[dev]"
.venv\Scripts\votoaberto-auditor --help
```

Linux: `python3 -m venv .venv`, `.venv/bin/python -m pip install '.[dev]'`,
`.venv/bin/votoaberto-auditor --help`. Ative a venv ou use seu executável nos exemplos:

```powershell
votoaberto-auditor inventory --input "D:\TSE" --json inventory.json
votoaberto-auditor inspect --input "D:\TSE" --json inspection.json
votoaberto-auditor verify --input "D:\TSE" --crc --json verification.json
votoaberto-auditor import --config config/president-2026.example.json
votoaberto-auditor plan --config config/national-2026.example.json --json plan.json
votoaberto-auditor import --input "D:\TSE" --output data/processed/sc --territory SC
votoaberto-auditor validate --dataset data/processed/sc
votoaberto-auditor report --dataset data/processed/sc --json report.json
```

Os três primeiros aceitam `--references arquivo.json`. `import` aceita `--office
president`, `--round 1 --round 2`, `--territory SC`, `--profile public|analyst`,
`--synthetic`, `--no-resume` e `--require-verified`. Flags substituem opções
correspondentes do JSON. Cargos/combinações desconhecidos geram erro explícito.

Configuração: [exemplo](../config/president-2026.example.json). Padrão: presidente,
2026, dois turnos, ALL, public. ALL significa abrangências disponíveis, sem
prometer cobertura nacional. UF explícita exige presença em cada turno. JSON
aceita `input_dir`, `output_dir`, `selection`, `limits`, `references`, `data_kind`,
`resume`, `require_verified`, `source_metadata`, `coverage_requirements`, `storage`,
`source_paths`, `inventory_cache`; opções desconhecidas falham. Caminhos no JSON são
relativos à configuração; caminhos na CLI, ao diretório atual. Entrada e saída
devem ser separadas, sem sobreposição. Não versionar caminhos pessoais.

Stdout: JSON; stderr: progresso/erros. Códigos: 0 sucesso (inclusive hashes
`unverified`, declarados), 1 validação negativa, 2 erro, 130 Ctrl+C. `validate`
aceita release, diretório com `current.json` ou SQLite. Arquivo SQLite isolado
permite verificar o banco, mas não os hashes dos demais artefatos.

## Código e uso como biblioteca

```text
pipelines/tse_importer/
  domain.py       seleção, limites e registro de domínio independente do formato
  discovery.py    inventário e streams ZIP seguros
  integrity.py    SHA-256/SHA-512 e referências
  schemas.json    colunas efetivamente observadas nos ZIPs
  parsers.py      BWEB e votação por seção 2026
  storage.py      staging e exportação SQLite
  validation.py   matemática, reconciliação e validação independente do banco
  engine.py       checkpoints, relatórios e promoção local
  partitioned.py  unidades primárias e consolidação sequencial por UF/turno
  workspace.py    orçamento, propriedade, temporários e limpeza segura
  reporting.py    resumo exato e detalhe limitado
  planning.py     preflight sem gerar bancos
apps/votoaberto_auditor/votoaberto_auditor/cli.py
tests/            fixtures gerados, falhas, integração e volume
```

```python
from pathlib import Path
from tse_importer.domain import Config, Selection
from tse_importer.engine import run_import

release = run_import(Config(
    input_dir=Path('/fontes/TSE'), output_dir=Path('/derivados/sc'),
    selection=Selection(territories=('SC',)),
))
```

O motor não importa a CLI nem usa rede. O perfil public projeta resultados
presidenciais, totais disponíveis e proveniência; não copia BUs completos ou logs.
Analyst acrescenta `analyst_presidential`, com registros presidenciais das fontes
e contexto técnico selecionado. Não é um arquivo completo de todos os cargos/BUs.

## Formatos e semântica

Somente conjuntos exatos de colunas em `schemas.json`, separador `;`, Latin-1,
2026 e eleição ordinária. Ordem das colunas pode variar. Campos ausentes/adicionais,
cabeçalhos duplicados, BOM e outros delimitadores não recebem interpretação
inventada. Latin-1 é o contrato dos leiautes; não existe detector heurístico
universal de codificação. A inspeção informa amostra e cabeçalho.

Presidente exige código `1` e descrição `Presidente`. BWEB usa ordinária `0`;
votação por seção usa `2`, abrangência `F` e unidade `BR`. Suporte a nominal,
branco `95` e nulo `96`; BWEB exige tipos votáveis `1/2/3` correspondentes e tipo
de urna `1` (apurada). Não suportados: `97`, outros tipos votáveis/situações BU,
arquivos binários BU/assinaturas/RDV/logs, outros cargos/anos/schemas e BR/VT como
território. Esses casos no recorte selecionado interrompem a importação, com
membro/linha. Outros cargos são contados na leitura, sem exportação.

Identificadores permanecem texto, com zeros; TSE não é IBGE. `SQ_CANDIDATO` fica
separado do número de campanha. Nomes BWEB e votação podem diferir: comparar
número dentro da eleição, sem impor igualdade de nome entre fontes. Candidato
precisa ser consistente dentro da fonte escolhida. Não aplicar padding ou
aproximação às chaves. `ZZ` é exterior, não uma 28ª UF.

`NULL` não é zero. Categoria sem linha permanece ausente. `totals_status`
distingue `missing` (`-1`, `#NULO#`), `not_recorded` (`-3`, `#NE#`), `present`
e `unavailable_no_unique_bu`. Zero explícito é preservado. Erro interrompe
processamento; não vira zero. Raw sentinels/contexto selecionado ficam no staging
e no perfil analyst. Dados sintéticos devem declarar `data_kind: synthetic`.

## Segurança e recursos

Limites padrão por ZIP: 1.000 membros, índice de 8 MiB, membro de 8 GiB, expansão
total declarada de 16 GiB, razão 300, linha de 1 MiB. SQLite: cache de 16 MiB por
conexão, temporários em disco, lotes de 2.000 linhas. O índice é verificado antes
da alocação por ZipFile, incluindo metadados ZIP64. Rejeitar traversal,
caminhos absolutos/ADS, links, duplicatas, criptografia e arquivos aninhados.
Extensões desconhecidas são inventariadas e recusadas na importação.

Nunca extrair caminhos do ZIP. Ler um membro por stream até EOF força conferência
de CRC, inclusive PDFs auxiliares. A inspeção parcial informa `crc_checked: false`.
Buffers/índice/expansão são limitados; não há limite rígido de RSS nem quota de
disco. Para entradas hostis, aplicar quotas do SO. Não há descompactação integral,
download ou exclusão automática de originais.

## Hashes, confiança e proveniência

Calcular SHA-256/SHA-512 em blocos durante o inventário. Comparar tamanho, mtime e
identidade durante inventário, antes/depois dos streams e antes da consolidação.
Checkpoint retido é relido e seu hash e marcador transacional são conferidos.
Não reler desnecessariamente todos os ZIPs depois de cada membro. O cache opcional
de hashes usa a identidade local do arquivo; não equivale a recalcular seus bytes
e bloqueia prontidão pública. Isso detecta mudanças observáveis; não oferece
snapshot contra autor hostil restaurando bytes/mtime entre leituras. CRC verifica
corrupção, não autenticidade. Detalhes no [guia nacional](NATIONAL_IMPORT.md).

Referências são objetos por caminho relativo do ZIP com `algorithm` (sha256 ou
sha512), `digest` hexadecimal completo, `origin` e `trusted` booleano. Confiança
é declaração do operador após consultar a origem, nunca inferida pelo nome.
Auxiliar `.zip.sha512` aceita linha GNU `digest  nome.zip` ou marcador `*`;
nome/algoritmo/comprimento precisam corresponder. `checksum_line` também aceita
SHA-256. Formatos desconhecidos não são adivinhados.

`source_metadata` é objeto por caminho relativo, com campos textuais opcionais
`source_url`, `catalog_url`, `consulted_at`, `license_label` e `attribution`.
Registrar apenas metadados efetivamente consultados; o motor não os inventa.

| Estado | Significado |
| --- | --- |
| verified | Bytes coincidem com referência declarada confiável |
| mismatch | Digest diverge da referência |
| unverified | Referência ausente/sem confiança suficiente, mesmo com auxiliar coincidente |
| unsupported | Algoritmo/formato não interpretado |
| error | Falha de leitura/cálculo; fonte recusada |

Mismatch, unsupported e erros bloqueiam importação. Sem referência, permitir
derivado com hashes não conferidos; `require_verified` bloqueia esse caso. Validação
matemática/estrutural é distinta da confiança nos bytes. Hash não é assinatura.

## Reconciliação e qualidade

Chave: `(CD_ELEICAO, SG_UF, CD_MUNICIPIO, NR_ZONA, NR_SECAO)`; resultado acrescenta
`NR_VOTAVEL`. Eleição preserva seu turno original. Contexto BWEB é digest dos
identificadores publicados de urna/carga, emissão/recepção, tipo e seções agregadas.
É identificador interno de contexto, sem alegar identificar equipamento físico.

Preferir votação por seção quando presente na localidade. Sem ela, BWEB exige
contexto único. Não somar fontes/contextos nem expandir seções agregadas. Contextos
concorrentes geram alerta e impedem conferência; sem alternativa inequívoca,
bloquear publicação. Duplicatas dentro do contexto ou fontes primárias concorrentes
são fatais. Diferenças não recebem explicação inventada.

Comparar presença dos votáveis, votos e local quando há BU único. Conjuntos de
linhas completos iguais recebem comparison=matched por seção. Diferenças de
votos/local e matemática BU bloqueiam publicação. Linhas exclusivas de uma fonte
são not_verifiable, relatadas sem forçar correspondência. Isso permite coberturas
diferentes sem fingir uma conferência nacional.

Verificar, quando possível: votos presidenciais somados = comparecimento;
aptos = comparecimento + abstenções; estabilidade dos totais no contexto;
integridade SQLite/foreign keys/unicidade; totais por categoria/seção, agregações
e vínculo de eleição do candidato. Nominal não certifica situação jurídica.

`divergences-summary.json` contém contagens exatas por UF/turno e código.
Ausência de fonte BWEB fica agregada; ausência de seção/votável, diferença de
votos/local, ambiguidade e matemática possuem códigos separados.
`divergences.jsonl` contém detalhe limitado, com registros, fontes e linhas.
Limite padrão: 8 MiB; truncamento e contagem omitida ficam explícitos no resumo.
Severidades: fatal/interrupção, divergence/diferença, warning/ambiguidade,
not_verifiable/cobertura insuficiente; informações de sucesso/cobertura ficam em
validation.json. Registros inválidos não são descartados silenciosamente.

## SQLite, schema 1 e contrato futuro

`PRAGMA user_version=1`. Tabelas: metadata (versões/configuração/natureza), sources
(ZIP/membro/hash/referência), elections (código/ano/turno/cargo), sections
(hierarquia original), candidates (eleição/número/sequencial/nome/categoria),
results (votos/fonte/linha), section_totals (totais disponíveis/BU/estado),
aggregates (eleição/UF/candidato/seções com registro). IDs inteiros são locais;
códigos originais continuam texto. Não há tabela de equipamento físico.

Índice único de seção atende UF → município → zona → seção; chave de results
atende seção; results_candidate atende votável; aggregates_scope atende
UF/nacional. Agregações municipais/zonais consultam os resultados indexados,
evitando replicar votos em todas as hierarquias. [Consultas SQL](data_queries.sql).

O adaptador Flutter futuro deverá traduzir para ElectionDataset/RoundResult,
validar cobertura/denominadores/proveniência e representar totais indisponíveis:
o domínio M1 hoje exige totais não nulos. Exterior precisa de inclusão explícita
nos agregados; não pertence ao mock nacional. Nenhuma alteração Flutter nesta missão.

## Publicação local, retomada e limpeza

```text
output/
  .import.lock
  .runs/<run-id>.json
  .work/<run-id>/checkpoints/<hash>.sqlite + <hash>.json
                   staging/
                   tmp/
  releases/<release>/election.sqlite
                     manifest.json
                     validation.json
                     divergences.jsonl
                     divergences-summary.json
  current.json
```

Lock exclusivo impede escritores simultâneos. Após queda abrupta, confirmar
ausência de processo ativo antes de remover somente `.import.lock`. Ctrl+C fecha
conexões, retira lock e preserva versão anterior. `.partial` nunca é reutilizado.
Unidade completa usa hash da fonte/membro/configuração/schema/versão/código e hash
do checkpoint SQLite. Retenção é explícita (`retain_checkpoints: true`); o padrão
elimina bancos intermediários após sucesso/falha. Retomada só reutiliza unidades
completas com registro de propriedade, hash e marcador válidos; checkpoints M2
antigos ficam intactos e não são adotados. Corrupção reinicia aquela unidade. `--no-resume` reprocessa
unidades, mas release já concluída e íntegra continua idempotente.

Consolidar por UF/turno em staging, fechar transações, recuperar páginas livres
com incremental_vacuum sem criar cópia integral do banco, validar, calcular
hashes finais, escrever relatórios/manifesto, mover diretório e trocar current.json
atomicamente no mesmo volume. Não sobrescrever release. Falha preserva diagnóstico
e ponteiro anterior; não há deploy. Queda de energia/disco depende das garantias
do SO/SQLite/filesystem. Limpeza automática restrita aos arquivos desta execução
com identidade confirmada; nenhuma limpeza recursiva genérica. Arquivos desconhecidos,
originais e releases anteriores são preservados. Política e métricas de disco:
[NATIONAL_IMPORT.md](NATIONAL_IMPORT.md).

Manifesto: versões/schema/digest de regras, seleção/cobertura, origem local,
hashes/referências/confiança, contagens, data de processamento UTC, natureza
oficial/sintética declarada, limitações, atribuição, hashes dos quatro artefatos
finais. URLs/datas de consulta realmente conhecidas ficam nas referências e no
relatório investigativo. SQLite é determinístico para fontes/opções/regras iguais
no mesmo runtime e representação de código (inclusive finais de linha);
datas, tempo e RSS dos relatórios variam. Não se promete manifesto byte a byte
igual após reconstrução. Assinatura futura exige serialização canônica, chave
protegida e identificada, algoritmo público e política de rotação/revogação;
nenhuma assinatura foi simulada.

## Testes

```powershell
python -m ruff format --check pipelines/tse_importer apps/votoaberto_auditor tests
python -m ruff check pipelines/tse_importer apps/votoaberto_auditor tests
python -m pytest -q
$env:TSE_REAL_INPUT = "D:\MODELOS_TSE"
# Opcional: configuração com saída persistente e referências consultadas
$env:TSE_REAL_CONFIG = "D:\config\sc-2026.json"
python -m pytest -q -m official
```

Sem TSE_REAL_INPUT e TSE_REAL_CONFIG, pular teste oficial. Fixtures gerados são fictícios, usam
layouts observados, DF/ZZ/zeros, casos negativos e volume de 20.000 registros.
CI separado faz instalação/CLI/formato/lint/testes no Ubuntu e Windows,
Python 3.11/3.12, sem baixar TSE. Flutter CI fica preservado. Configuração de CI
Linux não comprova execução Linux desta revisão; consulte o relatório de evidências.

## Avaliação v2 — integridade, cobertura e publicação

A avaliação introduzida no importador 0.2.1 continua na versão 0.3.1, mantendo
schema SQLite 1 e `assessment_version: 2` no manifesto/relatório. Não há booleano
global `valid` para datasets novos. Consumidores
do JSON 0.2.0 precisam migrar: `coverage` tabular passou a `observed_coverage`;
`assessment.coverage` contém o contrato de cobertura. O resumo histórico de SC
permanece inalterado. Releases 0.2.0/schema 1 podem ser reavaliadas sem reescrita:
as garantias novas são calculadas a partir do banco e das evidências retidas.

| Dimensão em assessment | Estados e alcance |
| --- | --- |
| sqlite_integrity | passed/failed; PRAGMA integrity_check |
| referential_integrity | passed/failed; foreign keys e eleição do candidato |
| mathematics | passed/partially_checked/failed; somas e identidades disponíveis, contando seções com totais indisponíveis |
| coverage | observed_only/complete/incomplete; presença dos pares UF/ZZ × turno explicitamente declarados |
| source_hashes | matched_operator_trusted, partially_matched_operator_trusted, matched_without_assigned_trust, unverified ou failed |
| reconciliation | complete/partial/not_verifiable/divergent/not_assessed; linhas e pares seção/turno confrontados |
| local_release | eligible/blocked com motivos; permite uma investigação parcial legítima |
| public_readiness | ready_for_declared_scope/not_ready com motivos; nunca significa cobertura nacional implícita |

`structurally_valid` resume estrutura não vazia, integridade física e vínculos;
não inclui sucesso matemático, cobertura, hashes ou reconciliação. Um SQLite
estruturalmente íntegro com somas erradas apresenta mathematics=failed e é recusado.
`data_nature` é synthetic ou official-derived, separado da confiança dos hashes.
Ausência de totais mantém matemática parcialmente conferida, mesmo quando não há
divergência nas somas conhecidas. A fonte nacional de SC continua sem referência
oficial suficiente; isso não invalida a estrutura do SQLite.

Uma release local é bloqueada por erros do banco/matemática, divergências confirmadas,
falha de hash/referência, cobertura exigida ausente ou falta de confiança exigida
por require_verified. Linhas sem BU/contextos ambíguos continuam permitidos quando
há fonte primária inequívoca, com reconciliação parcial/não verificável.

Prontidão pública exige cumulativamente: critérios locais, natureza official-derived
declarada, cobertura territorial explícita satisfeita, comparação de todos os hashes
com referências de confiança atribuída pelo operador, reconciliação completa e
matemática disponível conferida. É prontidão técnica **no recorte declarado**,
sem atestar licença, origem criptográfica ou integridade eleitoral; nenhum deploy
é executado. current.json aponta uma release local, podendo estar publicamente
not_ready. Um SQLite isolado informa public_readiness=not_assessed; use a release
para avaliar catálogo e evidências de reconciliação.

Código de saída 0 de validate significa elegibilidade local sob o contrato
registrado (ou controles conhecidos do SQLite isolado); não afirma prontidão
pública. Uma automação de distribuição deve examinar public_readiness e seu
scope, mesmo após sucesso do comando.

validate recalcula estrutura, matemática e cobertura observada; fontes não são
relidas nesse comando. source_hashes.evidence=retained_catalog_no_source_reread e
reconciliation.evidence=retained_report_and_database deixam isso explícito.
Na importação, as evidências vêm dos streams e hashes correntes. report separa
import_report de current_validation, inclusive para releases históricas.

## Exigir cobertura sem alterar os filtros

ALL permanece um filtro para as abrangências disponíveis. Exigências de saída são
independentes e podem ser declaradas em JSON:

```json
"coverage_requirements": {
  "territories": ["SC", "DF", "ZZ"],
  "rounds": [1, 2]
}
```

Isso exige os seis pares. NATIONAL expande para as 27 UFs e ZZ; com dois turnos,
são 56 pares. O [exemplo nacional](../config/national-2026.example.json) permite
análise local sem checksum oficial de todos os arquivos, mantendo public_readiness
conservador. Exige projeção de disco fundamentada em piloto antes da carga oficial
NATIONAL; o valor 0 do exemplo indica projeção ainda não feita.

```powershell
votoaberto-auditor import --input "D:\TSE" --output data/processed/national --require-territory NATIONAL --require-round 1 --require-round 2
```

Flags `--require-territory`/`--require-round` substituem os campos correspondentes
do JSON. Filtros que excluem territórios/turnos exigidos são recusados. Sem exigência
territorial explícita, uma seleção de UFs exige essas UFs nos turnos selecionados;
ALL informa observed_only. Um contrato adicional define o recorte mínimo exigido;
as observações adicionais continuam registradas. Turnos selecionados precisam
ter dados. Pares ausentes impedem promoção local e preservam releases anteriores.

coverage.scope=territory_round_presence não comprova presença de todas as seções
eleitorais: section_completeness permanece not_assessed sem inventário independente.
Mesmo NATIONAL completo não autoriza anunciar conferência exaustiva por seção.

## Confiança atribuída pelo operador

`trusted: true` é uma declaração do operador sobre a referência. URL HTTPS, domínio
oficial ou coincidência SHA não autenticam automaticamente sua origem no motor.
O nome legado verified em cada fonte significa exclusivamente digest coincidente
sob essa declaração; acompanha status_scope e reference_trust=operator_declared.
O agregado usa matched_operator_trusted para explicitar o limite. trusted=false
com digest coincidente informa match sem confiança atribuída. Sempre são registrados
origin_authentication=not_performed e signature_verification=not_performed.
SHA-256/SHA-512 não são assinaturas digitais. As consultas de referência efetivamente
feitas para SC continuam registradas na investigação original.

## Caminhos do teste oficial

O teste é habilitado com qualquer uma das duas variáveis:

1. TSE_REAL_CONFIG aponta o JSON; caminhos relativos nele são resolvidos contra
   a pasta do JSON, inclusive output_dir.
2. TSE_REAL_INPUT, quando definido, **substitui** input_dir do JSON e é resolvido
   contra o diretório de execução. Caminho inexistente falha, sem fallback ao JSON.
3. Com apenas TSE_REAL_CONFIG, usar input_dir do JSON. Com apenas TSE_REAL_INPUT,
   usar seleção SC/dois turnos e saída temporária do pytest. Sem ambos, pular.

A resolução reutiliza import_config da CLI: variáveis são interpretadas somente
pelo adaptador do teste oficial, não automaticamente pela CLI. Configuração
oficial deve selecionar SC e ambos os turnos; output_dir do JSON é preservado.

Durante a revisão local foram observadas negações intermitentes de acesso na
renomeação de staging no Windows. A promoção continua os.replace atômico, com
até seis tentativas apenas para WinError 5/32/33 (espera total máxima de 1,55 s).
Erro persistente é propagado, destino existente não é sobrescrito e o ponteiro
anterior permanece. Não foi atribuída uma causa específica ao bloqueio observado.
