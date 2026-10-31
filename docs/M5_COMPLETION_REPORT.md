# M5 — Explorador geográfico Brasil e Mundo

Entrega local em 30/10/2026, com cobertura exterior **parcial e explícita**.
A interface, o mapa municipal, a navegação mundial e as validações estão
implementados. A correspondência confirma 117 das 145 localidades do exterior;
28 permanecem sem país atribuído, com consulta eleitoral preservada.

## Branch, commits e escopo

Repositório `UrnaLivre/votoaberto`, branch única
`feat/m5-geographic-explorer`, criada da `main` atualizada `a97d6e7` após fetch.
Não houve outra branch, push, PR ou merge. A cópia para builds isolados não é
worktree Git nem branch.

| Commit local | Conteúdo |
| --- | --- |
| `4ef6018` | Pontos oficiais, correspondência exterior conservadora, manifesto/hash, exportador, testes Python e proveniência |
| `65f9f50` | Brasil/Mundo, mapa mundial, marcador municipal, rotas, resumo/comparação, testes, CI e preparação de builds isolados |

Este relatório, o resumo numérico, o índice README e a formatação final do
agregador integram o commit de fechamento, identificável em `git log -1`.
O fechamento não altera a lógica compilada nos builds verificados.

A aba Explorar os Dados e o estado `ExplorerView.insights` foram removidos.
Links antigos com `visao=insights` migram para `summary`, preservando caminho,
turno e demais parâmetros. Links técnicos antigos do exterior também continuam
funcionando, sem expor ZZ como título público. Temas, gráficos relevantes,
comparação por identidade de candidato e busca/navegação M4 foram preservados.

## Fontes e licenças

O [guia técnico](GEOGRAPHIC_EXPLORER.md) documenta URLs exatos, inspeção das
versões efetivas, junções, transformações, condições de uso e reprodução.
O [manifesto geográfico](../apps/votoaberto_flutter/assets/geo/manifest.json)
registra os hashes dos arquivos/fontes. Seu SHA-256 é
`e7e5f78f267c2f29245a3df1ef13172dedffb9a4aee7be3c71316ae117143b6b`.

| Fonte | Versão efetivamente inspecionada | Condição registrada |
| --- | --- | --- |
| TSE, correspondência TSE/IBGE | CSV gerado em 25/10/2026 09:00:09; ZIP atualizado em 25/10/2026 | Creative Commons Attribution declarada pelo catálogo, sem versão especificada |
| IBGE, Localidades do Brasil | Censo 2022; GeoPackage publicado em 19/11/2025 | Dado público, reutilização com atribuição; sem inventar licença CC/SPDX |
| TRE-DF, três planilhas do exterior | Publicação de 02/09/2026; ZIPs contêm XLSX | Documentos oficiais públicos, com atribuição ao órgão |
| TRE-DF, edital de carga e lacração | PDF atualizado em 15/09/2026 15:32:26 UTC | Ato oficial público, com atribuição; não relicenciado como MIT |
| Natural Earth | Countries/Map Units 5.1.1, 1:50m; também investigado 1:110m | Domínio público, inclusive derivados |

Natural Earth foi simplificado em 0,04 grau, com preservação topológica antes do
arredondamento a quatro casas. Polígonos múltiplos, ilhas, anéis interiores e
antimeridiano são tratados pelo renderizador. As fronteiras não constituem
reconhecimento oficial de disputas territoriais. Não há biblioteca pesada de mapas,
serviço de tiles ou chamada geográfica em execução.

## Cobertura municipal

Foram auditados **5.571/5.571 identificadores domésticos** da mini-base M4,
todos com correspondência oficial por UF/códigos e ponto IBGE confirmado.
Zero municípios sem ponto nesta versão; o código continua omitindo o marcador
para qualquer chave futura ausente ou ambígua. A votação permanece consultável.

Os códigos TSE e IBGE ficam separados. O catálogo preserva o código M4, seu
equivalente textual oficial com cinco dígitos e o IBGE relacionado. Nenhuma
associação é obtida por semelhança de nome. Duplicatas idênticas de capitais no
GeoPackage são consolidadas; posições divergentes seriam recusadas.

DF (`97012` → `5300108`) e Fernando de Noronha (`30015` → `2605459`) usam
ponto representativo; Boa Esperança do Norte/MT (`5101837` IBGE) também está
coberta. Os outros pontos são sedes municipais. Transformação SIRGAS2000 → WGS84
(operação com precisão declarada de 1 m), arredondamento a seis casas, sem
atribuir essa precisão à fonte original ou à malha de apresentação.

