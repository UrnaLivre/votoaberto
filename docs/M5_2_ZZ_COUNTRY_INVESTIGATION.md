# M5.2 — Investigação das localidades eleitorais do exterior

## Resumo executivo

Investigação de 31/10/2026, baseada na `main` sincronizada `f7f8011`, com PR #6
integrado e working tree inicialmente limpa. Única branch criada:
`feat/m5-zz-country-verification`. Não houve push, PR, merge, reimportação nacional
ou reconstrução do SQLite.

Das **28 localidades investigadas, 26 receberam associação verificável**. A cobertura
passou de **117/145 (80,69%) para 143/145 (98,62%)**, em **100 países/territórios**
(antes, 80). Os 20 novos países estão enumerados no resumo JSON. O denominador
é o universo de localidades observado no M4, sem afirmação de completude eleitoral geral.

Permanecem **duas pendências**: Bruxelas tem locais cadastrados em Bélgica e
Luxemburgo, exigindo um derivado de votos por seção; Trípoli apresenta conflito
entre referência administrativa à Líbia e endereço físico na Tunísia. Há, assim,
um conflito documental/semântico não resolvido e uma abrangência multinacional
documentada ainda incompatível com o agregado municipal. Nenhuma foi atribuída
integralmente a um país. Não há caso classificado como `not_found`.

Os países ganharam **702 votos contabilizados no primeiro turno e 734 no segundo**
(686 e 705 válidos). São votos anteriormente residuais, sem alteração dos
resultados originais. A reconciliação executada passou para todos os candidatos,
categorias, seções e disponibilidades: **países + residual = exterior original M4**.
O residual continua necessário. `public_readiness.status = not_ready` foi preservado.

O resultado é geografia dos locais oficialmente cadastrados associada a chaves
de resultados efetivamente observadas. O cadastro não é um boletim de urna nem
certifica comparecimento físico individual ou residência do eleitor.

## Fontes, versões e identificação

### S1 — Cadastro TSE de locais de votação de 2026

Fonte decisiva: [Eleitorado por local de votação — 2026][S1-catalogo], com
[ZIP oficial][S1]. Download auxiliar separado dos ZIPs eleitorais originais.
Foram lidos o membro `eleitorado_local_votacao_2026_ZZ.csv` e seu `leiame.pdf`;
nenhum CSV nacional de resultados foi reimportado. O arquivo ZZ tem **5.430 registros**,
41 colunas, separador `;` e codificação Latin-1. Geração interna:
**25/10/2026 15:27:44**; HTTP Last-Modified: **25/10/2026 18:32:19 UTC**.

- ZIP: 167.493.511 bytes; SHA-256 `771ecfe5086b65c38943df9f694831dc5b94e0addd563517cd139fbd97642981`.
- CSV ZZ: 2.259.581 bytes; SHA-256 `9871aeca7234d11b15c2159aa93f06e2c6b736965d24ee7633c2658183decb34`.
- Licença declarada pelo catálogo: Creative Commons Attribution, sem versão especificada.
- Consulta: 31/10/2026; URLs e metadados preservados no manifesto e na revisão versionada.

O `leiame.pdf`, página 3, define `CD_MUNICIPIO` como código TSE, e os campos
`NR_ZONA`, `NR_SECAO`, `NR_LOCAL_VOTACAO` e seção principal/agregada. O cadastro
inclui `NR_TURNO` e `AA_ELEICAO`. A junção usa **código TSE + zona + seção + turno**,
confirmando também o local. No SQLite somente leitura, `elections` liga `6257`
ao primeiro turno e `6258` ao segundo. Os nomes nunca são chaves da junção.

**Não existe coluna padronizada de país nesse CSV.** `NM_BAIRRO` significa bairro;
não foi transformada genericamente em país. Cada uma das 26 decisões guarda o
literal de país efetivamente presente no endereço ou, nos casos individualmente
revisados, no campo `NM_BAIRRO`, além dos três campos textuais completos. O país
também é corroborado pela planilha TRE-DF S2. Essa revisão é explícita e restrita
aos bytes fixados de S1; não é um geocodificador nem inferência por cidade.
O próprio caso Bruxelas demonstra por que `NM_BAIRRO` não pode virar regra geral.

Todas as **52 chaves observadas** das 26 associações têm `CD_TIPO_SECAO_AGREGADA=1`
(Principal) e `NR_SECAO_PRINCIPAL=-1`, nos turnos correspondentes. Também foram
revisadas todas as linhas cadastrais desses códigos, incluindo duas linhas
agregadas de Rio Branco, para recusar locais/campos incompatíveis. A quantidade
e a presença das seções por turno coincidem integralmente com o M4.

