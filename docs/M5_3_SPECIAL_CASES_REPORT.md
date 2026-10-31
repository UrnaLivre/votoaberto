# M5.3 — Janela de casos especiais do exterior

Data: 31/10/2026. Branch única: `feat/m5-3-overseas-special-cases`.

## Base e escopo

`git fetch origin main` confirmou `main` sincronizada em **3196ffb**, que integra
o PR **#7 da M5.2**. A working tree estava limpa antes da criação da branch.
Não foram criadas branches auxiliares. Não houve push, PR ou merge nesta missão.

A entrega altera somente apresentação, getters de seleção para a interface e
testes. Não altera dados, classificação documental, parsers, agregadores,
exportadores, fontes, dependências ou cartografia. Não foi criada release
eleitoral/geográfica, JSON de votos ou distribuição nova de países.

Commit de implementação: **1567558** — `feat(explorer): explain overseas residuals
in accessible special-cases dialog`. O commit de documentação contém este
relatório e os índices; consultar seu hash com `git log -2 --oneline`.

## Visão geral Mundo

Foi removida do painel principal a mensagem “Cobertura por país parcial: 143 de
145 localidades...” e a lista expansível que repetia Bruxelas e Trípoli.
Imediatamente abaixo de **Consultar votação no Brasil** aparece o botão secundário
**Casos especiais (2)**, com `info_outline`, cores e estilo do tema existente.

O botão é exclusivo da visão geral Mundo; não aparece em Brasil, país ou
localidade. Sua contagem considera os registros presentes na união dos turnos,
independentemente de 1º turno, 2º turno ou Comparação. A identificação usa os
códigos TSE **29432/30686**, estado de correspondência residual e vínculo de
versão entre geografia e dataset, sem depender do nome textual da localidade.

Não são criados casos ou números para uma base demonstrativa sem esses registros.
Fixtures que usam os códigos para testar a UI permanecem explicitamente fictícios.
Se um registro conhecido não existir na base, a interface só oferece os casos
presentes. Se surgir uma pendência diferente ou a correspondência estiver
indisponível/incompatível, ela continua acessível em **Outras localidades sem
país confirmado (n)**, incluindo sua rota individual; não é ocultada nem atribuída
a um país por suposição. A busca geral de localidades também foi preservada.

`unmappedLocalities`, a cobertura 143/145, os 100 países e o residual continuam
intactos. As ressalvas metodológicas, mensagens de agregação parcial dos países,
percentuais indisponíveis e limitações independentes da base continuam vigentes.
`public_readiness: not_ready` e os bloqueios herdados permanecem na metodologia.

## Janela, navegação e acessibilidade

Um `Dialog` Flutter apresenta **Casos especiais — Votação no exterior**, com
`TabBar`/`TabBarView` e abas **Bruxelas** e **Trípoli**. Não há segunda janela
nativa, rota principal nova, seletor de turno ou gráfico de comparação.
Os turnos disponíveis são seções estáticas, acessíveis por rolagem vertical.

- Largura máxima de 760 pixels lógicos; margens de 24 no desktop e 12 no celular.
  A altura respeita a tela e fica limitada a 800, sem exigir tela cheia.
- Tipografia VotoSans, cores, superfícies, espaçamento e gráficos do tema atual.
  Não foram introduzidas cores de alerta, badges de erro ou animações chamativas.
- Botão de fechar com tooltip/semântica **Fechar casos especiais**; Escape fecha.
  Tab e Shift+Tab ficam no diálogo; setas esquerda/direita sobre as abas permitem
  alterná-las. O foco retorna ao botão de abertura se ele continuar disponível.
- Títulos com semântica de cabeçalho, diálogo nomeado, abas padrão Material e
  semântica de candidatos/votos/percentuais herdada de `DistributionChart`.
- A preferência de redução de animações é respeitada na abertura e nas abas.
- Cada aba mantém sua posição de rolagem por código. Trocar abas não dispara
  consultas de repositório nem pode apresentar a resposta tardia de outro código.

Abrir, trocar abas e fechar não modifica rota, modo, localidade, câmera ou
rolagem do painel principal. Continuam funcionando:
`/mundo/localidade/29432` e `/mundo/localidade/30686`, inclusive os parâmetros
anteriores de turno/visualização. A janela não exige nenhuma mudança de URL.

## Textos definitivos e resultados

### Bruxelas

Título: **Bruxelas**. Subtítulo: **Localidade eleitoral TSE 29432**.

