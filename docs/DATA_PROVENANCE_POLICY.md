# Política de proveniência documentada de derivados presidenciais — v1

Identificador executável: `tse-presidential-documented-provenance-1`.
Implementação: `pipelines/tse_importer/provenance.py`. Proposta submetida à
aprovação formal do operador; implementada para avaliar elegibilidade técnica.
Não representa uma aprovação de publicação, redistribuição ou legitimidade eleitoral.

## Escopo e fundamento

A ausência de checksum publicado não é evidência de adulteração. Um fornecedor
pode oferecer um produto em catálogo oficial sem oferecer assinatura ou hash.
A política separa a integridade dos bytes, a documentação de origem e a
reconciliação de conteúdo. Não fabrica uma referência independente para preencher
essa ausência nem torna uma assinatura inexistente condição obrigatória.

Aplica-se a resultados **presidenciais derivados**, no ano, turnos e territórios
declarados. Usa linhagem TSE nos formatos `bweb` e `section` já importados.
Não abrange outros cargos, cada byte não selecionado dos arquivos ou identificação
física de equipamentos. É reutilizável em futuras eleições com os mesmos tipos de
evidência; não contém dataset ID, ano, UF ou quantidade de fontes de 2026 como
exceção. Os parsers de ingestão continuam limitados aos leiautes habilitados:
a política não habilita importação de uma eleição futura por si só.

## Critérios cumulativos

1. **Linhagem imutável:** manifesto nacional, relatório de importação/reconciliação
   e manifesto compacto de origem são preservados. Seus bytes e hashes ficam
   vinculados ao dossiê. O SHA-256 do relatório deve corresponder ao artefato do
   manifesto nacional; o compacto deve apontar a mesma release e o mesmo SQLite.
2. **Integridade local atual de todas as fontes:** uma leitura sequencial de cada
   ZIP calcula SHA-256 e SHA-512 juntos. Registra bytes efetivamente lidos,
   caminho relativo, horários e estabilidade do arquivo durante a leitura.
   Ambos os digests e tamanho devem coincidir com os históricos vinculados à
   importação. Fingerprint isolado não satisfaz este critério. Divergência,
   arquivo ausente, fonte extra/duplicada ou leitura incompleta impede promoção.
3. **Referências externas disponíveis:** para BWEB, esta versão exige o SHA-512
   textual oficial, com nome exato do ZIP, recurso de catálogo identificado,
   consulta HTTPS 200 registrada e hash do corpo recebido. O digest deve coincidir
   com os bytes locais atuais. `trusted`/`match` não são aceitos como substitutos
   dessa verificação. A referência pode ser reutilizada de uma consulta anterior
   vinculada à mesma release; sua data continua explícita. Não há consulta nova
   implícita. Novas atualizações devem produzir nova fotografia de evidências.
4. **Origem documentada:** catálogo/recurso e URLs oficiais identificáveis;
   evidência de aquisição vinculada ao manifesto e às fontes. Testemunho explícito
   e retrospectivo do operador é admitido como testemunho, com autoria contextual,
   data e limitações; não se inventa transcript contemporâneo de download.
5. **Fonte sem checksum publicado:** admissível para o formato `section` quando
   o catálogo não informa hash, consultas documentadas dos endpoints investigados
   retornam ausência (404/410), e metadados oficiais HEAD 200 identificam o mesmo
   recurso e tamanho. Timeout/503 não demonstram ausência. ETag não vira SHA.
   Os hashes locais atuais devem coincidir com a linhagem histórica, e o
   testemunho de aquisição deve abranger essa fonte.
6. **Reconciliação efetiva:** a importação retida precisa demonstrar formato,
   cobertura lida, CRC, ausência de quarentena e quantidade selecionada por
   arquivo. Todas as linhas presidenciais selecionadas dos dois formatos devem
   estar reconciliadas, sem divergências, linhas sem contraparte ou ambiguidades.
   As contagens por fonte devem somar o total reconciliado e o total do banco.
   Cada UF/turno da fonte sem checksum deve estar coberta por BWEBs cujos bytes
   atuais correspondam às referências oficiais. Toda a cobertura declarada deve
   ter essas âncoras. A reconciliação retida é reaplicável porque os bytes de
   entrada e os artefatos de saída continuam iguais aos da execução documentada.
