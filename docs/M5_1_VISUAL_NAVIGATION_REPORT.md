# M5.1 — Refinamento visual, navegação e comparação eleitoral

Data: 31/10/2026. Branch: `feat/m5-visual-navigation-polish`.

## Base e escopo

A working tree estava limpa na `main`. `git fetch origin main` confirmou que
`fe83f6b` já era a versão atual; esse commit integra o M5 pelo PR #5. Foi criada
somente a branch solicitada, sem branches auxiliares, push, PR ou merge.

O trabalho altera apresentação Flutter, navegação, pintura vetorial e testes.
Não altera modelos eleitorais, agregadores, exportadores, fontes, correspondências
ou assets. A classificação `public_readiness: not_ready` e seus bloqueios continuam
visíveis na metodologia e na prévia local.

## UI e resultados

- Um `SegmentedButton<ResultMode>` apresenta **1º turno | 2º turno | Comparação**,
  imediatamente abaixo do título do painel. Foram removidos os controles separados
  de turno e de visualização.
- `ResultMode.first/second/comparison` substitui o par de estado da interface
  `ElectionRound + ExplorerView`. Os objetos de domínio conservam seus turnos.
- Cada resumo usa exclusivamente seu turno; a comparação exige ambos e independe
  do modo anterior. A mesma implementação atende Brasil, UF, município, Mundo,
  país e localidade eleitoral.
- A comparação mantém barras pareadas apenas para candidaturas com votos nos dois
  turnos e correspondência aceita pelo contrato M4 (número e identidade de origem).
  Candidaturas exclusivas ou sem registro no outro turno não geram linhas soltas,
  zeros artificiais ou equivalências por nome. Conflitos de identidade continuam
  sem comparação; métricas eleitorais comparáveis permanecem disponíveis.
- Campos ausentes, somas parciais, denominadores zero e cobertura parcial por país
  conservam os tratamentos existentes. O agregado Mundo usa o exterior M4 integral;
  os países usam somente localidades verificadas. Brasil continua incluindo o
  exterior uma única vez.

## Mapas

`MapResetButton` compartilha texto **Ver mapa inteiro**, ícone `zoom_out_map`,
estilo e fade de 220 ms. Só existe quando o destino da câmera está ampliado; links de países indisponíveis
conservam a visão global sem o botão. Durante a saída, a área
ignora ponteiros e exclui foco e semântica. Após o fade, o botão sai da árvore.
Movimento reduzido aplica duração zero, inclusive na câmera existente.

O reset usa a rota como fonte de seleção: limpa UF/município ou país/localidade,
atualiza o painel agregado e anima o mapa retido até sua visão geral. Não cria um
estado paralelo de câmera. Preserva o modo e o contexto: `/` ou `/mundo`.
Escape/Home mantêm a mesma ação. Uma nova seleção volta a ampliar normalmente.

`MapCaption` compartilha tipografia `labelMedium`, família VotoSans e posição
(14 px no topo, 16 px nas laterais). O texto inicial mundial é **Selecione um país**;
hover/foco apresenta o nome. Créditos permanecem legíveis, acima do botão em telas
estreitas quando necessário. A moldura e o fundo decorativos do Mundo foram
removidos; só permanece o indicador de foco acessível, como no Brasil.

### Cores

`mapRegionFill` extrai exatamente a fórmula preexistente do Brasil:
`Color.lerp(surfaceContainerHighest, primaryContainer, .3 + (index % 4) * .1)`.
Nenhuma cor brasileira ou token do tema foi alterado. O Mundo reutiliza essa
variação tonal; seleção usa `primary`, hover/foco usa `primaryContainer`, contornos
de interação usam `onSurface` e países inativos usam `outlineVariant`. Não foram
criados RGBs ou uma paleta nova. Disponibilidade e interação determinam as cores,
sem codificação de candidatos, partidos ou quantidade de votos.

### Pintura e continuidade geográfica

