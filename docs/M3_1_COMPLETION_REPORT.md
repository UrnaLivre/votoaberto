# Conclusão M3.1 — primeira base presidencial nacional local

Concluído em 29/10/2026: importação presidencial dos arquivos fornecidos para os
dois turnos, com 27 UFs + ZZ, **56 pares observados e 5.731.614 resultados**.
Todos os resultados correspondem entre votação por seção e BWEB; a validação
estrutural, matemática e referencial passou. A base é **elegível para análise
local**, com **prontidão pública `not_ready`**. Não houve publicação remota.

## Git, implementação e arquitetura

- Branch única desta entrega: `feat/m3-national-presidential-data`.
- Base, após fetch e conferência inicial da main limpa:
  `d27712b338344a9baecc03e8bb78237b9f0e3e6e`, merge do PR #2/M2.
- Implementação: `0760cefc53d0406672afaf83c7fa8bdc99e3f8b5`
  (`feat(data): bound disk usage and consolidate presidential partitions`).
- Reforço de caminhos: `3e030df5b3d94e516e3b04ecd48ea02438d366c2`
  (`fix(data): reject drive-relative work directories`).
- O commit documental final deve ser identificado por `git log -1`; seu próprio
  SHA não é embutido neste arquivo para evitar autorreferência.

Não houve merge ou conflito nesta etapa: o M2 já estava integrado à main.
As decisões da ADR 0003 foram preservadas: motor compartilhado, Auditor local,
SQLite público compacto, BUs usados como conferência, Flutter com mock.
Não foram criadas branches auxiliares, feito push, aberto PR, excluída branch
ou reescrito histórico. Ao encerrar, os arquivos desta entrega são commitados;
artefatos locais continuam ignorados.

O motor 0.3.1 mantém schema SQLite 1 e avaliação 2. `workspace.py` controla UUID,
propriedade/identidade, orçamento de 8 GiB, reserva de 15 GiB, TEMP somente do
processo e limpeza restrita. `partitioned.py` mantém uma unidade primária indexada,
processa BWEB/partição UF-turno sequencialmente, incorpora e descarta intermediários.
`planning.py` exige projeção fundamentada antes da carga oficial NATIONAL.
`reporting.py` agrega contadores exatos e limita detalhes, explicitando truncamento.
Hash em cache tem evidência distinta e impede prontidão pública. Não há quota
rígida do SO; métricas e limitações constam do guia operacional.

Arquivos alterados/adicionados em relação à base:

- `.github/workflows/data-engine.yml`
- `README.md`
- `apps/votoaberto_auditor/README.md`
- `apps/votoaberto_auditor/votoaberto_auditor/cli.py`
- `config/national-2026.example.json`
- `docs/ARCHITECTURE.md`
- `docs/DATA_ARCHITECTURE.md`
- `docs/DATA_ENGINE_OPERATIONS.md`
- `docs/M3_1_COMPLETION_REPORT.md`
- `docs/NATIONAL_IMPORT.md`
- `docs/ROADMAP.md`
- `docs/TSE_2026_NATIONAL_INVESTIGATION.md`
- `docs/TSE_2026_NATIONAL_SOURCE_INVENTORY.json`
- `docs/TSE_2026_NATIONAL_VALIDATION_SUMMARY.json`
- `pipelines/tse_importer/__init__.py`
- `pipelines/tse_importer/assessment.py`
- `pipelines/tse_importer/discovery.py`
- `pipelines/tse_importer/domain.py`
- `pipelines/tse_importer/engine.py`
- `pipelines/tse_importer/parsers.py`
- `pipelines/tse_importer/partitioned.py`
- `pipelines/tse_importer/planning.py`
- `pipelines/tse_importer/reporting.py`
- `pipelines/tse_importer/storage.py`
- `pipelines/tse_importer/validation.py`
- `pipelines/tse_importer/workspace.py`
- `pyproject.toml`
- `tests/test_assessment.py`
- `tests/test_engine.py`
- `tests/test_storage_policy.py`

## Fontes, formatos e reprodução

Foram encontrados 57 ZIPs: 56 BWEBs e um nacional de votação por seção, além de
56 auxiliares SHA-512. A organização real possui subpastas por turno/UF e votação
por seção. Nenhuma duplicata de bytes ou par territorial ausente foi encontrada
no conjunto atualizado. Os 56 BWEBs coincidem com seus auxiliares; duas referências
SC têm confiança atribuída pelo operador, as demais permanecem sem essa atribuição.
O nacional continua sem checksum oficial identificado. SHA não é assinatura.