### S2 — Planilha TRE-DF de votação manual

[Notícia oficial de 02/09/2026][S2-noticia], atualizada em 08/09/2026,
e [download exato da planilha][S2]. ZIP de **9.291 bytes**, Last-Modified
**02/09/2026 18:15:27 UTC**; SHA-256
`d0f122a2fa5d33c2382e608ed7d4574a0a171f4b63b21c5534b606c08fad578b`.
Os bytes baixados nesta missão coincidem com a cópia M5.
Membro `Secoes_Eleitorais___Exterior___Votacao_Manual.xlsx`, aba **Votação Manual**.

A planilha tem país, cidade, local, aptos e quantidades; **não tem código municipal
TSE nem número individual da seção**. Serve de corroboração e para explicar a
lacuna no edital eletrônico, nunca como identificação suficiente sozinha.
As linhas da tabela abaixo contam o cabeçalho como linha 1.

### S3 — Edital TRE-DF de carga e lacração

[PDF oficial de 2026][S3], 1.116.535 bytes; Last-Modified
**15/09/2026 15:32:26 UTC**; SHA-256
`4711e1428eb0ac6751ee22db5fc04b417a24076e2ce433d59d53f242e8b714c4`.
Novo download nesta missão confirmou os mesmos bytes do M5. As páginas 4 e 22
foram renderizadas e conferidas visualmente, além da extração textual.
São tabelas de preparação eletrônica, não resultado observado. O extrator M5
não foi alterado para forçar correspondências.

### Outras fontes verificadas e limites

- [Editais 46 e 50 e publicações no DJe][S4]: 17 páginas, 457.536 bytes,
  SHA-256 `81dfd8f3025a9a898d7ba81b2fd8c4b9cd652b7a73f70395ba34113146810469`.
  Tratam de locais dispensados; a coluna Código é de local, não código municipal.
  Não foram usadas informações de pessoal presentes em outras páginas.
- [OpenAPI público do TRE-DF][S5], versão 1.0.0: SHA-256
  `0c8e242b40648f58ca3fccdbbcce9dfde7b2abc71df6727da0c931657d6f68d7`.
  Documenta somente rotas `/df/v1/zonas`, `/df/v1/locais/{zona}` e
  `/df/v1/secoes/{zona}/{local}`; sem país/ZZ/ano/turno no contrato. Não sustenta
  associação do exterior. A [página de acesso automatizado][S5-pagina] foi consultada.
- A [explicação institucional do TRE-DF][S6] distingue jurisdição consular,
  município e local de votação. É contexto, não prova de associação de um código.
- Buscas por códigos, nomes, votação manual, editais complementares, retificações
  e documentos consulares não forneceram uma fonte mais precisa que S1 para as
  duas pendências. Não se atribuiu país a partir de snippets ou páginas consulares
  genéricas. Os resultados por seção existentes foram usados por suas chaves,
  sem reabrir os ZIPs nacionais para processamento.

## Avaliação individual das 28 localidades

Em cada `verified`, a justificativa é a junção exata com S1 nos dois turnos,
literal documental revisado, corroboração S2 e cobertura integral das chaves
observadas. `r` indica número do registro CSV incluindo cabeçalho, **não** seção.
Todos os casos são zona 1. Campos integrais, referências individuais de Bruxelas,
local e turno estão em [M5_2_VALIDATION_SUMMARY.json](M5_2_VALIDATION_SUMMARY.json),
e as decisões em [zz_review_2026.json](../tools/geography/zz_review_2026.json).
Hipóteses na terceira coluna não constituem evidência identificadora.