A primeira passagem pinta países maiores e depois os pequenos, coerente com o
hit-testing que prioriza áreas pequenas. Passagens finais redesenham os contornos
do selecionado e, por último, hover/foco. Ilhas pequenas conservam seus alvos
visuais e acessíveis; Polygon e MultiPolygon usam os mesmos caminhos originais.

O enquadramento global abrange longitude ±180° e latitude ±90°, com ajuste uniforme
do `MapViewport` e proporção 2:1. O canvas é recortado a **uma única faixa de 360°**,
inclusive nas áreas vazias deixadas pelo ajuste de proporção. As translações
internas só recompõem as partes de países que cruzam a emenda; não aparecem
continentes repetidos nas laterais. Durante zoom a faixa acompanha o centro da
câmera, preservando Fiji e países multipartes. A geometria e a licença Natural
Earth do M5 permanecem intactas; fronteiras continuam sem declaração de soberania.

## Navegação e URLs

As raízes são independentes: `Brasil > UF > município` e
`Mundo > país > localidade eleitoral`. Breadcrumbs ancestrais são clicáveis;
o nível municipal/localidade também é exibido. Mundo não contém Brasil como
ancestral. A alternância usa **Consultar votação no exterior** e **Consultar
votação no Brasil**; o retorno hierárquico usa país/Mundo/UF conforme a seleção.
No botão Voltar nativo, a raiz Mundo já não simula um retorno ancestral ao Brasil.

O parâmetro canônico é `modo=1`, `modo=2` ou `modo=comparacao`.

| Entrada anterior | Modo canônico |
| --- | --- |
| `turno=1&visao=summary` | `modo=1` |
| `turno=2&visao=summary` | `modo=2` |
| `turno=1&visao=comparison` | `modo=comparacao` |
| `turno=2&visao=comparison` | `modo=comparacao` |
| `turno=1&visao=insights` | `modo=1` |
| `turno=2&visao=insights` | `modo=2` |

Sem parâmetros, usa-se `modo=1`. Um `modo` válido explícito tem precedência;
parâmetros legados são retirados na normalização. Valores inválidos apresentam
indisponibilidade, sem fabricar resultados. A segunda leitura da URL canônica é
estável, sem ciclos. As rotas existentes, incluindo exterior legado e localidades
sem país, são preservadas. Câmera não entra na URL.

## Validação

Ambiente: Flutter 3.47.8 / Dart 3.13.7, Python 3.12, Windows. Código funcional
compilado: `5a18cdc` (inclui `bc8b82d`). Evidência resumida, hashes e dimensões das
capturas: [M5_1_VALIDATION_SUMMARY.json](M5_1_VALIDATION_SUMMARY.json).

| Verificação | Resultado |
| --- | --- |
| `dart format --output=none --set-exit-if-changed lib test integration_test` | Passou |
| `flutter analyze --no-pub` | Sem problemas |
| `flutter test --no-pub --coverage` | 111 passaram; 7 opcionais de dados reais ignorados |
| Cobertura de linhas | 1.921/2.004 = 95,86% |
| Ruff format/check (mesmo escopo do CI) | 32 arquivos formatados; sem problemas |
| `pytest -q --basetemp=.local/m5_1/pytest-temp` | 146 passaram; 2 opcionais ignorados |
| Web release, assets reais | Passou |
| Windows release, assets reais | Passou |
| APK debug, assets reais (mesma modalidade do workflow) | Passou |
| Smoke Windows nativo com dados reais | 1 passou; **0 tentativas de HTTP da aplicação** |
| `git diff --check` | Passou |

A execução Python inicial não conseguiu usar o temporário padrão sob o sandbox.
A suíte completa passou com um temporário novo e isolado dentro de `.local`.
Nenhum arquivo Python foi alterado. Os builds usam `embedded_build.py`, as mesmas
modalidades dos workflows, SDK/dependências já instalados e `--no-pub`. No Web,
`--no-web-resources-cdn` mantém o runtime local; a última compilação usa
`--no-wasm-dry-run` (as anteriores também passaram pelo dry run Wasm). O aviso de
obsolescência de `--pwa-strategy=none` é do SDK, sem falha de build.