> Esta localidade eleitoral reúne seções com locais de votação documentados na Bélgica e em Luxemburgo. Os resultados disponíveis estão agregados por localidade e ainda não podem ser distribuídos entre os dois países sem uma apuração específica por seção.

Nota:

> Os votos abaixo são o agregado da localidade TSE 29432, não os resultados individuais da Bélgica ou de Luxemburgo.

São exibidos **Resultados — 1º turno** e **Resultados — 2º turno**, com os
objetos efetivamente carregados do M4. Nenhum voto é escolhido para BE/LU,
dividido por proporção ou novamente somado ao total exterior.

### Trípoli

Título: **Trípoli**. Subtítulo: **Localidade eleitoral TSE 30686**.

> Esta localidade aparece associada administrativamente à Líbia, mas o local de votação cadastrado fica em Túnis, na Tunísia. A documentação analisada ainda não permite estabelecer um critério definitivo de atribuição territorial para seus resultados.

Nota:

> O país de atribuição permanece pendente de esclarecimento documental.

O primeiro turno usa o registro existente, confirmado diretamente no JSON
municipal M4 e no smoke: **2 votos contabilizados e válidos**, 30 aptos, dois
comparecimentos e 28 abstenções. Brancos/nulos são indisponíveis, não zeros.
Para o segundo turno a mensagem é:

> Não há registro de resultados desta localidade para o 2º turno na base consultada.

Não se cria resultado, candidato, comparecimento zero ou comparação para esse turno.

### Origem das estatísticas e critérios

`ExplorerController.municipalities` já contém as localidades ZZ carregadas pelo
repositório M4. O diálogo encontra cada objeto pelo código TSE e passa seus
`RoundResult` diretamente a **RoundSummary**. Esse componente foi extraído do
resumo existente do painel, mantendo métricas, textos, formatação, critérios de
disponibilidade e `DistributionChart`; não é um sistema novo de estatísticas.

Uma conferência textual após substituição dos parâmetros confirmou que a
apresentação compartilhada preserva o corpo do resumo M5.2, com o detalhe
doméstico nacional recebido como widget opcional. A janela não agrega, calcula
votos novos ou faz chamadas HTTP. Nenhum número eleitoral está fixado no código
de produção; constantes numéricas reais existem apenas nas asserções do smoke.

No M4 consultado:

| Localidade/turno | Contabilizados | Comparecimento | Aptos | Abstenção | Válidos | Brancos | Nulos |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Bruxelas 1º | 5.091 | 5.091 | 10.073 | 4.982 | 4.975 | 63, parcial 13/14 seções | 53, parcial 13/14 |
| Bruxelas 2º | 5.326 | 5.326 | 10.075 | 4.749 | 5.218 | 51, 14/14 | 57, parcial 12/14 |
| Trípoli 1º | 2 | 2 | 30 | 28 | 2 | Indisponível | Indisponível |
| Trípoli 2º | Ausente | Ausente | Ausente | Ausente | Ausente | Ausente | Ausente |

Os votos por candidato vêm de cada registro, com as mesmas contagens e identidades.
Percentuais dos válidos só aparecem quando o campo válido está completo e o
denominador permite; taxas de participação respeitam a cobertura de seus campos.
Categorias parciais conservam o rótulo existente e candidatos sem registro não
viram zeros. A nota final da janela esclarece:

> Estes resultados já integram os totais do exterior e do Brasil. A consulta nesta janela não acrescenta votos aos agregados.

## Carregamento e erros

O botão só fica disponível para os casos reconhecidos nos dados carregados.
Durante o carregamento inicial ZZ, o painel mantém o estado existente de leitura;
em falha, conserva a ação de tentar novamente. A janela também observa esses
estados, além de ausência de localidade ou incompatibilidade documental, e não
apresenta números nessas situações. As identidades das abas ficam estáveis na
abertura; cada conteúdo revalida seu código no estado corrente.

A janela não possui operação assíncrona de carregamento própria. Usa o fluxo
existente de `ExplorerController`, com sua proteção de respostas tardias.
Fechamento durante leitura pendente foi testado: não há `setState` tardio do
diálogo, dados de outra localidade ou navegação alterada pelo fechamento.

## Arquivos alterados

Sob `apps/votoaberto_flutter/`:

- `lib/features/explorer/presentation/explorer_page.dart`: botão, abertura/restauração
  de foco, retirada da mensagem e nova lista das outras pendências.
- `lib/features/explorer/presentation/explorer_controller.dart`: getters de
  classificação visual dos casos conhecidos e demais residuais; agregação intacta.