Ao selecionar município, a câmera anima para a UF e mostra o marcador. Para
Noronha, o enquadramento inclui o ponto insular além do continente. A troca de
município conserva a instância do mapa, e Voltar respeita município → UF → Brasil.
Os pontos não representam urnas nem locais de votação. Contagens por UF e
metadados completos estão em [M5_VALIDATION_SUMMARY.json](M5_VALIDATION_SUMMARY.json).

## Exterior: resultado auditável e pendências

As planilhas prioritárias do TRE-DF têm país/cidade/endereço/quantidades, mas
não identificam individualmente as seções nem o município TSE. O campo Código
da planilha de dispensadas é de local de votação e se repete, portanto não foi
tratado como código municipal. As tabelas/metadados do SQLite não contêm país.

O edital de carga fornece país e **seções principais**. A junção usa essas
seções e as identidades do SQLite somente leitura: abrangência exterior,
zona `1` e seção única por localidade na união dos turnos. Cada associação
guarda a página e as chaves verificadas. Seções agregadas não são usadas para
atribuir país. Não se infere país pelo nome da cidade, consulado ou endereço.

Há 1.282 seções principais únicas no planejamento eletrônico; 1.309 seções
distintas observadas; 1.281 compartilhadas, 28 somente observadas e uma somente
planejada (936). A seção 3310 se repete de forma idêntica no edital. Planejamento
de carga do primeiro turno e votação observada, incluindo manual, não são o mesmo
universo.

**117 localidades confirmadas, 80 países/territórios com votação em ambos os
turnos** no subconjunto verificado. Há 117 registros localidade/turno mapeados
em cada turno. O residual tem 28 no primeiro e 27 no segundo; TRÍPOLI (`30686`)
não possui registro no segundo turno. Não foi criada linha para completá-lo.
O código admite países que só tenham registros em um dos turnos, testados com fixture.

As 145 localidades, seus nomes e evidências ficam na
[correspondência versionada](../apps/votoaberto_flutter/assets/geo/overseas_correspondence.json).
O resumo numérico lista os códigos de todas as localidades mapeadas por país.
As 28 pendências são enumeradas abaixo. Nenhuma recebeu um país presumido.

| Código TSE | Localidade eleitoral | Pendência |
| --- | --- | --- |
| `29173` | KATMANDU | Sem junção verificável por seção |
| `29254` | ABIDJÃ | Sem junção verificável por seção |
| `29270` | ACCRA | Sem junção verificável por seção |
| `29297` | ANCARA | Sem junção verificável por seção |
| `29300` | ARGEL | Sem junção verificável por seção |
| `29394` | BISSAU | Sem junção verificável por seção |
| `29432` | BRUXELAS | Conflito BE/LU nas chaves de seção |
| `29580` | CONCEPCIÓN | Sem junção verificável por seção |
| `29645` | DÍLI | Sem junção verificável por seção |
| `29750` | HANÓI | Sem junção verificável por seção |
| `29777` | HAVANA | Sem junção verificável por seção |
| `29858` | KIEV | Sem junção verificável por seção |
| `29912` | LAGOS | Sem junção verificável por seção |
| `30171` | MUMBAI | Sem junção verificável por seção |
| `30295` | PASO LOS LIBRES | Sem junção verificável por seção |
| `30325` | PORT OF SPAIN | Sem junção verificável por seção |
| `30333` | PORTO PRÍNCIPE | Sem junção verificável por seção |
| `30430` | RIO BRANCO | Sem junção verificável por seção |
| `30546` | SÓFIA | Sem junção verificável por seção |
| `30597` | TEERÃ | Sem junção verificável por seção |
| `30686` | TRÍPOLI | Sem junção verificável por seção |
| `30708` | TUNIS | Sem junção verificável por seção |
| `30821` | WINDHOEK | Sem junção verificável por seção |
| `38962` | DAR ES SALAAM | Sem junção verificável por seção |
| `39102` | MASCATE | Sem junção verificável por seção |
| `99155` | PUERTO IGUAZÚ | Sem junção verificável por seção |
| `99180` | NASSAU | Sem junção verificável por seção |
| `99473` | BAREIN | Sem junção verificável por seção |

Em BRUXELAS, as seções observadas do mesmo código encontram referências a BE
na página 4 e a LU na página 22 do edital. O código inteiro fica sem país, em vez
de escolher por maioria ou nome. As outras 27 não têm junção verificável nessa
fonte. São necessárias fontes oficiais com código de localidade ou chaves
zona/seção que cubram essas localidades e esclareçam a contradição. As planilhas
nominais, isoladamente, não resolvem a ausência.