| TSE | Nome original | Hipótese geográfica de pesquisa | Associação documental incorporada | Evidência/justificativa | Status final | Próxima ação |
| --- | --- | --- | --- | --- | --- | --- |
| 29173 | KATMANDU | Nepal | Nepal (`NP`) | [S1] r7/743, seção 494; endereço `NEPAL`; [S2] linha 27 | `verified` | — |
| 29254 | ABIDJÃ | Costa do Marfim | Costa do Marfim (`CI`) | [S1] r2805/2245, seção 1; bairro revisado `COSTA DO MARFIM`; [S2] linha 5 | `verified` | — |
| 29270 | ACCRA | Gana | Gana (`GH`) | [S1] r305/978, seção 3; bairro revisado `GANA`; [S2] linha 23 | `verified` | — |
| 29297 | ANCARA | Turquia | Turquia (`TR`) | [S1] r5405/4705, seção 495; bairro revisado `TURQUIA`; [S2] linha 12 | `verified` | — |
| 29300 | ARGEL | Argélia | Argélia (`DZ`) | [S1] r1934/200, seção 6; bairro revisado `ARGÉLIA`; [S2] linha 20 | `verified` | — |
| 29394 | BISSAU | Guiné-Bissau | Guiné-Bissau (`GW`) | [S1] r4514/1008, seção 28; bairro revisado `GUINÉ BISSAU`; [S2] linha 7 | `verified` | — |
| 29432 | BRUXELAS | Bélgica (nome); Luxemburgo (local) | Nenhuma para o agregado municipal | [S1] r4078/1462 e r2119/3587 (LU); demais chaves BE; [S3] pp. 4/22 | `multi_country_pending_section_aggregation` | Derivado independente por seção, reconciliado antes de ativar BE/LU |
| 29580 | CONCEPCIÓN | Paraguai; homônimos no Chile | Paraguai (`PY`) | [S1] r3062/1278, seção 96; bairro revisado `PARAGUAI`; [S2] linha 11 | `verified` | — |
| 29645 | DÍLI | Timor-Leste | Timor-Leste (`TL`) | [S1] r3993/4603, seção 380; bairro revisado `TIMOR LESTE`; [S2] linha 6 | `verified` | — |
| 29750 | HANÓI | Vietname | Vietname (`VN`) | [S1] r2236/3611, seção 1703; bairro revisado `VIETNAM`; [S2] linha 10 | `verified` | — |
| 29777 | HAVANA | Cuba | Cuba (`CU`) | [S1] r841/3316, seção 127; bairro revisado `CUBA`; [S2] linha 4 | `verified` | — |
| 29858 | KIEV | Ucrânia | Ucrânia (`UA`) | [S1] r4699/2691, seção 1183; bairro revisado `UCRÂNIA`; [S2] linha 16 | `verified` | — |
| 29912 | LAGOS | Nigéria | Nigéria (`NG`) | [S1] r2728/104, seção 150; bairro revisado `NIGÉRIA`; [S2] linha 9 | `verified` | — |
| 30171 | MUMBAI | Índia | Índia (`IN`) | [S1] r2454/1806, seção 1340; bairro revisado `INDIA`; [S2] linha 19 | `verified` | — |
| 30295 | PASO LOS LIBRES | Argentina | Argentina (`AR`) | [S1] r5259/5108, seção 348; bairro revisado `ARGENTINA`; [S2] linha 24 | `verified` | — |
| 30325 | PORT OF SPAIN | Trinidad e Tobago | Trinidad e Tobago (`TT`) | [S1] r306/1946, seção 352; bairro revisado `TRINIDAD TOBAGO`; [S2] linha 8 | `verified` | — |
| 30333 | PORTO PRÍNCIPE | Haiti | Haiti (`HT`) | [S1] r163/3503, seção 353; bairro revisado `HAITI`; [S2] linha 26 | `verified` | — |
| 30430 | RIO BRANCO | Uruguai; homônimo no Brasil | Uruguai (`UY`) | [S1] r2048/3584, seção 384; bairro revisado `URUGUAI`; [S2] linha 18 | `verified` | — |
| 30546 | SÓFIA | Bulgária | Bulgária (`BG`) | [S1] r5340/567, seção 1764; bairro revisado `BULGÁRIA`; [S2] linha 2 | `verified` | — |
| 30597 | TEERÃ | Irão | Irão (`IR`) | [S1] r2618/502, seção 1182; bairro revisado `IRÃ`; [S2] linha 22 | `verified` | — |
| 30686 | TRÍPOLI | Líbia (nome); Tunísia (endereço) | Nenhuma | [S1] r1127, seção 443, 1º turno: bairro LÍBIA versus endereço TUNÍSIA; [S2] linha 29 | `conflicting` | Obter BUEx/ata ou esclarecimento oficial da localização efetiva; não inventar 2º turno |
| 30708 | TUNIS | Tunísia | Tunísia (`TN`) | [S1] r4665/4111, seção 444; bairro revisado `TUNÍSIA`; [S2] linha 21 | `verified` | — |
| 30821 | WINDHOEK | Namíbia | Namíbia (`NA`) | [S1] r489/2092, seção 1524; bairro revisado `NAMÍBIA`; [S2] linha 25 | `verified` | — |
| 38962 | DAR ES SALAAM | Tanzânia | Tanzânia (`TZ`) | [S1] r935/4273, seção 558; bairro revisado `TANZÂNIA`; [S2] linha 28 | `verified` | — |
| 39102 | MASCATE | Omã | Omã (`OM`) | [S1] r852/2648, seção 712; bairro revisado `OMÃ`; [S2] linha 3 | `verified` | — |
| 99155 | PUERTO IGUAZÚ | Argentina | Argentina (`AR`) | [S1] r2177/207, seção 1504; endereço `ARGENTINA`; [S2] linha 17 | `verified` | — |
| 99180 | NASSAU | Bahamas | Bahamas (`BS`) | [S1] r1614/623, seção 1228; endereço `BAHAMAS`; [S2] linha 14 | `verified` | — |
| 99473 | BAREIN | Bahrein | Bahrein (`BH`) | [S1] r2962/1436, seção 1327; endereço `BAHRAIN`; [S2] linha 15 | `verified` | — |

