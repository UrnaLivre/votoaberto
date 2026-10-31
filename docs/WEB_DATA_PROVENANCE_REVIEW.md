# M6 — Proveniência da primeira base pública

> Fotografia histórica. A [M6.1](WEB_DATA_PROVENANCE_FINALIZATION.md) recalculou
> os 57 ZIPs, implementou a política documentada e preparou outra release de
> metadados tecnicamente elegível. Este relatório e suas evidências continuam
> preservados; seu `BLOCKED` descreve o estado anterior.

Consulta/execução: **31/10/2026**; horários das evidências em UTC.
Repositório `UrnaLivre/votoaberto`, branch `feat/web-production-cloudflare`.
Conclusão: **BLOCKED**. A proveniência ganhou evidência oficial nova, mas a
base existente continua `public_readiness: not_ready` pela política vigente.
Não houve importação, extração de ZIP, reconstrução do SQLite, alteração de
votos, aprovação presumida, push, tag, release ou deploy.

## Evidências e auditoria inicial

- [57 registros individuais de fontes e referências](WEB_DATA_SOURCE_EVIDENCE.json):
  nomes, URLs/IDs, digests, consultas HTTP, avaliações anteriores e propostas.
- [Termos e metadados cartográficos](WEB_DATA_REDISTRIBUTION_EVIDENCE.json).
- [Revalidação, identidade, testes, preflight e estado remoto](WEB_DATA_REVALIDATION.json).
- [SHA-256 antes/depois dos 79 arquivos preservados](WEB_DATA_INTEGRITY_REVIEW.json).
- [Coletor reproduzível e limites operacionais](../tools/provenance/README.md).

Antes de implementar, foram lidos `WEB_RELEASE_REPORT.md`, `WEB_DEPLOYMENT.md`,
`DATA_POLICY.md`, `DATA_ENGINE_OPERATIONS.md`, `NATIONAL_IMPORT.md`,
`TSE_2026_NATIONAL_SOURCE_INVENTORY.json`,
`TSE_2026_NATIONAL_VALIDATION_SUMMARY.json`, os manifestos nacional/compacto,
o avaliador, os testes de confiança/cache e os gates Web. Os documentos
históricos permanecem preservados; os dois documentos Web recebem nota M6.