Nove ZIPs iniciais não tinham índice ZIP final e divergiam dos auxiliares; o
operador repôs ES/GO/MG/MS/MT/PA/PB/PE/PI do primeiro turno. O motor não alterou
originais nem fez downloads. PA atual tem 172.050.487 bytes; SHA-512:
`7ec84395ef9ce10fcfeedc9236b9fb93de80d7d278b56b074d0538009ed53e4fff695a627dd848028e91ef8cd1a5a36a1e6fe2318b0adac909c741739371d788`.
Os auxiliares permaneceram idênticos entre os snapshots. Não se concluiu o que
mudou no conteúdo remoto nem foram comparados backups, conforme adiamento solicitado.
Ao final, os fingerprints dos 113 arquivos coincidiram com o catálogo de hashes
usado na carga. Essa conferência de metadados não foi uma nova leitura criptográfica.

São suportados os CSVs observados: BWEB/45 campos, seção/26 campos, Latin-1,
`;`, cargo presidencial 1, dois turnos e categorias nominais/branco/nulo.
Os 57 CSVs foram lidos integralmente com CRC; 57 PDFs auxiliares tiveram CRC
conferido, sem parser eleitoral. Layouts desconhecidos, tipo 97 e situações
presidenciais não interpretadas são recusados. Não há descarte silencioso.
Foram selecionadas 5.731.614 linhas por fonte; 64.215.467 linhas BWEB de outros
cargos foram contadas e filtradas; quarentena zero pela política estrita.

O [inventário versionado](TSE_2026_NATIONAL_SOURCE_INVENTORY.json) traz nomes,
tamanhos, membros, SHA-256/SHA-512, referências e diferenças dos snapshots.
O [guia nacional](NATIONAL_IMPORT.md) descreve configuração, comandos, retomada,
consultas, orçamento, limpeza e confiança. Configuração efetiva, catálogos e
evidências integrais locais estão em `.local/m31-*`, fora do Git.

## Base e validação dos dados

Release única ativa:
`data/processed/national-2026/releases/6305f74561d4687a23bd3054/`.
`current.json` aponta para ela. O SQLite contém 2 eleições, 998.411 pares seção-turno,
19 registros de candidatos/categorias vinculados às eleições (15 no turno 1 e
4 no turno 2), 5.731.614 resultados, 998.411 totais de seção,
532 agregados e 57 fontes eleitorais. Todos os resultados públicos provêm do CSV
de votação por seção; BWEB conferiu/complementou os totais permitidos, sem somar
votos das duas fontes nem copiar BUs completos.

| Indicador nacional, incluindo ZZ | Turno 1 | Turno 2 |
| --- | ---: | ---: |
| Seções observadas | 499.206 | 499.205 |
| Resultados presidenciais | 3.800.511 | 1.931.103 |
| Votos nominais | 119.306.034 | 124.082.273 |
| Brancos | 2.300.798 | 1.430.496 |
| Nulos | 3.669.003 | 2.723.305 |
| Contabilizados / comparecimento | 125.275.835 | 128.236.074 |
| Aptos disponíveis | 158.745.007 | 158.744.977 |
| Abstenção disponível | 33.469.172 | 30.508.903 |
| Seções sem totais BU completos | 0 | 0 |

A [investigação nacional](TSE_2026_NATIONAL_INVESTIGATION.md) contém a matriz de
seções, municípios, zonas e reconciliação para cada um dos 56 pares, os votos por
candidato e as diferenças observadas entre UFs/turnos. O
[resumo JSON](TSE_2026_NATIONAL_VALIDATION_SUMMARY.json) inclui candidatos por
UF/turno, sentinelas, gerações, agregações indicadas, origens e avaliações.
Municípios de ZZ são códigos da fonte; zonas são códigos distintos dentro da
abrangência, e pares município/zona aparecem separadamente. Não há expansão
artificial de seções agregadas ou correspondência presumida com equipamentos.

SQLite `integrity_check=ok`, foreign keys sem erros, erros matemáticos,
agregados, categorias e vínculos: zero. Reconciliação: 5.731.614 linhas matched,
zero diferenças/exclusivas/ambiguidades/erros matemáticos BWEB. A comparação de
locais passou. A validação independente pós-carga levou 48.096 s
e confirmou os votos e contagens históricos de SC. Seus documentos M2 foram
preservados. Presença dos 56 pares não demonstra completude de todas as seções:
`section_completeness=not_assessed`, sem inventário externo exaustivo.

Hashes dos quatro artefatos constam do manifesto. SHA-256 do SQLite:
`c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4`.