### Por que as 27 localidades não tinham junção no M5

As 27 pendências sem junção coincidem com localidades da planilha de votação
manual S2, inclusive Trípoli. Suas seções principais observadas estão ausentes
do recorte eletrônico S3, mas estão identificadas em S1. O cadastro agora permite
separar a identidade eleitoral do rótulo de cidade e do total de aptos.
Nos 26 casos resolvidos, a mesma chave de seção está documentada **em ambos os turnos**;
não se extrapolou um registro do primeiro para o segundo.

Não foi encontrada evidência de que esses 26 casos exigissem criação posterior
de localidade, troca de identificador, leitura de seção agregada ou correção de
extração de tabela. O problema sustentado é a cobertura da fonte eletrônica
usada anteriormente. Rio Branco inclui a agregada 3468 → principal 384 no
cadastro; os votos observados/M4 estão na principal 384 e são somados uma vez.
Trípoli soma a essa causa uma divergência semântica de país e a ausência de registro
M4 no segundo turno. Bruxelas tem causa diferente e é discutida a seguir.

## Bruxelas — código 29432

1. **Mesmo código TSE? Sim.** As 14 seções observadas estão sob `29432`, zona 1,
   nas eleições `6257` e `6258`. S1 repete os mesmos identificadores por turno.
2. **Edital interpretado corretamente? Sim nas linhas relevantes.** Conferência
   visual da página 4 mostra Bélgica/Prefeitura de Saint-Gilles; página 22 mostra
   Luxemburgo/Prefeitura de Esch-sur-Alzette, com a expressão administrativa
   “EM BRUXELAS” no texto do local. Não se confundiu essa expressão com país físico.
3. **Principais ou agregadas?** As principais de BE são 1935–1940, 3097, 3212,
   3293, 3356, 3455 e 3681. As principais de LU são **1946 e 1947**.
   No edital, 3765 e 3438 são suas agregadas; não geraram atribuição independente.
   Em S1, 1946/1947 têm `NR_SECAO_PRINCIPAL=-1`, tipo Principal, local **1058**.
   As 12 principais belgas usam local **1015**.
4. **Erro de extração ou mudança de país?** Não há suporte para erro de extração
   nessas duas linhas. S1 corrobora o endereço `HÔTEL DE VILLE, L-4002,
   ESCH-SUR-ALZETTE, LUXEMBURGO`, nos registros 4078/1462 (1º) e 2119/3587 (2º).
   O campo `NM_BAIRRO` continua “BÉLGICA” inclusive nessas linhas: referência
   administrativa ampla, inadequada para definir automaticamente o país físico.
   Não se demonstrou uma mudança entre turnos.
5. **Um município eleitoral pode reunir locais em países diferentes?** Este
   cadastro concreto demonstra isso: mesmo código 29432, dois locais e dois países
   físicos documentados. Não se generaliza o fato para outras localidades.
6. **País por seção?** É identificável para essas 14 seções cadastradas nos dois
   turnos, com concordância S1/S3 sobre a localização. Ainda não foi produzida
   nesta missão uma distribuição auditada dos votos BE/LU por seção.

Portanto, a explicação mais sustentada é **abrangência multinacional do município
eleitoral**, com diferença entre país físico e rótulo administrativo. O conflito
do agregado municipal não se resolve escolhendo o país majoritário.