A árvore estava limpa em `c591e43af29c43d96f6dac16669f0e073f9628dc`, na branch
solicitada. Os workflows remotos desse commit concluíram com sucesso:
[Flutter 41240990196](https://github.com/UrnaLivre/votoaberto/actions/runs/41240990196)
e [Data Engine 41240990152](https://github.com/UrnaLivre/votoaberto/actions/runs/41240990152).
São validações do commit anterior, não dos commits M6, que não foram enviados.
As leituras autenticadas retornaram listas vazias de variáveis do repositório
e environments. `WEB_DEPLOY_ENABLED` não está definida nesse escopo e não foi
ativada. Não se presume inspeção de configurações herdadas da organização.
O workflow de deploy não foi modificado nem executado.

Corpos HTTP pequenos ficam no cache ignorado `.local/m6/http`, por SHA-256.
As linhas de checksum recebidas e os hashes dos corpos estão versionados nas
evidências. Relatórios integrais locais ficam em `.local/m6/`; seus resultados
relevantes estão consolidados no JSON de revalidação. São registros observados
desta execução, não uma ata assinada pelo TSE ou pelo operador.

## 1. Estado anterior confirmado

| Item | Estado observado |
| --- | --- |
| Release nacional local | `6305f74561d4687a23bd3054` |
| Dataset compacto | `e4e9c9cb5189ab5d4e124bfc` |
| Escopo declarado | Presidente, 2026, turnos 1 e 2, 27 UFs e ZZ |
| Minibase instalada | 32 JSONs, 4.475.495 bytes, incluindo manifesto e validação |
| Localidades | 5.716: 5.571 domésticas e 145 no exterior |
| Fontes ZIP | 57: 56 BWEB e uma votação nacional por seção |
| Auxiliares `.sha512` locais | 56, distintos das 57 fontes ZIP |
| Tamanho atual dos ZIPs | 5.463.538.463 bytes, aproximadamente 5,09 GiB |
| SQLite existente | 935.424.000 bytes |

O valor aproximado de 4,15 GB não descreve o inventário final. O relatório
histórico distingue a fotografia inicial de 4.457.109.026 bytes e a posterior,
após substituições registradas pelo operador de nove BWEBs do primeiro turno
(ES, GO, MG, MS, MT, PA, PB, PE e PI). Não se comparou o conteúdo dos backups
antigos nesta missão. A substituição histórica não foi tratada como divergência
de votos da release atual.

## 2. Causas exatas dos blockers

### `source_hashes_reused_from_local_cache`

Os **57 ZIPs** têm `hash_calculation: reused_local_fingerprint_cache` no manifesto
nacional. SHA-256/SHA-512 são cálculos anteriores associados a tamanho, `mtime_ns`,
dispositivo e inode. A importação nacional reutilizou os digests desse cache.

`pipelines/tse_importer/assessment.py::assess_release` bloqueia prontidão pública
quando qualquer ZIP tem esse marcador. `engine.validate_release` verifica os
artefatos e banco, mas reaplica evidências retidas das fontes. Consultar o checksum
remoto novamente melhora a independência da referência; não transforma um digest
local retido em cálculo corrente dos bytes.

M6 confirmou fingerprints coincidentes em 57/57 fontes. **Fingerprint não é prova
criptográfica de bytes intactos.** Nenhum ZIP local foi aberto para hash ou
extração, respeitando a prioridade incremental. O blocker permanece pela regra
atual; não se removeu seu marcador para obter aprovação. A identidade dos
derivados foi, separadamente, recalculada e preservada.

### `operator_trusted_hashes_incomplete`

`integrity.verify` compara digest e referência. `trusted: true` é declaração
explícita do operador, conforme `DATA_POLICY.md` e `DATA_ENGINE_OPERATIONS.md`.
URL oficial e coincidência SHA não atribuem esse booleano automaticamente.
`source_hash_assessment` e `assess_release` exigem todas as fontes comparadas
sob essa declaração para o estado `matched_operator_trusted`.

Somente os dois BWEBs SC tinham confiança do operador e digest coincidente,
classificados individualmente como `verified` no vocabulário legado. Outros
**54 BWEBs** coincidiam com auxiliares locais, sem confiança atribuída. A fonte
nacional não tinha referência: **55/57** eram insuficientes para esse critério,
sem que isso representasse divergência de votos.

M6 fornece referência oficial nova para os 56 BWEBs, inclusive SC. Há suporte
novo para propor confiança nos 54 restantes. Todas as `proposed_reference`
mantêm `trusted: false`; nenhuma declaração humana foi fabricada. A fonte
nacional continua sem referência independente comparável. Os manifestos e
suas classificações não foram regravados.

## 3. Método e resultados de hashes

O coletor consulta o CKAN oficial de
[Resultados 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026) e
[Boletim de Urna 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna).
Cruza nomes exatos, preserva IDs e consulta referências por HTTPS sem obter ZIPs.
São três workers, timeout de 15 segundos por operação de rede, até duas tentativas,
checksums limitados a 4 KiB e catálogos a 2 MiB. TLS usa a cadeia padrão da
plataforma. Redirects fora dos hosts oficiais ou para ZIP são recusados.
O parser confere algoritmo, digest completo e nome exato na linha GNU;
normaliza somente CRLF do texto. MIME `application/zip` nos pequenos `.sha512`
do TSE não autoriza download ou extração de dados eleitorais.

Coleta inicial: 21:07:39–21:07:42 UTC; complemento RR: 21:11:04 UTC.
Recebidos 8.848 bytes de checksums BWEB (56 × 158). Com os dois catálogos e
dois primeiros 404, a coleta principal soma 140.259 bytes de corpos HTTP.
Consultas documentais/complementares são separadas; o maior documento adicional
foi o PDA IBGE, com 982.498 bytes. **Zero bytes de ZIP baixados.**

| Medida | Quantidade | Significado |
| --- | ---: | --- |
| Fontes ZIP avaliadas | 57 | Inventário da release existente |
| SHA-512 oficiais obtidos novamente | 56 | Todos os BWEBs, HTTP 200 |
| Coincidências com digest local retido | 56 | Não é recálculo de bytes ZIP em M6 |
| Referências exclusivamente herdadas | 0 | Os dois casos SC também foram consultados |
| Digests ZIP locais reutilizados | 57 | Linhagem histórica e fingerprints preservados |
| Fontes sem referência utilizável encontrada | 1 | Votação por seção nacional |
| Endpoints dessa fonte com HTTP 404 | 4 | Com/sem `.zip`, SHA-512/SHA-256 |
| Referências BWEB indisponíveis ao final | 0 | RR resolvido documentalmente |
| Divergências de digest observadas | 0 | Entre as 56 comparações possíveis |
| Declarações anteriores do operador | 2 | SC, ambos os turnos, herdadas |
| Fontes ainda sem declaração no manifesto | 55 | 54 BWEB + uma nacional |
| Novas declarações do operador | 0 | Dependem de revisão humana |
| Assinaturas independentes verificadas | 0 | Nenhuma cadeia aplicável verificada |

### Catálogo de RR

A entrada de ZIP `e54adb15-931b-462e-a506-7b6330dd2a9d` e a entrada de hash
`3c8e2aec-5df5-4a6e-a632-eb9063d3414b` apontam ambas para
[`bweb_2t_RR_261020260742.zip.sha512`](https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/buweb/bweb_2t_RR_261020260742.zip.sha512).
A primeira coleta não encontrou o recurso ZIP pelo nome. A consulta complementar
recebeu 200 e nomeia exatamente o arquivo local; seu digest coincide.
Ambos os aliases e a tentativa inicial estão preservados. A URL ZIP fica
marcada como inferida do checksum, **não como ZIP consultado**. URLs diferentes
para o mesmo nome continuariam sendo erro de ambiguidade.

### Fonte nacional sem checksum encontrado

Recurso [Presidente — Votação por seção — 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026/resource/01ea4ccd-f443-469c-9f29-c69ff97f7d4c),
ID `01ea4ccd-f443-469c-9f29-c69ff97f7d4c`,
[ZIP oficial](https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_BR.zip).
O campo `hash` está vazio. Foram testados `.zip.sha512`, `.zip.sha256`,
`.sha512` e `.sha256`, todos 404. Isso não prova inexistência de qualquer
referência em todo o TSE.

HEAD HTTPS em 21:15:20 UTC recebeu 200 e tamanho 241.891.087 bytes, igual ao
retido localmente; `Last-Modified: Mon, 26 Oct 2026 17:42:32 GMT` e
`ETag: "e6af70f-65ec1dac721b7"`. Não há Digest/Content-Digest recebido.
ETag é identificador opaco, nunca tratado como SHA ou assinatura. O manifesto
registra consulta ao catálogo em 29/10/2026, não um transcript HTTPS preservado
do download original. Não se inventou esse registro.

SHA-256 local retido:
`c928321f63f2d095706fca73d4607c048d2ada23bda6876455d6911aaf1bc9c1`.
SHA-512 local retido:
`4bdd302e64afb5b9c16081dc03433f23392415aacc56b0d894283c09bc8245e8448d5c54d44ea6e25939478fa408bef21dea00fc0b7e3c9f05abdbf2f51de536`.
São digests locais, **não referências oficiais**.

Evidência alternativa: recurso identificável no catálogo, metadados HTTPS
coerentes e reconciliação dos registros presidenciais selecionados com 56 BWEBs
agora vinculados a referências oficiais novas. Sustenta proveniência documentada
e consistência no recorte; não autentica cada byte do ZIP nacional ou os cargos
não selecionados. A lacuna continua expressa.

## 4. Confiança e coerência da política

| Conceito | Evidência | Limitação |
| --- | --- | --- |
| Integridade dos derivados | SHA-256 e validação do banco/JSON refeitos | Não prova origem do ZIP |
| Referência oficial nova | 56 respostas HTTPS ligadas ao catálogo/nome | Comparadas com digests ZIP retidos |
| Proveniência documentada | URLs, IDs, datas, metadados e linhagem | Uma fonte sem checksum independente |
| Confiança do operador | Duas declarações antigas; 54 propostas novas sustentadas | Nenhuma declaração humana nova |
| Autenticidade criptográfica do arquivo | Não verificada | SHA não é assinatura; TLS autentica transporte |
| Validação eleitoral | Matemática/referências/reconciliação do recorte | Não certifica legitimidade eleitoral |

`origin_authentication` e `signature_verification` permanecem `not_performed`.
Isso não desliga nem nega a validação do certificado TLS; indica ausência de
verificação de assinatura/cadeia independente aplicável ao arquivo eleitoral.
Os serviços e formatos reconciliados também não são fontes institucionalmente
independentes do TSE. Nenhum desses conceitos prova legitimidade absoluta.

A política exige referências de confiança para todas as fontes, sem exigir
assinatura digital inexistente. Já admite publicação no recorte territorial
declarado sem inventário exaustivo de seções: `section_completeness: not_assessed`
não é um blocker oculto ou requisito removido por M6.

Não se alterou a política. Uma política futura para recursos sem checksum
poderia exigir, de forma geral e reutilizável: identificação oficial inequívoca,
aquisição/linhagem documentada, hashes locais imutáveis, reconciliação completa
com fonte relacionada vinculada a referência oficial, matemática e cobertura
declarada aprovadas, revisão do operador e limitações registradas. Precisaria
tratar separadamente atualidade dos bytes e ausência de referência. Declarar
`trusted: true` sobre hash do mesmo cache não cria independência. A ausência de
registro de download original precisa entrar nessa revisão metodológica.
É proposta para decisão informada, não exceção implementada para liberar 2026.

## 5. Revalidação e reconciliação

`engine.validate_release` recalculou hashes dos artefatos e verificou o banco
existente em 36,723 s. Reconciliação foi confrontada com banco/relatório retidos,
marcada `retained_report_and_database`; não foi repetida lendo ZIPs.

| Dimensão | Resultado |
| --- | --- |
| SQLite | `ok` / `passed` |
| Referências internas | `passed`, zero foreign keys e ligações eleitorais inválidas |
| Matemática | `passed`, zero erros e totais indisponíveis |
| Estrutura | 5.731.614 registros de resultado |
| Cobertura | 56 pares UF/turno, nenhum exigido ausente |
| Seções/turnos observados | 998.411 |
| Completude exaustiva de seções | `not_assessed`, sem inventário independente |
| Reconciliação retida conferida | 5.731.614 linhas e 998.411 pares seção/turno coincidentes |
| Divergências / só BU / só seção / ambiguidades | 0 / 0 / 0 / 0 |
| Identidade de equipamento | `not_asserted` |
| Elegibilidade local / pública | `eligible` / `not_ready`, mesmos dois blockers |

`validate_embedded` passou nos hashes/hierarquia e depois na comparação
independente dos JSONs ao SQLite existente: totais, candidatos, categorias,
nomes, municípios e UFs. Banco aberto com `mode=ro`, `uri=True` e `query_only`.
Foram 11.431 registros município/turno, em 21,521 s. Não houve reconstrução.
Bruxelas (`29432`), Trípoli (`30686`), identificadores, atribuições e separação
de turnos foram preservados por identidade de bytes. Trípoli continua sem dado
no segundo turno; nenhuma ausência virou zero. Nenhuma agregação foi alterada.

O catálogo Resultados 2026 alerta para 39 registros de aptos ligados à transferência
temporária que permaneceram também na origem: 158.745.502 registros nos arquivos
versus 158.745.463 pessoas após a correção indicada pelo TSE. É aviso documental,
**não ajuste feito em M6**, nem denominador transplantado para outro recorte.
Não se alteraram aptos, comparecimento ou abstenção. A reconciliação não equivale
a auditoria externa desse cadastro.

## 6. Redistribuição — revisão documental para aprovação humana

Não é parecer jurídico formal nem aprovação do operador. MIT do código não
relicencia dados eleitorais, cartografia ou outros materiais de terceiros.

### TSE

| Organização / conjunto | Recurso | Termo observado em 31/10/2026 |
| --- | --- | --- |
| TSE/AGEL, Resultados 2026 | [Presidente por seção, 01ea4ccd…](https://dadosabertos.tse.jus.br/dataset/resultados-2026/resource/01ea4ccd-f443-469c-9f29-c69ff97f7d4c) | `cc-by`, Creative Commons Attribution |
| TSE/AGEL, Boletim de Urna 2026 | [112 entradas ZIP/hash](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna), URLs/IDs individuais no JSON | `cc-by`, Creative Commons Atribuição |
| TSE/SMG, Códigos TSE/IBGE | [c6c767d7-f341-4256-8dff-010683a9c796](https://dadosabertos.tse.jus.br/dataset/codigos-oficiais-de-uf-e-municipios-segundo-o-tse-e-o-ibge/resource/c6c767d7-f341-4256-8dff-010683a9c796) | `cc-by`, Creative Commons Attribution |
| TSE/AGEL, Eleitorado 2026 | [Locais, 300626b4…](https://dadosabertos.tse.jus.br/dataset/eleitorado-2026/resource/300626b4-2b24-4d2e-b4fc-46b569cfffe5) | `cc-by`, Creative Commons Attribution |

Os catálogos não explicitam versão numérica. O link
[`opendefinition.org/licenses/cc-by`](https://opendefinition.org/licenses/cc-by/)
apresenta atualmente [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br).
Registram-se versão não declarada diretamente pelo TSE e destino atual da
referência; não se reescreveu o manifesto como declaração textual de versão.

CC BY 4.0 permite compartilhar/adaptar sob condições de crédito, link, indicação
de modificações e ausência de restrições adicionais. Recomenda-se crédito com
autor, título, recurso/licença, acesso e alterações, sem sugerir endosso.
Nenhuma condição adicional específica foi identificada nos metadados examinados.
Periodicidade e alertas de leitura de CSV são informações operacionais.
Aceitar/documentar a referência e a ambiguidade de versão continua decisão humana.

Transformações: seleção presidencial por turno, normalização dos formatos,
reconciliação de BWEB/votação por seção, SQLite derivado, agregações
município/UF/Brasil/exterior e conversão para JSON. ZIPs/BUs integrais não são
redistribuídos. Texto proposto, com links dos catálogos/licença acima:

> Fonte: Tribunal Superior Eleitoral (TSE), Portal de Dados Abertos — Resultados
> 2026, votação presidencial por seção e boletins de urna, ambos os turnos.
> Termo informado: Creative Commons Atribuição, sem versão explicitada pelo TSE;
> referência de licença vinculada no catálogo. Consulta de proveniência:
> 31/10/2026. O Voto Aberto realiza processamento independente de dados públicos:
> seleção, reconciliação, agregação e conversão para JSON. Fontes, hashes,
> alterações e limitações estão no relatório M6. Não se presume endosso do TSE
> ou certificação do processo eleitoral.

### Cartografia e correspondências

| Material | Fonte / termo | Transformações e avaliação |
| --- | --- | --- |
| `br_states.geojson` | [IBGE Malhas v3](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3), [endpoint exato](https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=intermediaria&intrarregiao=UF) | Já simplificada pela API, bytes preservados; sem afirmar ano territorial 2026 ou CC/MIT |
| Pontos municipais | [IBGE Localidades, Censo 2022](https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/), `Localidades_Brasil_gpkg.zip` | Seleção de sedes/DF/Noronha, códigos, EPSG:4674 → WGS84 e seis casas; não são posições de urnas |
| Correspondência municipal | [TSE/IBGE](https://dadosabertos.tse.jus.br/dataset/codigos-oficiais-de-uf-e-municipios-segundo-o-tse-e-o-ibge) | CC BY confirmada no catálogo; joins por identificadores, sem intercambiar códigos |
| Correspondência exterior | [TSE Locais 2026](https://dadosabertos.tse.jus.br/dataset/eleitorado-2026/resource/300626b4-2b24-4d2e-b4fc-46b569cfffe5) e [edital TRE-DF](https://www.tre-df.jus.br/comunicacao/noticias/arquivos/edital-carga_e_lacracao_das_urnas_eletronicas__df_e_zz____2026/@@download/file) | TSE CC BY; edital oficial público, sem CC/MIT presumida. Correspondências derivadas, sem cópia integral do edital/endereços pessoais |
| Mundo e rótulos | Natural Earth 5.1.1, [map units 50m](https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_map_units.zip) e [countries 50m](https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip) | [Termos oficiais](https://www.naturalearthdata.com/about/terms-of-use/) confirmam domínio público em todas as versões; simplificação 0,04° e quatro casas. Crédito preservado, embora facultativo |

O [PDA IBGE 2024–2025](https://www.ibge.gov.br/np_download/novoportal/documentos_institucionais/Plano_de_Dados_Abertos_IBGE_2024_2025.pdf)
foi obtido com HTTP 200, SHA-256
`9c56d0c952a326d9489e2e829fa12795570ae8fb65d34633268f03b22b599e02`.
Seu glossário explica dados/licenças abertas; **não é licença específica dos
dois recursos cartográficos**. Malhas v3 confirma origem/finalidade Web, sem
licença explícita encontrada. O índice Localidades foi acessível; as páginas
gerais de dados abertos/termos e a página do produto consultadas retornaram 403.
A página do edital TRE-DF retornou 403; conteúdo/hash são herdados, sem nova
verificação desse documento nesta missão.

`CARTOGRAPHY.md` registra cópia histórica de correspondência IBGE em lista OSM
e condição adotada de crédito. Ela não foi elevada a licença primária específica
nem generalizada. Termos da Agência de Notícias não foram usados para licenciar
cartografia. Os rótulos de licença dos manifestos geográficos são declarações
anteriores do projeto, não aprovação jurídica M6.

**Pendência humana:** rever a base de reutilização de malhas/pontos IBGE e uso
derivado do edital TRE-DF; se necessário, obter confirmação específica dos órgãos.
Revisar atribuição TSE e referência de licença. Não há autorização para registrar
`redistribution_review.approved: true`. Texto cartográfico proposto, acompanhado
dos links da tabela:

> Cartografia: IBGE — Malhas Geográficas v3 e Localidades do Brasil, Censo 2022;
> Natural Earth 5.1.1 — dados em domínio público. Correspondências: TSE, códigos
> TSE/IBGE e locais de votação 2026; TRE-DF, edital de carga e lacração 2026.
> O Voto Aberto selecionou e associou registros por códigos, converteu coordenadas
> e simplificou a geometria mundial. Mapas e pontos servem à navegação, sem
> precisão para medição, limites eleitorais ou localização de equipamentos.
> Créditos não implicam endosso dos fornecedores.

O app já credita os quatro fornecedores e informa processamento independente.
Os textos preparam a publicação futura; não se alteraram Dart, assets ou build.

## 7. Identidade preservada e aprovação

| Objeto | SHA-256 final, igual ao inicial |
| --- | --- |
| Manifesto compacto / instalado | `c4dcddacb8092ff1dfffb35b07b739dbf360232e701e080087f52a4a09e20637` |
| Manifesto nacional | `cb7f7757501913f319605b65c58d1d00784cd319228db05223e85b0d27b338fa` |
| SQLite nacional | `c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4` |

Dataset: **`e4e9c9cb5189ab5d4e124bfc`**, sem regeneração. A lista de hashes
antes/depois dos 79 arquivos tem zero mudanças: release nacional, compacta,
ponteiros e assets eleitorais/geográficos. Os 32 JSONs instalados e da release
mantêm os bytes. Os 57 ZIPs conservam tamanho/mtime e fingerprints, com a
limitação expressa de não ter sido recalculado seu conteúdo nesta missão.

`apps/votoaberto_flutter/web-data-approval.json` continua intacto: dataset/hash/tag
vazios, revisão não aprovada, sem revisor/data fabricados. O mecanismo vigente
usa revisão aprovada e campos vinculantes; nenhum booleano paralelo foi criado.
**Não há candidato tecnicamente elegível de aprovação.** Os valores acima são
identidade para revisão. Atualização legítima futura de metadados exigirá novo
hash de manifesto vinculado à aprovação e prova separada de hashes eleitorais
preservados. `release_tag` continua pendente, sem criar tag imutável.

## 8. Validação, regressões e segurança

Comandos principais na raiz:

```powershell
.venv\Scripts\python.exe -m pytest -q tests/test_provenance_review.py tests/test_assessment.py tests/test_storage_policy.py tests/test_web_release.py tests/test_embedded_exporter.py tests/test_embedded_build.py --basetemp=.local/m6/pytest-targeted
.venv\Scripts\python.exe -m ruff format --check pipelines/tse_importer apps/votoaberto_auditor tests tools/generate_embedded_fixture.py tools/geography tools/provenance apps/votoaberto_flutter/tool
.venv\Scripts\python.exe -m ruff check pipelines/tse_importer apps/votoaberto_auditor tests tools/generate_embedded_fixture.py tools/geography tools/provenance apps/votoaberto_flutter/tool
python apps/votoaberto_flutter/tool/web_release.py audit --mode real --report .local/m6/web-audit.json
python apps/votoaberto_flutter/tool/web_release.py preflight --source apps/votoaberto_flutter/assets/data/real
```

**124 passed, 1 skipped**, zero falhas, 68,73 s. O skip é teste oficial opt-in
que demandaria processamento dos originais; a validação real usou a release
existente. Ruff: 40 arquivos, formatação/lint aprovados. Pacote Web auditado:
82 arquivos, 49.065.783 bytes, limites estáticos aprovados, dados íntegros,
`production_approved: false`. Preflight: **saída 2 esperada**, pelos dois blockers.

Novas regressões: nome/algoritmo inválidos, referência ausente, 404, digest
divergente, arquivo local alterado/ausente, limites de download, tentativas,
URLs/redirects inseguros, ambiguidade/aliases, manifesto imutável e distinção
entre proposta e confiança humana. Os testes existentes de cache/avaliação,
aprovação vinculada a outro dataset, hash divergente, fixtures e empacotamento
passaram. Não foi criado `--force`, `--skip-verification` ou aprovação automática.

Não se recompilou Flutter/Android porque dados consumidos, identidade, metadados
e código do produto não mudaram. Não se repetiu a suíte completa Flutter/browser
da missão anterior. Não se disparou CI remoto. O workflow **Data Engine** passou
a incluir o coletor em lint/filtros; workflow Flutter/deploy e gates intactos.

Limitações de ferramentas: algumas leituras Web IBGE deram 403; HTTPS direto
ao PDA funcionou e ficou registrado. `pdftotext` local encontrou restrições
MiKTeX; extração documental foi concluída com `pypdf` já instalado no runtime.
Uma leitura exploratória com encoding padrão Windows e uma URI SQLite sem
`uri=True` falharam; as execuções corretas usam UTF-8 e modo somente leitura.
Não houve falha de validação dos dados ou mutação do banco nessas tentativas.

## 9. Próximos passos mínimos

1. **Confiança e fonte sem hash:** revisar as 56 referências e propostas;
   obter referência independente da fonte nacional ou decidir formalmente uma
   política geral para proveniência/reconciliação sem checksum publicado.
   Não basta declarar oficial o digest do próprio cache. Não se exige inventar
   assinatura digital.
2. **Reavaliação de metadados, sem reimportar:** após a decisão, vincular as
   evidências à release preservando derivados. Pela regra atual, o cache exige
   hashes correntes: leitura sequencial dos originais locais para hash, sem
   extração/download/reconstrução. Não foi feita em massa nesta missão porque
   a lacuna independente da fonte nacional já impede elegibilidade e a prioridade
   é reutilização. Aceitar a cadeia retida como alternativa exigiria política
   formal, justificativa e regressões, não simples remoção do blocker. O CLI
   `validate` atual não grava novas avaliações.
3. **Redistribuição:** operador revisa atribuição TSE, ambiguidade de versão e
   documentação IBGE/TRE-DF, registrando sua decisão.
4. Somente com avaliação técnica elegível, preparar candidato com dataset,
   **hash exato atualizado se o manifesto mudar**, tag de dados e revisão.
   Operador aprova explicitamente esses valores. Depois, CI do commit revisado
   e preparação da release conforme `WEB_DEPLOYMENT.md`.

Não é preciso reimportar os 5,7 milhões de registros, reconstruir SQLite ou
baixar ZIPs para resolver essas decisões. Há evidência concreta para revisão,
mas uma lacuna essencial e critérios técnicos não satisfeitos impedem usar
`READY_FOR_DATA_APPROVAL` ou `READY_FOR_RELEASE_PREPARATION`. Deploy continua
desabilitado nesta entrega.

## 10. Organização Git

O commit local `db29481` contém coletor, README, testes e integração de lint
no Data Engine. O commit documental seguinte contém este relatório, quatro
JSONs de evidência e as notas M6 nos dois documentos Web. A lista exata pode
ser conferida com `git log c591e43..HEAD --oneline` e
`git diff --stat c591e43..HEAD`. Não há alterações no avaliador, preflight,
aprovação Web, dados eleitorais, cartografia ou regras de agregação.
Nenhuma branch nova, push, merge, tag, release ou configuração externa foi criada.