- `lib/features/explorer/presentation/overseas_special_case.dart`: códigos e
  explicações documentais dos dois casos.
- `lib/features/explorer/presentation/overseas_special_cases_dialog.dart`: diálogo,
  abas, estados, rolagem, teclado e apresentação dos turnos disponíveis.
- `lib/features/explorer/presentation/round_summary.dart`: extração do resumo já
  existente para uso compartilhado no painel e no diálogo.
- `test/overseas_special_cases_test.dart`: fixtures em memória, sem novo JSON
  eleitoral e sem SQLite/fontes oficiais na CI; 24 novos testes de widget.
- `test/geographic_explorer_test.dart`: rótulo da lista genérica de pendências.
- `integration_test/offline_results_test.dart`: smoke real das duas abas, totais,
  ausência de turno, tema e captura opcional por `QA_SCREENSHOTS`.

Documentação: este relatório, `README.md` e `docs/GEOGRAPHIC_EXPLORER.md`.
`result_charts.dart`, domínio eleitoral, repositório M4, roteador, tema,
`geographic_catalog.dart`, dependências e assets não foram modificados.

## Validação automatizada e visual

| Verificação | Resultado |
| --- | --- |
| Dart format | 42 arquivos; zero diferenças na verificação final |
| Flutter analyze --no-pub | Zero issues |
| Flutter test --no-pub --coverage | **151 passaram**, 7 smokes reais opt-in pulados; 44 s |
| Testes focados de janela + navegação | 39 passaram |
| pytest de geografia, países e evidências | **34 passaram**; 5,37 s |
| Ruff nos testes Python pertinentes | Passou |
| Windows release real | Passou; compilação 114,0 s |
| Web release real | Passou; compilação 130,0 s |
| APK debug real | Passou; Gradle 136,9 s |
| Smoke Windows real | **1 passou**; 0 tentativas HTTP da aplicação |
| Integridade de assets/releases/originais | 295 arquivos idênticos antes/depois |
| git diff --check | Passou |

Python 3.12, Flutter 3.47.8/Dart 3.13.7 locais. Cobertura gerada em
`apps/votoaberto_flutter/coverage/lcov.info`, ignorada pelo Git. As suítes anteriores
de navegação, comparação, mapas e repositório foram executadas. CI remota não
foi disparada, pois não houve push.

Os testes cobrem os 25 requisitos: visibilidade e posicionamento, retirada da
mensagem/lista duplicada, duas abas/códigos/textos, identidade dos objetos de
resultados e candidatos, turnos de Bruxelas, ausência em Trípoli, campos ausentes,
rota/modo/rolagem/foco preservados, Tab/Shift+Tab/setas/Escape, deep links,
totais/residual inalterados, execução offline, demonstração e terceira pendência.

Nos temas claro e escuro foram testados **1366×768, 1920×1080, 390×844 e 768×1024**,
mais 280×640. As duas abas permitem rolagem sem overflow. Houve ainda teste de
texto ampliado 2×, nomes longos, contagens grandes, denominador parcial,
redução de animações e verificação automática de contraste textual nos dois temas.

As primeiras rodadas corrigiram a semântica de escopo de rota e detalhes do
harness de foco/medição. Uma tentativa de build simultâneo foi recusada pelo
bloqueio existente de empacotamento; os builds finais foram concluídos em sequência
na cópia isolada, sem remover esse bloqueio ou alterar o instalador.

## Capturas locais

Quatro capturas com o `rootBundle` real foram produzidas pelo smoke Windows,
na camada Flutter de 1266×683, e inspecionadas visualmente. As áreas externas ao
diálogo são transparentes na captura; não são a moldura de uma segunda janela.
São artefatos locais, não versionados nem publicados:

- [Bruxelas — claro](../.local/m5_3/screenshots/bruxelas-light-desktop.png).
- [Trípoli — claro](../.local/m5_3/screenshots/tripoli-light-desktop.png).
- [Bruxelas — escuro](../.local/m5_3/screenshots/bruxelas-dark-desktop.png).
- [Trípoli — escuro](../.local/m5_3/screenshots/tripoli-dark-desktop.png).

## Preservação e pacotes

O inventário antes/depois conferiu **295 arquivos, 7.804.288.004 bytes**:
SHA-256, tamanho, mtime e identidade de arquivo coincidem integralmente. Inclui
ZIPs TSE e backups, releases, SQLite, assets eleitorais e geográficos, fontes
empacotadas e derivados por país M5/M5.2. Recibos locais:
`.local/m5_3/preservation-before.json` e `preservation-after.json`.

