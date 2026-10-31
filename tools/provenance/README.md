# Coleta incremental de referências oficiais

## Reavaliação M6.1, sem importação

`rehash_local.py` lê cada ZIP uma vez para os dois algoritmos e escreve um relatório
novo, sem rede/extração. `prepare_release.py` valida o banco existente, vincula as
evidências, aplica a [política](../../docs/DATA_PROVENANCE_POLICY.md), compara os
JSONs ao SQLite e cria somente uma nova release de metadados em outra saída.

```powershell
python tools/provenance/rehash_local.py --manifest data/processed/national-2026/releases/6305f74561d4687a23bd3054/manifest.json --references docs/WEB_DATA_SOURCE_EVIDENCE.json --report docs/WEB_DATA_CURRENT_HASHES.json
python tools/provenance/prepare_release.py --national data/processed/national-2026/releases/6305f74561d4687a23bd3054 --embedded data/processed/embedded-presidential-2026/releases/e4e9c9cb5189ab5d4e124bfc --references docs/WEB_DATA_SOURCE_EVIDENCE.json --hashes docs/WEB_DATA_CURRENT_HASHES.json --testimony docs/WEB_DATA_ACQUISITION_TESTIMONY.json --output data/processed/embedded-public-2026
```

Esses destinos já existem após M6.1; não sobrescrevê-los nem repetir o hash dos
ZIPs para apenas rever o candidato. Conferir o candidato existente com
`validate_embedded`/`web_release.py preflight`. Uma nova execução deve usar destinos
novos para preservar evidências. A instalação de metadados é explícita pelo
`--install-to` ou API `install_metadata`: confere que todos os artefatos eleitorais
instalados são idênticos e só substitui manifesto/adiciona o dossiê. Preserva
`.gitkeep`, rejeita mistura e restaura metadados em falha, sem sobrescrever edição
concorrente detectada. Não instala uma aprovação.

O dossiê é autocontido: bytes dos manifestos/relatório de origem, fotografia M6,
testemunho, recálculo e validação. Contém inventário técnico e caminhos históricos,
sem ZIPs, SQLite ou dump de registros por seção. A revisão humana deve considerar
esse conteúdo exato, cujo hash é vinculado à aprovação.

## Coletor de metadados M6

```powershell
python tools/provenance/review_sources.py --manifest data/processed/national-2026/releases/6305f74561d4687a23bd3054/manifest.json --report .local/m6/new-source-review.json --http-cache .local/m6/http
```

Requer Python 3.11+, biblioteca padrão e acesso HTTPS ao TSE. Consulta os dois
catálogos CKAN e, para cada ZIP existente no manifesto, somente referências
`.sha512`/`.sha256`. Nunca abre os ZIPs locais, baixa ZIPs, extrai membros,
importa votos, escreve releases ou atribui confiança ao operador.

São três consultas simultâneas por padrão (máximo quatro), timeout de 15 segundos
por operação de rede e no máximo duas tentativas por requisição. Checksums têm
limite de 4 KiB e catálogos de 2 MiB. HTTPS usa a cadeia de certificados padrão
da plataforma. Redirecionamentos para ZIPs ou fora dos hosts oficiais são recusados.
O nome exato do arquivo deve constar na linha de checksum; algoritmo, tamanho e
formato são conferidos. MIME `application/zip` não transforma um checksum textual
de 158 bytes em um arquivo de votos: a validação examina seu conteúdo limitado.

O relatório relaciona referência nova, digest histórico, comparação, fingerprint
local, consulta HTTP, metadados e declaração anterior de confiança. Referências
propostas sempre têm `trusted: false`. Fingerprint coincidente não equivale a
recalcular os bytes locais. Uma referência nova que coincide com um digest retido
não remove automaticamente o blocker de cache do avaliador vigente.

Entradas duplicadas com a mesma URL preservam seus aliases. URLs distintas para
o mesmo nome são ambíguas e interrompem a coleta. Se apenas o checksum estiver
no catálogo, a URL inferida do ZIP fica explicitamente marcada; isso não afirma
que o ZIP foi consultado. RR/segundo turno foi esse caso na revisão M6.

O relatório existente nunca é sobrescrito. `--http-cache` guarda apenas os corpos
pequenos recebidos por SHA-256, para inspeção local. A coleta não usa esse cache
como substituto de uma consulta de rede nova. Registre o relatório original ao
consolidar tentativas posteriores; não apague indisponibilidades anteriores.

Saídas: `0` coleta concluída, inclusive com referências indisponíveis; `1` digest
divergente; `2` erro de coleta/configuração. Sucesso da coleta não significa
prontidão pública, aprovação humana nem autorização de deploy. Os mecanismos
`validate_release` e `web_release.py preflight` continuam sendo obrigatórios.

Testes offline: `python -m pytest -q tests/test_provenance_review.py`.
Evidência observada: [revisão M6](../../docs/WEB_DATA_PROVENANCE_REVIEW.md).