| Arquivo da release | Bytes lógicos |
| --- | ---: |
| `divergences-summary.json` | 598 |
| `divergences.jsonl` | 0 |
| `election.sqlite` | 935.424.000 |
| `manifest.json` | 299.094 |
| `validation.json` | 347.647 |

## Recursos, limpeza e remanescentes

| Medida | Valor |
| --- | ---: |
| Livre no inventário inicial, antes do processamento | 444.714.639.360 bytes |
| Livre ao iniciar a carga nacional | 443.895.771.136 bytes |
| Projeção calculada / configurada | 6.584.854.964 / 7.516.192.768 bytes |
| Orçamento / reserva mínima | 8.589.934.592 / 16.106.127.360 bytes |
| Pico contabilizado conservador da carga | 2.879.172.608 bytes (2,68 GiB) |
| Pico de arquivos visíveis | 2.466.150.529 bytes |
| Pico da área de trabalho | 2.466.053.716 bytes |
| Menor espaço livre observado | 441.016.598.528 bytes |
| Pico de journals amostrado | 16.376.128 bytes |
| Checkpoint primário, máximo por arquivo | 826.728.448 bytes |
| Maior checkpoint BWEB, SP/1 | 339.599.360 bytes |
| Maior partição, SP/1 | 639.344.640 bytes |
| Maior temporário SQLite observado | 233.020.371 bytes |
| SQLite final | 935.424.000 bytes |
| Saída canônica total no inventário final | 936.423.406 bytes |
| Área de trabalho da carga concluída | 0 bytes |
| Checkpoints/SQLite intermediários remanescentes | 0 bytes |
| Limpeza explícita da carga | 171 arquivos / 4.064.248.602 bytes |
| Temporários SQLite observados e já liberados pelo SQLite | 328 |
| Limpeza adicional dos pilotos AC/SC | 12 arquivos / 34.350.120 bytes |
| Limpeza dos testes desta missão | 3107 arquivos / 82.794.714 bytes |
| Livre no inventário final | 442.267.017.216 bytes |
| CSVs descompactados lidos até EOF | 33.996.632.666 bytes |
| Importador até relatório inicial | 4.834,033 s |
| Parsing / consolidação / validação inicial | 3.564,457 / 1.211,581 / 38,2 s |
| Comando com fechamento e revalidação do wrapper | 4.914,729 s (81,91 min) |
| Pico RSS, Windows PeakWorkingSetSize | 87.543.808 bytes (83,49 MiB) |
| Pós-validação: pico contabilizado / temporários SQLite | 246.263.808 bytes / 15 |

A área `.work/2e537ead4adc4e3488ceef0e0148529a/` da carga concluída foi removida.
Resta **somente** `.work/b6f65db330d144d5a73b697b297b3d54/inventory.json`
na saída canônica: 149.079 bytes do preflight inicialmente recusado, preservados
por `retain_failed_diagnostics=true`. Não contém SQLite. Os dois registros
`.runs/` somam 202.890 bytes; ponteiro tem 98 bytes. As pastas vazias de controle
não representam cópias da base. Fora da saída, os pilotos e pós-validação retêm
somente registros de execução, sem `.work`, releases ou checkpoints.

O inventário local final lista 4.881.833 bytes em evidências/scripts
`.local/m31*` na fotografia anterior à gravação do próprio inventário final;
o relatório `.local/m31-storage-after.json` e o presente gerador são adicionais
pequenos. Não restam diretórios `pytest-m31-*`. O levantamento final confirmou
os tamanhos lógicos dos grupos preexistentes inalterados. Inventários/recibos:
`.local/m31-storage-before.json`, `.local/m31-storage-after.json`,
`.local/m31-pilot-cleanup.json`, `.local/m31-test-cleanup.json`.

Os bytes recuperados são soma de comprimentos lógicos dos arquivos explicitamente
removidos ao longo da execução, não ganho simultâneo nem delta físico do volume.
SQLite libera seus próprios temporários separadamente. Máximos por arquivo não
devem ser somados como pico. O monitor usa 100 ms, callbacks SQL/lotes e margem;
atividade externa pode inflar ou mascarar o delta do volume. Não há quota rígida
do SO ou garantia absoluta. Temporários do wrapper de revalidação não foram
medidos individualmente; a pós-validação adicional mediu seus temporários em
área controlada. Não foi criado SQLite comprimido, nem repetida a carga nacional
para benchmark. Houve apenas um preflight recusado antes da única carga completa.