O smoke real verifica Brasil nos dois turnos, municípios SP/Adamantina, marcador,
reset nacional, Mundo, EUA, Boston em comparação, reset mundial, Bruxelas sem
país e integridade dos totais. `HttpOverrides` rejeita e conta qualquer criação
de `HttpClient` no processo da aplicação. O servidor Web usado na inspeção serve
apenas os arquivos estáticos locais; não há serviço de resultados, tiles ou API.

Os testes novos cobrem a matriz de seis abrangências × três modos, migração de
links, raízes/breadcrumbs, reset com limpeza de seleção e retorno aos agregados,
fade/interação/foco/semântica, movimentos reduzidos, seleção rápida, ilhas,
antimeridiano, cores nos dois temas e enquadramento nas quatro resoluções.
Há testes rasterizados para pixels nas áreas laterais (nenhuma cópia) e no
contorno comum entre vizinhos (destaque acima). A suíte anterior mantém testes
de identidade, totais parciais, assets locais e respostas assíncronas obsoletas.

## Inspeção visual

Foram inspecionados os viewports 1366×768, 1920×1080, 390×844 e 768×1024
nos temas claro e escuro. Foram preservadas **15 capturas JPEG locais**, sem
reescalonamento, em `.local/m5_1/` (não versionadas):

- `world-{light,dark}-{1366x768,1920x1080,390x844,768x1024}.jpg`: oito visões globais.
- `municipality-{light,dark}-{1366x768,390x844}.jpg`: quatro visões de Porto Alegre,
  com marcador, breadcrumbs e botão contextual.
- `country-light-1366x768.jpg`: Egito selecionado, três modos e reset.
- `locality-light-1366x768.jpg`: Mundo > Egito > Cairo.
- `comparison-light-1366x768.jpg`: somente as duas candidaturas comparáveis.

Foram conferidos mapa único e proporcional, cores, títulos, marcador, ausência de
moldura, reset e seleção posterior. Voltar/avançar do navegador restaurou Egito e
Mundo em Comparação, com URLs e painel correspondentes. O reset de Porto Alegre
retornou ao Brasil em segundo turno, sem marcador ou UF selecionada.

A captura nativa do navegador integrado pode omitir a faixa inferior de 19 px do
viewport DOM 1920×1080 e 1 px do 390×844; as dimensões efetivas dos arquivos estão
no resumo JSON. O DOM desktop confirmou 1920×1080. Os testes Flutter também usam
as dimensões exatas solicitadas. Não houve recorte ou distorção da cartografia.
A inspeção não substitui testes em aparelho Android físico.

## Preservação e tamanho

A comparação antes/depois revalidou SHA-256, tamanho, `mtime_ns` e identidade do
arquivo. Foram preservados:

| Conjunto conferido | Arquivos | Bytes |
| --- | ---: | ---: |
| Releases processadas/backups, assets instalados e derivado por país M5 | 175 | 2.340.107.525 |
| Originais TSE do inventário anterior | 113 | 5.463.547.311 |
| Mini-base real M4 (subconjunto dos 175) | 32 JSONs | 4.475.495 |
| Cartografia/correspondências M5, incluindo malha brasileira | 5 | 1.338.504 |
| Derivado por país M5 e manifesto (subconjunto dos 175) | 2 | 67.654 |

Também foi conferida a ausência de novos arquivos nas áreas protegidas. O SQLite
nacional conserva 935.424.000 bytes e SHA-256
`c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4`.
A release M4 permanece `e4e9c9cb5189ab5d4e124bfc`, com manifesto
`c4dcddacb8092ff1dfffb35b07b739dbf360232e701e080087f52a4a09e20637`.
As correspondências dos 5.571 municípios e 145 localidades estrangeiras não
foram editadas. O derivado M5 `f3116546104b1248b29011ba` permanece intacto.

Os inventários locais antes/depois estão em `.local/m5_1/preservation-*.json` e
`originals-*.json`. Seus hashes coincidentes constam no resumo versionado.
Não houve importação, extração/reprocessamento de ZIPs, instalação de assets ou
substituição de releases. Nenhum novo asset: **acréscimo cartográfico/eleitoral
zero bytes**.