### Extensão proposta, deliberadamente não implementada

O M4 embarcado contém somente o agregado municipal. Para separar Bruxelas,
um novo derivado deverá ler `results` e `section_totals` do SQLite **somente
leitura**, preservando sua linhagem, com chave
`ano/eleição + localidade TSE + zona + seção + turno → país físico`.
Antes de fazê-lo, documentar chaves das tabelas, substituições/contingências,
categorias ausentes e a relação exata entre cada resultado e seção. A soma das
partições por seção deverá reproduzir candidatos, campos e disponibilidade
do municipal M4, além do exterior completo. Cada linha tem exatamente um destino.

Será necessário um contrato novo de resultados por país, tratamento explícito
de localidade multinacional na navegação, e retirada do agregado 29432 da rota
municipal de agregação para impedir dupla contagem. O derivado atual não mistura
duas granularidades. Não houve divisão proporcional dos 5.091/5.326 votos de
Bruxelas; eles continuam integralmente no residual.

## Trípoli — divergência distinta

S1, registro 1127, liga a seção 443 ao código 30686 no primeiro turno. O local é
Embaixada do Brasil em Túnis e o endereço termina em **TUNÍSIA**, enquanto
`NM_BAIRRO` registra **LÍBIA**. S2, linha 29, também combina país Líbia e local
Embaixada do Brasil em Túnis. Isso pode refletir jurisdição/atendimento consular
ou instalação física fora da Líbia, mas não se escolheu uma interpretação sem
documentação adicional. É necessária evidência de operação da seção (BUEx/ata)
ou esclarecimento do TRE-DF/MRE sobre o critério de país.

Não há resultado M4 para esse código no segundo turno. Mesmo uma linha cadastral
de outro turno não criaria votos, aptos ou abstenção ausentes no M4. O residual
contém dois votos válidos/contabilizados dessa localidade apenas no primeiro turno.

## Reconciliação executada

O novo derivado usa os JSONs M4 `e4e9c9cb5189ab5d4e124bfc`, cujo manifesto tem
SHA-256 `c4dcddacb8092ff1dfffb35b07b739dbf360232e701e080087f52a4a09e20637`.
O exportador valida hashes e vínculo de versão antes de somar. Nenhum ZIP de
resultados foi reimportado; o SQLite serviu apenas para identidades.

### Mudança na soma atribuída a países

| Campo | Antes 1º | Depois 1º | Acréscimo 1º | Antes 2º | Depois 2º | Acréscimo 2º |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Válidos | 325.342 | 326.028 | 686 | 365.728 | 366.433 | 705 |
| Brancos publicados | 5.745 | 5.753 | 8 | 4.612 | 4.624 | 12 |
| Nulos publicados | 4.884 | 4.892 | 8 | 5.043 | 5.060 | 17 |
| Contabilizados | 335.971 | 336.673 | 702 | 375.383 | 376.117 | 734 |
| Comparecimento | 335.971 | 336.673 | 702 | 375.383 | 376.117 | 734 |
| Aptos | 904.237 | 905.936 | 1.699 | 904.383 | 906.083 | 1.700 |
| Abstenção | 568.266 | 569.263 | 997 | 529.000 | 529.966 | 966 |
| Seções | 1.268 | 1.294 | 26 | 1.268 | 1.294 | 26 |

### Países, residual e exterior

| Campo | Países 1º | Residual 1º | Exterior 1º | Países 2º | Residual 2º | Exterior 2º |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Válidos | 326.028 | 4.977 | 331.005 | 366.433 | 5.218 | 371.651 |
| Brancos publicados | 5.753 | 63 | 5.816 | 4.624 | 51 | 4.675 |
| Nulos publicados | 4.892 | 53 | 4.945 | 5.060 | 57 | 5.117 |
| Contabilizados | 336.673 | 5.093 | 341.766 | 376.117 | 5.326 | 381.443 |
| Comparecimento | 336.673 | 5.093 | 341.766 | 376.117 | 5.326 | 381.443 |
| Aptos | 905.936 | 10.103 | 916.039 | 906.083 | 10.075 | 916.158 |
| Abstenção | 569.263 | 5.010 | 574.273 | 529.966 | 4.749 | 534.715 |
| Seções | 1.294 | 15 | 1.309 | 1.294 | 14 | 1.308 |