Escócia/Reino Unido são consolidados em ISO GB. Hong Kong, Taiwan, Palestina e
Guiana Francesa preservam a identidade cartográfica ISO pertinente à associação;
isso não constitui declaração de soberania.

## Reconciliação eleitoral

O derivado novo é `f3116546104b1248b29011ba`, regras `country-1`, vinculado à
release M4 `e4e9c9cb5189ab5d4e124bfc` e ao hash da correspondência. Foi criado
separadamente em `.local/m5/country-export/releases/`, com `countries.json` e
manifesto; 67.654 bytes. Repetir a exportação reproduziu os mesmos bytes/ID.
Versões existentes divergentes são recusadas. Não se alterou o instalador M4.

As comparações usam inteiros e verificam **todos** os candidatos, categorias,
seções e disponibilidade por campo nos dois turnos:

- soma dos países = soma independente das localidades efetivamente mapeadas;
- soma dos países + residual sem país = total exterior M4;
- a soma dos países, isoladamente, **não é** o total exterior completo.

| Campo | Países 1º | Residual 1º | Exterior 1º | Países 2º | Residual 2º | Exterior 2º |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Válidos | 325.342 | 5.663 | 331.005 | 365.728 | 5.923 | 371.651 |
| Brancos publicados | 5.745 | 71 | 5.816 | 4.612 | 63 | 4.675 |
| Nulos publicados | 4.884 | 61 | 4.945 | 5.043 | 74 | 5.117 |
| Contabilizados | 335.971 | 5.795 | 341.766 | 375.383 | 6.060 | 381.443 |
| Comparecimento | 335.971 | 5.795 | 341.766 | 375.383 | 6.060 | 381.443 |
| Aptos | 904.237 | 11.802 | 916.039 | 904.383 | 11.775 | 916.158 |
| Abstenção | 568.266 | 6.007 | 574.273 | 529.000 | 5.715 | 534.715 |
| Seções | 1.268 | 41 | 1.309 | 1.268 | 40 | 1.308 |

Brancos e nulos acima são somas dos registros publicados e continuam parciais.
Cobertura exterior: brancos 1.192/1.309 seções no primeiro turno e 1.165/1.308
no segundo; nulos 1.180/1.309 e 1.194/1.308. Os outros campos agregados têm
cobertura de seção integral dentro do recorte observado. Isso não atesta
exaustividade de todas as seções possíveis nem autenticação das fontes.

Foram conferidos os 13 candidatos publicados no primeiro turno e os dois do
segundo. Ausência de registro não vira zero nem candidatura participante
inventada. Vetores completos por candidato e controles de disponibilidade
estão no resumo JSON. Percentuais não são exportados, e percentuais de país
ficam indisponíveis na UI enquanto houver lacunas de correspondência. O total
Mundo continua usando o exterior original, e o total Brasil continua incluindo-o
uma única vez.

## Tamanho e desempenho

| Asset novo | Bytes |
| --- | ---: |
| `municipal_locations.json` | 331.831 |
| `overseas_correspondence.json` | 56.691 |
| `world.geojson` | 697.008 |
| `manifest.json` | 1.839 |
| **Total adicional empacotado** | **1.087.369** |

São aproximadamente 1,04 MiB adicionais descomprimidos. No APK, esses quatro
arquivos ocupam **421.239 bytes comprimidos**. Nenhum polígono municipal completo
foi incorporado. A mini-base eleitoral continua com 4.475.495 bytes.

| Pacote final na área isolada | Bytes | Dados eleitorais originais | Geografia adicional |
| --- | ---: | ---: | ---: |
| Web release, diretório | 48.976.505 | 4.475.495 | 1.087.369 |
| Windows release, diretório | 35.207.714 | 4.475.495 | 1.087.369 |
| APK debug, arquivo | 155.955.809 | 1.042.490 comprimidos | 421.239 comprimidos |

Tamanhos totais incluem runtime, código, fontes e metadados do build. O acréscimo
dos assets é medido diretamente; diferenças de tamanho total frente a pacotes
históricos M4 não isolam o efeito da geografia, especialmente em APK debug.
Não se atribui eventual redução do APK aos recursos do M5.

SHA-256 do APK:
`e2a37d72f3741c9bbeff1b905f459d71f3e223b8e4ed0c3baf0bec6d2ceaa625`.
Os três pacotes foram inspecionados por arquivo: 32 JSONs eleitorais reais com
hashes idênticos, zero JSON eleitoral sintético e quatro assets M5 idênticos ao
manifesto. Os builds finais usam o código funcional de `65f9f50`.