| Pacote final isolado | Bytes | Diferença ante pacote M5 registrado |
| --- | ---: | ---: |
| Web release, diretório | 48.956.622 | −19.883 |
| Windows release, diretório | 35.142.210 | −65.504 |
| APK debug, arquivo | 155.960.173 | +4.364 |

Os totais incluem código, runtime e metadados de compilação; não isolam o custo
da UI. Os três pacotes foram abertos e conferidos por arquivo: **32 JSONs reais e
cinco arquivos geográficos idênticos à origem**, sem JSON eleitoral sintético.
SHA-256 do APK final:
`61ea6b0a0e28101e1bcfbb7bfcc4f75987b60d42a599c31f6c7553376f95ad8c`.

## Commits e arquivos

1. `bc8b82d` — `refactor(explorer): unify result modes and independent geographic navigation`.
2. `5a18cdc` — `fix(maps): unify framing controls and render one consistent world`.
3. `docs(m5.1): record visual validation builds and preservation` — commit que contém
   este relatório e o resumo de validação; seu identificador pode ser consultado
   com `git log --oneline fe83f6b..HEAD`.

Arquivos de produção sob `apps/votoaberto_flutter/lib/`:

- `app/votoaberto_app.dart`.
- `features/explorer/presentation/`: `explorer_controller.dart`, `explorer_page.dart`,
  `result_mode.dart` (novo) e `result_charts.dart`.
- `features/map/domain/world_geometry.dart`.
- `features/map/presentation/`: `brazil_map.dart`, `world_map.dart` e
  `map_controls.dart` (novo).

Testes sob `apps/votoaberto_flutter/`: `test/comparison_chart_test.dart`,
`test/controller_test.dart`, `test/embedded_repository_test.dart`,
`test/explorer_widget_test.dart`, `test/geographic_explorer_test.dart`,
`test/municipal_widget_test.dart`, `test/visual_navigation_polish_test.dart` (novo)
e `integration_test/offline_results_test.dart`. Documentação: este relatório e
`docs/M5_1_VALIDATION_SUMMARY.json`. Os testes anteriores foram migrados para os
novos modos sem perder as verificações eleitorais de origem.

## Executar a prévia real

Os builds foram produzidos exclusivamente em `.local/m5_1/preview`, sem instalar
JSONs sobre releases anteriores. O repositório principal continua preparado para
fixtures no CI, sem download eleitoral ou importação nacional.

```powershell
# Executável já compilado; não exige API ou servidor.
& .local/m5_1/preview/apps/votoaberto_flutter/build/windows/x64/runner/Release/votoaberto.exe

# Web: somente servidor de arquivos estáticos local.
.venv/Scripts/python.exe -m http.server 18766 --bind 127.0.0.1 --directory .local/m5_1/preview/apps/votoaberto_flutter/build/web
# Abrir http://127.0.0.1:18766/#/mundo?modo=comparacao
```

Para refazer os builds sem tocar nos assets instalados, criar **outro diretório
novo** com `tools/geography/prepare_preview.py --target .local/<novo-diretorio>`;
usar `flutter pub get --offline` e `tool/embedded_build.py web|windows|apk --mode real`
nessa cópia. O helper preserva o manifesto e o hash da release M4; não contorna a
proteção do instalador. Não apagar ou reutilizar à força um destino já existente.

## Limitações mantidas

- As 28 localidades sem país confirmado do M5 continuam acessíveis e sem associação
  inventada; a cobertura por país continua explicitamente parcial.
- Não houve coleta, autenticação ou reconciliação eleitoral nova. Os resultados e
  limitações de proveniência continuam os do M4/M5.
- A cartografia é simplificada; a lista e a busca oferecem alternativas para países
  ou territórios pequenos. O marcador municipal não representa urna ou local de voto.
- A inspeção Web responsiva não equivale a execução em dispositivo Android físico.
  Não foram medidos FPS nem feitas alegações de desempenho em produção.