Brancos/nulos são somas de campos publicados, **não totais completados com zeros**.
Cobertura exterior preservada: brancos 1.192/1.309 e 1.165/1.308; nulos 1.180/1.309
e 1.194/1.308. O resumo JSON conserva vetores completos antes/depois, inclusive
os **13 candidatos do primeiro turno e dois do segundo**, os campos `reported`,
`available_sections` e as seções. As igualdades foram executadas com inteiros;
não se verificou apenas uma soma de votos válidos.

Há 143 localidades mapeadas em cada turno. O residual tem duas no primeiro e uma
no segundo. Nenhuma localidade é simultaneamente país e residual. Ausência de
turno/candidato/categoria não se torna linha zero. A visão Mundo permanece usando
o exterior original; Brasil inclui exterior uma única vez. Percentuais de país
continuam indisponíveis enquanto a correspondência global for parcial.

## Código, contratos e versões

Commit de implementação: **`ae82421`** — `feat(geo): verify 26 overseas localities
with official section registers`. O segundo commit local reúne este relatório,
o resumo JSON e os índices; seu hash pode ser obtido com `git log -2 --oneline`.

- `tools/geography/zz_review_2026.json`: 28 decisões explícitas, literais, campos
  revisados, fonte e referências S2. Os nomes são informativos.
- `tools/geography/resolve_overseas.py`: construtor offline; recusa fonte/hash,
  baseline, duplicatas, seções ausentes/não principais, diferença de local/turno,
  campos divergentes e destino já existente. Mantém os 117 registros anteriores.
- `pipelines/tse_importer/overseas_evidence.py`: valida contratos v1/v2, documentos,
  país por literal revisado e identidades; recusa associação somente por nome.
- `pipelines/tse_importer/country_exporter.py`: regras `country-2`, hash das regras,
  vínculo M4 e prontidão herdada; partição/reconciliação exatas e saída independente.
- `tools/geography/audit_countries.py`: reproduz o novo derivado duas vezes,
  confronta o histórico e gera o resumo auditável das 28 investigações.
- `assets/geo/overseas_correspondence.json` e `manifest.json`: contrato de
  correspondência **v2**, pacote **`geography-2026-2`**. O manifesto continua schema 1.
- Flutter: `country_evidence.dart`, `geographic_catalog.dart` e
  `explorer_controller.dart` admitem evidência oficial por identificadores e
  recusam contagem de seções/turnos incompatível, mantendo a localidade no residual.
  O hash fixado por `GeographicAssets` foi atualizado.
- Testes: `test_overseas_evidence.py`, `test_country_exporter.py`,
  `test_geography_assets.py`, `country_evidence_test.dart`,
  `geographic_assets_test.dart`, `geographic_explorer_test.dart` e
  `integration_test/offline_results_test.dart`.

Não foram modificados os renderizadores, verdes, tipografia, zoom, reset,
malhas, duas raízes Brasil/Mundo ou biblioteca de mapas. As mensagens e listas
existentes calculam a nova cobertura e os países a partir dos dados verificados.
O contrato v1 continua legível; evidência nova exige v2. IDs legados de derivados
não foram usados para conteúdo novo. O ID novo inclui hash das regras em texto
normalizado, além do manifesto M4 e correspondência.

### Hashes finais

- Correspondência: 77.035 bytes; SHA-256 `028df778ddbca88b1959541a287221d8cb869dcdfa5eecac6bf33abdf3e5f699`.
- Manifesto geográfico: 3.590 bytes; SHA-256 `ab4be0d225aa2209c976ec2238c1faa1a4c922d8d2f80ac8f87ba078f5746c47`.
- Decisões revisadas: 21.150 bytes; SHA-256 `54959ddb420a8b717c9888518dc562c129b0f0812d30651bd677432aff90afe1`.
- Resumo de reconciliação: 44.598 bytes; SHA-256 `e9f05c81cfeb1745eb071e0196615b8ea44101440f1d79cc870a2fb036c0e124`.

Derivado independente final: **`746f675cc3b364609946ff7b`**, regras `country-2`,
**84.162 bytes** em `countries.json` + manifesto,
sob `.local/m5_2/country-export-final/releases/`. O manifesto e hash do payload
estão integralmente no resumo JSON. Repetir a exportação produziu os mesmos bytes/ID;
reconstruir a geografia em novo diretório produziu o mesmo hash de manifesto.
O histórico M5 `f3116546104b1248b29011ba` e seus arquivos permanecem intactos.

### Preservação