Diagnóstico em VM Flutter: leitura/verificação/decodificação do catálogo 83,827 ms;
mapa mundial 71,149 ms; uma observação, sem assertion de tempo dependente da máquina.
O mapa mundial tem 250 grupos cartográficos, incluindo unidades neutras, e é
lido sob demanda. Exportação repetida: 1,104 s, pico de alocações Python medido
por tracemalloc de 19.274.785 bytes; não é pico de memória total do processo.

No smoke Windows debug com `rootBundle` real: quadro nacional estabilizado
1.334,194 ms; troca de turno 491,409 ms; UF 962,202 ms; busca municipal 399,457 ms;
seleção municipal 586,796 ms; Mundo 440,796 ms; país 734,045 ms. Os números incluem
pumps/estabilização do harness, não medem partida fria, FPS, release ou Android.

## Testes e builds

| Verificação local | Resultado |
| --- | --- |
| Ruff format/check, 32 arquivos Python | Passou |
| pytest completo | 146 passaram, 2 integrações oficiais opt-in puladas; 381,32 s |
| Regressão final exportador/hashes | 13 passaram |
| Dart format, 33 arquivos | Passou |
| Flutter analyze | Zero issues |
| Flutter test com coverage | 83 passaram; 7 smokes de dados reais opt-in pulados |
| Smoke real Windows, separado dos fixtures | 1 passou; 0 tentativas HTTP da aplicação |
| Web release | Passou; 106,5 s |
| Windows release | Passou; 92,5 s |
| APK debug | Passou; 132,0 s |
| `git diff --check` | Passou |

Flutter 3.47.8/Dart 3.13.7 e Python 3.12 locais. A CI continua usando fixtures
eleitorais pequenos e jobs Web, Windows e Android; workflows não foram executados
remotamente, pois não houve push. Não se reimportaram ZIPs oficiais nos testes.

Cobertura dos requisitos de teste:

| Itens solicitados | Evidência |
| --- | --- |
| 1–2: aba removida e links antigos | `geographic_explorer_test.dart`, enum/router |
| 3–6: TSE/IBGE, coordenadas, chave ausente, marcador/zoom | `test_geography_assets.py`, `geographic_assets_test.dart`, `geographic_explorer_test.dart` |
| 7–10: Brasil/Mundo, países ativos/inativos, país/localidade | `geographic_explorer_test.dart`, smoke nativo real |
| 11–13: totais por turno, países versus exterior, ausências/parciais | `test_country_exporter.py`, fixtures Dart e reconciliação real versionada |
| 14–16: hierarquia, deep links, corrida assíncrona, teclado/responsividade | testes de Explorer/controller/mapa; Web real em três viewports |
| 17–18: assets locais e nenhuma API | AssetBundle verificado, guardas estáticas e `HttpOverrides` recusando clientes no smoke Windows |
| 19–20: hashes/versionamento e releases anteriores | testes de adulteração, determinismo/recusa de sobreposição, suíte M4 e recibos de preservação |

QA Web real em 1366×768, 390×844 e 768×1024: país/mapa/painel, Noronha, DF,
comparação, alternância Brasil/Mundo e tema escuro. Sem overflow observado nesses
recortes. Capturas em `.local/m5/qa-*.png`. Sem avaliação externa com leitor de
tela ou Android físico. Os testes de layout também cobrem 280 e 1920 pixels.

## Preservação comprovada

Antes/depois foram comparados **134 arquivos, 2.338.608.706 bytes**, nas áreas
de releases processadas, mini-base instalada e insumos locais: mesmos tamanhos,
SHA-256, mtime e identidade de arquivo. Os 32 JSONs instalados, releases e
ponteiros anteriores não foram apagados, substituídos ou reinstalados.

SQLite nacional: **935.424.000 bytes**, SHA-256
`c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4`,
inalterado. As únicas consultas novas ao banco foram de identidades geográficas
com `mode=ro` e `query_only=ON`. O exportador de países lê os JSONs existentes.

Também foram recalculados os SHA-256 dos **113 arquivos TSE originais e backups**,
5.463.547.311 bytes, na pasta de origem registrada pelo inventário anterior.
Todos coincidem, inclusive seus fingerprints. Foi somente leitura dos bytes
comprimidos para integridade: nenhum ZIP de votação foi extraído ou reprocessado.
Hashes dos recibos ficam no resumo JSON; recibos detalhados estão em `.local/m5/`.