Candidatos anteriores à limpeza, **todos preservados**, com potencial bruto de
1.632.924.446 bytes; incluem releases ativas e não são todos descartáveis:

| Caminho relativo ao repositório | Bytes potenciais brutos |
| --- | ---: |
| `data/processed/sc-2026` | 812.529.200 |
| `data/processed/sc-2026-review` | 580.681.064 |
| `.local/pytest-assessment-1` | 16.807.295 |
| `.local/pytest-assessment-2` | 18.046.693 |
| `.local/pytest-assessment-3` | 18.046.607 |
| `.local/pytest-assessment-4` | 18.389.626 |
| `.local/pytest-assessment-5` | 18.389.725 |
| `.local/pytest-m2-1` | 14.982.729 |
| `.local/pytest-m2-2` | 15.087.121 |
| `.local/pytest-m2-3` | 16.329.516 |
| `.local/pytest-m2-4` | 16.590.491 |
| `.local/pytest-m2-5` | 16.709.538 |
| `.local/pytest-m2-final` | 16.710.686 |
| `.local/pytest-m2-review-final` | 18.389.736 |
| `.local/pytest-m2-review-real` | 18.389.736 |
| `.local/pytest-merge-baseline` | 16.710.601 |
| `.local/pytest-merge-isolated` | 134.082 |
| `.local/pytest-official-m2-1` | 0 |

`sc-2026` tinha 3 releases válidas (1 ativa) e 9 checkpoints; `sc-2026-review`
tinha 2 releases válidas (1 ativa) e 6 checkpoints. Não havia lock ou `.partial`
nesses grupos. Checkpoints antigos requerem compatibilidade de fontes/regras e
não são adotados pelo M3. Remoção futura exige autorização específica; nenhuma
limpeza anterior, de ZIP original ou backup foi feita.

## Testes, CI e prontidão para PR

Ambiente local: Windows, Python 3.12.10, SQLite 3.49.1.

- `python -m ruff format --check pipelines/tse_importer apps/votoaberto_auditor tests`:
  21 arquivos formatados.
- `python -m ruff check pipelines/tse_importer apps/votoaberto_auditor tests`: passou.
- `python -m pytest -q --basetemp .local/pytest-m31-head`: **91 passed, 2 skipped,
  53,90 s**. Exclusões: integração oficial optativa e symlink sem permissão Windows.
- Integração oficial SC optativa executada nesta missão: **1 passed, 81 deselected,
  92,58 s**, antes do reforço administrativo de caminhos; os parsers da carga
  nacional são os mesmos. Pilotos AC/2 e SC e carga nacional validaram dados reais.
- Regressões cobrem orçamento/reserva, limite de temporário, sucesso/falha/Ctrl+C,
  falha de promoção, originais/releases anteriores, arquivos desconhecidos/trocados,
  checkpoints completos/obsoletos, resumo/truncamento, BWEB parcial/ausente,
  NATIONAL/ALL, cache de hashes e precedência CLI/configuração.
- `votoaberto-auditor --help`, `python -m pip check` e `git diff --check`: passaram.
- `validate_release` foi executado na promoção, pelo wrapper e na pós-validação
  independente, verificando hashes dos artefatos e banco somente leitura.

CI disponível da main:
[`40925676557`](https://github.com/UrnaLivre/votoaberto/actions/runs/40925676557),
SHA `d27712b338344a9baecc03e8bb78237b9f0e3e6e`, passou nos quatro jobs
Windows/Linux × Python 3.11/3.12. **Não é CI desta branch**: não houve push.
O workflow foi mantido com fixtures pequenos e sem arquivos TSE. O próximo PR
deverá executar essa matriz para os novos commits e passar por revisão independente.

O trabalho está pronto para abrir PR de código/documentação após autorização
do operador, sujeito ao CI e à revisão. Isso não autoriza distribuição pública
da base: `source_hashes_reused_from_local_cache` e
`operator_trusted_hashes_incomplete` mantêm `public_readiness=not_ready`.
A ausência de checksum nacional e a confiança não atribuída aos demais auxiliares
estão registradas; nenhuma política foi relaxada para obter um estado pronto.

Permanecem limites: contagem esperada de todas as seções indisponível; autenticação
da origem/assinatura não realizada; comparação dos backups adiada; layouts novos
e BWEBs separados com UF/turno sobreposto recusados; retomada apenas por unidade
completa. Próximos trabalhos: revisão independente/CI da branch, política de
proveniência/publicação, investigação de formatos adicionais, otimização de I/O
e quotas do SO. Integração Flutter e distribuição exigem marco próprio.