O inventário antes/depois abrangeu **255 arquivos, 7.803.563.158 bytes**, incluindo
originais TSE e backups, releases processadas, SQLite, mini-base instalada,
derivado histórico e geografia. **253 ficaram idênticos em SHA-256, tamanho,
mtime e identidade de arquivo**; somente os dois assets geográficos autorizados
(manifesto/correspondência) diferem. Os 32 JSONs eleitorais M4 permanecem idênticos.
O SQLite nacional mantém 935.424.000 bytes e SHA-256
`c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4`.
Recibos detalhados em `.local/m5_2/preservation-before.json`,
`preservation-after.json` e `preservation-diff.json`.

Os 117 registros de evidência originais têm digest canônico
`722352ad52031de5bd6839f795954633478a9364206bb80244d628df473fffbb`, protegido
por teste. Os 5.571 pontos municipais e Natural Earth mantêm seus hashes M5.
Não houve reinstalação/limpeza de releases ou originais.

## Testes, builds e funcionamento offline

| Verificação local | Resultado |
| --- | --- |
| Ruff format/check | 36 arquivos; passou |
| pytest completo | 167 passaram, 2 integrações oficiais opt-in puladas; 98,04 s |
| Regressão após guarda de tipo Principal e manifesto final | 34 passaram |
| Dart format | 38 arquivos; passou |
| Flutter analyze --no-pub | Zero issues |
| Flutter test --no-pub --coverage | 127 passaram; 7 smokes reais opt-in pulados |
| Smoke Windows com rootBundle real | 1 passou; 0 tentativas HTTP da aplicação |
| Windows release | Passou; compilação 46,9 s |
| Web release | Passou; compilação 40,3 s |
| APK debug | Passou; Gradle 29,5 s |
| Reconstrução geográfica e exportação repetidas | Mesmos bytes/ID |
| git diff --check | Passou |

Python 3.12, Flutter 3.47.8/Dart 3.13.7 locais. O smoke real exercitou Brasil/UF/
município, Mundo, os 100 países ativos, Katmandu nos três modos, navegação e
deep links, país anterior, Bruxelas residual e bloqueio de clientes HTTP.
O tempo de build não é medida de desempenho em execução.

As verificações solicitadas 1–8 são cobertas pelos fixtures de evidência/registro
e hashes: código, seção/turno, nome insuficiente, duplicatas, contradições,
ausências e abrangência multinacional. Itens 9–12: partição disjunta, residual,
reconciliação de todos os vetores e países ativos. Itens 13–19: testes Flutter
de listas/painel/deep links/três modos, contrato/hash, versão incompatível,
recusa de sobreposição/preservação, HTTP bloqueado e digest dos 117 registros.
Item 20: auditoria das 5.571 chaves e hashes intactos de pontos/resultados.
Fixtures são pequenos e fictícios; a CI não baixa fonte oficial. Workflows
remotos não foram executados, pois não houve push.

O primeiro comando Flutter tentou resolver pacotes online e falhou no sandbox;
a execução final usou `pub get --offline`, cache local e `--no-pub`. Um erro de
tipagem no novo fixture de duplicata e avisos de estilo foram corrigidos antes
das verificações finais. Não houve falha eleitoral mascarada por ajuste de dados.

### Tamanho e inspeção dos pacotes

| Pacote | Bytes | Conferência |
| --- | ---: | --- |
| Windows release, diretório | 35.197.073 | 32 JSONs reais + 5 arquivos geográficos idênticos à origem |
| Web release, diretório | 48.984.352 | 32 JSONs reais + 5 arquivos geográficos idênticos à origem |
| APK debug | 155.973.697 | Mesma conferência; geografia comprimida 515.567 bytes |

Nenhum pacote contém JSON eleitoral sintético. Os cinco assets geográficos
empacotados passam de **1.338.504 para 1.360.599 bytes**,
um acréscimo de **22.095 bytes descomprimidos**. O derivado `countries.json`
separado não é embarcado; Flutter agrega os JSONs municipais já instalados.
Os tamanhos globais também incluem runtime/código; não medem somente esta mudança.
SHA-256 do APK: `05a7d798aff999c3d9861a1f84a452826001d3e22ca9e8340dd52aac8c936911`.

## Reprodução e prévia real

As fontes auxiliares e recibos ficam em `.local/m5_2/`, ignorados pelo Git.
O baseline geográfico M5 foi copiado integralmente antes de qualquer edição para
`.local/m5_2/geography-2026-1/`; pode ser recuperado dos assets no commit `f7f8011`
sem modificar a working tree. Não reutilizar destinos já existentes.

