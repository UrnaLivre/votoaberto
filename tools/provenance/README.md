# Coleta incremental de referências oficiais

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