- M4: `e4e9c9cb5189ab5d4e124bfc`; manifesto
  `c4dcddacb8092ff1dfffb35b07b739dbf360232e701e080087f52a4a09e20637`.
- Manifesto geográfico: `geography-2026-2`, SHA-256
  `ab4be0d225aa2209c976ec2238c1faa1a4c922d8d2f80ac8f87ba078f5746c47`,
  com o mesmo hash fixado no cliente.
- Correspondência exterior: SHA-256
  `028df778ddbca88b1959541a287221d8cb869dcdfa5eecac6bf33abdf3e5f699`.
- SQLite nacional: SHA-256
  `c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4`;
  não foi aberto para consultas SQL nem reconstruído; somente seus bytes foram
  lidos para o hash de integridade.

Os três pacotes foram inspecionados por bytes: **32 JSONs eleitorais reais e
cinco arquivos geográficos idênticos à origem**, sem JSON eleitoral sintético.
Nenhum derivado real por país foi regenerado, reinstalado ou publicado. Não houve
nova reconciliação ou apuração eleitoral: esta missão preserva os resultados e
as verificações documentadas na M5.2 e testa somente sua apresentação e integridade.

| Pacote local | Bytes | Verificação |
| --- | ---: | --- |
| Windows release, diretório | 35.344.529 | 32 JSONs reais + 5 geográficos, todos idênticos |
| Web release, diretório | 49.032.864 | 32 JSONs reais + 5 geográficos, todos idênticos |
| APK debug | 155.986.001 | 32 JSONs reais + 5 geográficos, todos idênticos |

SHA-256 do APK: `0961e71183d15df022d992e780c464b02860d8b4d4d07bf55aca864e6050f8cf`.

Metadados de conferência dos pacotes e hashes das capturas em
`.local/m5_3/build-verification.json`. Os tamanhos incluem runtime e código;
não representam aumento de dados eleitorais, que permaneceram idênticos.

## Executar a prévia real

Na raiz do repositório:

```powershell
# Manter toda a pasta Release junto do executável.
& .local/m5_3/preview/apps/votoaberto_flutter/build/windows/x64/runner/Release/votoaberto.exe
```

Selecionar Mundo e clicar **Casos especiais (2)** abaixo de **Consultar votação
no Brasil**. Cada aba mostra os turnos existentes por rolagem; fechar retorna ao
mesmo modo e contexto.

Prévia Web local opcional:

```powershell
.venv/Scripts/python.exe -m http.server 18768 --bind 127.0.0.1 `
  --directory .local/m5_3/preview/apps/votoaberto_flutter/build/web
# http://127.0.0.1:18768/#/mundo?modo=comparacao
```

Para recompilar sem sobrepor prévias anteriores, criar outro destino novo:

```powershell
.venv/Scripts/python.exe tools/geography/prepare_preview.py --target .local/m5_3-outra-previa
cd .local/m5_3-outra-previa/apps/votoaberto_flutter
flutter pub get --offline
python tool/embedded_build.py windows --mode real -- --no-pub
python tool/embedded_build.py web --mode real -- --no-pub
python tool/embedded_build.py apk --mode real -- --no-pub
python tool/embedded_build.py native-test --mode real -- --no-pub
```

Opcionalmente passar `--dart-define=QA_SCREENSHOTS=<diretório-absoluto-local>`
ao `native-test` para salvar as quatro capturas. O parâmetro só existe no teste,
não no fluxo de uso do aplicativo. Executar os builds em sequência.

## Limitações mantidas

- Bruxelas continua no residual, sem divisão BE/LU; Trípoli continua sem escolha
  entre Líbia/Tunísia e sem segundo turno inventado.
- A cobertura geográfica permanece parcial, 143/145. A retirada de uma mensagem
  redundante do painel não declara completude nem modifica a metodologia.
- `public_readiness: not_ready` e as pendências de proveniência/autenticação M4
  permanecem independentes desta interface. Não houve publicação.
- Acesso Windows offline foi executado. Android foi compilado, sem teste em
  aparelho/emulador. Web dispensa API de resultados e usa assets estáticos do host;
  a primeira carga/reabertura totalmente offline não é garantida; PWA continua fora do marco.
- Acessibilidade foi verificada automaticamente para foco, teclas, semântica,
  contraste e texto ampliado; não houve sessão manual com leitor de tela.
- As capturas reais são de desktop; os outros viewports foram exercitados por
  testes de layout e interação com fixtures, sem alegar teste físico de dispositivo.