```powershell
# Reproduzir em NOVO diretório; sem rede e sem importação de resultados.
.venv/Scripts/python.exe tools/geography/resolve_overseas.py `
  --baseline .local/m5_2/geography-2026-1 `
  --source apps/votoaberto_flutter/assets/data/real `
  --register .local/m5_2/eleitorado-ZZ.csv `
  --sqlite data/processed/national-2026/releases/6305f74561d4687a23bd3054/election.sqlite `
  --output .local/m5_2/geography-outro

.venv/Scripts/python.exe tools/geography/audit_countries.py `
  --source apps/votoaberto_flutter/assets/data/real `
  --correspondence apps/votoaberto_flutter/assets/geo/overseas_correspondence.json `
  --previous .local/m5/country-export/releases/f3116546104b1248b29011ba `
  --register .local/m5_2/eleitorado-ZZ.csv `
  --sqlite data/processed/national-2026/releases/6305f74561d4687a23bd3054/election.sqlite `
  --output .local/m5_2/country-export-repro `
  --report .local/m5_2/audit-repro.json

# Prévia já compilada; manter toda a pasta Release junto do executável.
& .local/m5_2/preview/apps/votoaberto_flutter/build/windows/x64/runner/Release/votoaberto.exe

# Web: servidor estático local, sem backend ou API de resultados.
.venv/Scripts/python.exe -m http.server 18767 --bind 127.0.0.1 `
  --directory .local/m5_2/preview/apps/votoaberto_flutter/build/web
# http://127.0.0.1:18767/#/mundo/NP/localidade/29173?modo=comparacao
```

Para novos builds reais, usar `tools/geography/prepare_preview.py --target
.local/<novo-diretorio>`, `flutter pub get --offline` e
`tool/embedded_build.py windows|web|apk --mode real -- --no-pub` nessa cópia.
O smoke é `tool/embedded_build.py native-test --mode real -- --no-pub`.
O script copia fontes/mini-base e não instala dados sobre releases antigas.

## Limitações e próximos passos

- Concluir a atribuição de Bruxelas exige arquitetura de resultados por seção,
  com reconciliação independente e navegação multinacional; somente localizações
  documentais não autorizam repartir o agregado M4.
- Trípoli depende de documento operacional ou esclarecimento oficial; mantém
  conflito Líbia/Tunísia e segundo turno ausente no M4.
- S1 é um retrato cadastral datado. Atribuições não são regras para futuras eleições
  ou futuras versões desse CSV. Hash diferente exige nova revisão.
- Resultados nacionais continuam `not_ready`: autenticação da origem e confiança
  de referências históricas são questões independentes desta geografia.
- Android foi compilado, sem teste físico/emulador. Web usa assets estáticos
  próprios e dispensa chamadas HTTP para API de resultados; a primeira carga e
  reinício offline do navegador não são garantidos. PWA permanece desabilitada.
- Estética M5.1 preservada por arquivos de renderização/estilo intactos e testes
  de regressão; não se realizou uma nova avaliação com leitor de tela.

[S1]: https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip
[S1-catalogo]: https://dadosabertos.tse.jus.br/dataset/eleitorado-2026/resource/300626b4-2b24-4d2e-b4fc-46b569cfffe5
[S2]: https://www.tre-df.jus.br/eleicoes/arquivos-eleicoes-2026/secoes_eleitorais___exterior___votacao_manual/@@download/file
[S2-noticia]: https://www.tre-df.jus.br/comunicacao/noticias/2026/Setembro/eleicoes-2026-consulte-os-locais-e-as-secoes-eleitorais-para-votacao-no-exterior
[S3]: https://www.tre-df.jus.br/comunicacao/noticias/arquivos/edital-carga_e_lacracao_das_urnas_eletronicas__df_e_zz____2026/@@download/file
[S4]: https://www.tre-df.jus.br/eleicoes/arquivos-eleicoes-2026/edital_n-__46_e_50_2026___secoes_dispensadas/@@download/file
[S5]: https://apps.tre-df.jus.br/swagger/publico.json
[S5-pagina]: https://www.tre-df.jus.br/transparencia-e-prestacao-de-contas/acesso-automatizado-as-informacoes/disponibilizacao-para-sistemas-externos
[S6]: https://www.tre-df.jus.br/comunicacao/noticias/2026/Setembro/como-a-justica-eleitoral-organiza-as-eleicoes-no-exterior