O primeiro smoke Windows usou o diretório Debug normal; os builds de entrega e
o smoke final foram feitos na cópia isolada. Builds anteriores de distribuição
não foram excluídos. Três arquivos gerados Windows já apareciam modificados no
início por diferenças de checkout/terminadores, sem diff de conteúdo; não foram
incluídos nos commits M5. Nenhuma limpeza de dados/backups foi executada.

## Executar a prévia real

Na raiz do repositório, o pacote Windows já compilado pode ser aberto com:

```powershell
& '.local/m5/preview/apps/votoaberto_flutter/build/windows/x64/runner/Release/votoaberto.exe'
```

Manter toda a pasta Release junto do executável. Para Web:

```powershell
python -m http.server 18765 --bind 127.0.0.1 --directory .local/m5/preview/apps/votoaberto_flutter/build/web
```

Abrir `http://127.0.0.1:18765/#/mundo?turno=2&visao=summary`, ou
`/#/mundo/US/localidade/29416?turno=2&visao=comparison`. O host é estático e
local, sem backend. O servidor temporário usado no QA foi encerrado ao finalizar.
Para recompilar em nova área isolada, seguir o [guia](GEOGRAPHIC_EXPLORER.md).

## Limitações que permanecem

A cobertura por país é parcial: faltam as 28 associações enumeradas, com uma
contradição oficial que exige esclarecimento. Não se afirma cobertura mundial
completa nem se promove a soma parcial a total exterior. As 145 consultas
originais continuam disponíveis.

O status eleitoral `public_readiness=not_ready` do M4 é preservado: autenticação
de origem não foi realizada e as limitações históricas de confiança dos hashes
não foram removidas. Integridade matemática/hash não certifica uma eleição.

Native Windows foi executado; Android foi compilado, sem teste físico/emulador.
Web depende de acesso inicial aos assets do host; o marco não garante navegação
offline após reiniciar o navegador. PWA continua desabilitada. Não houve API,
publicação pública, push, PR ou merge.

## Arquivos alterados

37 arquivos de implementação/documentação (os três arquivos gerados preexistentes não integram esta relação):

- `.gitattributes`
- `.github/workflows/data-engine.yml`
- `.github/workflows/flutter.yml`
- `README.md`
- `apps/votoaberto_flutter/assets/geo/NOTICE.md`
- `apps/votoaberto_flutter/assets/geo/manifest.json`
- `apps/votoaberto_flutter/assets/geo/municipal_locations.json`
- `apps/votoaberto_flutter/assets/geo/overseas_correspondence.json`
- `apps/votoaberto_flutter/assets/geo/world.geojson`
- `apps/votoaberto_flutter/integration_test/offline_results_test.dart`
- `apps/votoaberto_flutter/lib/app/strings.dart`
- `apps/votoaberto_flutter/lib/app/votoaberto_app.dart`
- `apps/votoaberto_flutter/lib/core/widgets.dart`
- `apps/votoaberto_flutter/lib/features/elections/domain/country.dart`
- `apps/votoaberto_flutter/lib/features/explorer/presentation/explorer_controller.dart`
- `apps/votoaberto_flutter/lib/features/explorer/presentation/explorer_page.dart`
- `apps/votoaberto_flutter/lib/features/explorer/presentation/municipality_search.dart`
- `apps/votoaberto_flutter/lib/features/explorer/presentation/result_charts.dart`
- `apps/votoaberto_flutter/lib/features/map/domain/geographic_catalog.dart`
- `apps/votoaberto_flutter/lib/features/map/domain/world_geometry.dart`
- `apps/votoaberto_flutter/lib/features/map/presentation/brazil_map.dart`
- `apps/votoaberto_flutter/lib/features/map/presentation/world_map.dart`
- `apps/votoaberto_flutter/lib/main.dart`
- `apps/votoaberto_flutter/pubspec.yaml`
- `apps/votoaberto_flutter/test/geographic_assets_test.dart`
- `apps/votoaberto_flutter/test/geographic_explorer_test.dart`
- `apps/votoaberto_flutter/test/municipal_widget_test.dart`
- `docs/GEOGRAPHIC_EXPLORER.md`
- `docs/M5_COMPLETION_REPORT.md`
- `docs/M5_VALIDATION_SUMMARY.json`
- `docs/adr/0005-offline-geographic-explorer.md`
- `pipelines/tse_importer/country_exporter.py`
- `tests/test_country_exporter.py`
- `tests/test_geography_assets.py`
- `tools/geography/build_geography.py`
- `tools/geography/prepare_preview.py`
- `tools/geography/requirements.txt`