7. **Validação corrente dos derivados:** integridades SQLite, referencial,
   estrutural e matemática aprovadas; cobertura explícita satisfeita; comparação
   independente dos agregados JSON com o SQLite existente. Não é suficiente
   editar os estados do manifesto. Falhas impedem criar a release candidata.
8. **Limitações e aprovação:** completude exaustiva das seções continua
   `not_assessed` sem inventário independente. Assinatura/autenticação independente
   permanecem `not_performed`. Aprovação humana de referências, política,
   aquisição, limitações e redistribuição é condição separada do deploy.

## Dimensões e estados

| Dimensão | Resultado possível nesta política | O que não significa |
| --- | --- | --- |
| Bytes locais | SHA-256/SHA-512 atuais coincidem com históricos | Origem autenticada por assinatura |
| Referência externa | SHA-512 atual coincide com referência HTTPS oficial registrada | Prova absoluta da legitimidade eleitoral |
| Fonte sem referência | Ausência nos endpoints consultados; origem documentada e conteúdo reconciliado | Checksum local qualificado como oficial |
| Aquisição | Testemunho do operador identificado e vinculado | Certificado, assinatura ou log de download inventado |
| Conteúdo | Reconciliação completa dos registros presidenciais selecionados | Validação dos cargos não selecionados |
| Prontidão | `ready_for_declared_scope`, sem blockers técnicos | Autorização automática de publicação |

Não se afirma independência institucional entre formatos publicados pelo mesmo
TSE. Independência das comparações e formatos não equivale a uma auditoria externa
do processo eleitoral. Dados técnicos incompletos/corrompidos são rejeitados;
uma aprovação humana não pode superar uma falha de evidência.

## Identidade e preservação

O ID do **conteúdo eleitoral** permanece igual quando todos os JSONs de resultados
continuam byte a byte idênticos. Mudar esse campo nos próprios JSONs violaria essa
preservação. Uma revisão cria outra **identidade de release de metadados**:

- novo `metadata_release_id`, derivado do SHA-256 canônico do novo manifesto
  antes de inserir esse campo;
- novo SHA-256 do manifesto completo;
- `provenance.json`, com documentos vinculados, recálculo atual e validação;
- relação explícita com os manifestos histórico nacional e compacto.

Os artefatos anteriores, inclusive `validation.json`, são copiados sem alterações.
Não se muda `hash_calculation` no manifesto histórico. O novo avaliador produz
uma avaliação independente; o avaliador legado continua retornando os estados
históricos ao validar a release histórica. Não há exceção que retire blockers
de um objeto antigo.

O validador compacto verifica o hash do dossiê e **recalcula a avaliação**. O
manifesto inteiro deve corresponder ao resultado derivado dos documentos.
Arquivos extras, outra natureza de dados, versões misturadas, hash divergente
e dossiê ausente continuam inválidos. O limite do bundle passa de 32 para 33
arquivos somente para acomodar o dossiê nomeado e validado; a lista exata do
manifesto, orçamento de tamanho e rejeição de caminhos inseguros permanecem.

## Aprovação humana

`web_release.py` continua exigindo elegibilidade técnica, dataset/hash/tag exatos
e redistribuição aprovada. Para esta política exige adicionalmente:

- `metadata_release_id` exato;
- `provenance_approval.approved: true`, somente por decisão humana;
- `policy_id` e `review_sha256` exatos;
- revisor e data da decisão.

A decisão de proveniência engloba referências oficiais, uso da via sem checksum,
confiança no testemunho e limitações. Ela não substitui a decisão de redistribuição.
Ambas ficam `false` no candidato preparado pelo Codex. Nenhum `--force` ou caminho
para dispensar evidências/aprovação foi introduzido.
