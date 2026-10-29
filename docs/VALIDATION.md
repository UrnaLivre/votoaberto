# M1 — implementação e validação local

Data: **2026-10-29** (America/Sao_Paulo). Versão do aplicativo: **0.1.0+1**.
Branch: `feat/m1-interactive-explorer`, criada a partir da `main` limpa em
`bcc087c`. Não houve push, merge, rebase, publicação ou importação de dados TSE.

## Entrega efetiva

- Flutter com runners Windows, Web e Android, sem backend obrigatório.
- Brasil e 27 UFs funcionais: hit-test sobre limites IBGE, destaque, zoom
  interrompível, retorno nacional, busca sem acentos e navegação por teclado.
- Painéis nacional e estadual distintos, dois turnos, distribuição por candidato,
  comparações absolutas/relativas e ranking fictício de comparecimento.
- Temas claro/escuro, layout lateral no desktop e fluxo vertical no mobile,
  breadcrumbs, fontes/metodologia, licença de software, estados de carga/erro/vazio.
- Aviso **DEMONSTRAÇÃO — DADOS FICTÍCIOS** fixo fora da área de rolagem.
- Domínio tipado, mock-v1 determinístico, soma nacional coerente e interface
  `ElectionRepository`; `ApiElectionRepository` é abstrata e não simula HTTP.
- Modelo futuro de município, zona, seção, BU, exterior ZZ e chave composta
  com identificadores string e campos adicionais, sem registros fabricados.
- URLs hash para país/UF, turno e visão; histórico Web e retorno do sistema.
- Fontes e geometria embarcadas; motor Web local no build com
  `--no-web-resources-cdn`. Não há tiles, WebView, API ou fonte tipográfica
  remota exigidos pelo fluxo demonstrativo em português.

Arquitetura, decisões e fórmulas em [ARCHITECTURE.md](ARCHITECTURE.md),
[ADR 0001](adr/0001-vector-map.md) e [ADR 0002](adr/0002-state-data-navigation.md).

## Ferramentas verificadas

| Ferramenta | Versão/condição observada |
| --- | --- |
| Flutter | stable **3.47.8**, framework `737ba8f885dc774b53b442759999a312c9461e4e` |
| Dart | **3.13.7** |
| Windows | Windows 11 25H2, build 26200.9711 |
| Visual Studio | Community 2026 **18.10.3**, C++ e Windows SDK 10.0.26100.0 |
| Android Gradle Plugin / Gradle | **9.1.0 / 9.3.1** |
| Kotlin / alvo JVM | **2.4.0 / 17** no runner gerado pelo SDK |
| Android compile SDK / NDK | **36 / 28.2.13676358** |
| Android Build Tools / CMake | **36.0.0 / 3.22.1**, usados pelo build |

Flutter/Dart não estavam no PATH. O SDK oficial foi instalado em `.local/flutter`
e seu ZIP conferido com SHA-256 do manifesto oficial antes da extração. O ZIP
temporário foi removido; a instalação local está ignorada pelo Git.

O diagnóstico inicial detectou Android SDK existente, mas sem `cmdline-tools`.
O Gradle instalou NDK, Build Tools 36, Platform 36 e CMake 3.22.1 usando as
licenças **já aceitas** no SDK. Não foi necessário alegar bloqueio Android:
o APK compilou. `cmdline-tools`/fluxo de `flutter doctor --android-licenses`
ainda devem ser regularizados para uma estação Android completa.

## Comandos realmente executados

Todos abaixo terminaram com código **0** na revisão final:

| Comando em `apps/votoaberto_flutter` | Resultado |
| --- | --- |
| `flutter pub get` | Dependências resolvidas e `pubspec.lock` versionado |
| `dart format --output=none --set-exit-if-changed lib test` | 20 arquivos, 0 alterações |
| `flutter analyze` | **No issues found!** |
| `flutter test --coverage --reporter expanded` | **36 testes passaram**, 0 falhas |
| `flutter build windows --release` | `build/windows/x64/runner/Release/votoaberto.exe` |
| `flutter build web --release --no-web-resources-cdn` | `build/web`; dry run Wasm passou, build entregue é JavaScript |
| `flutter build apk --debug` | `build/app/outputs/flutter-apk/app-debug.apk` |
| `git diff --check` / `git diff --cached --check` | Sem erros após correção de whitespace |

O último Web build levou 51,6 s; Windows, 23,7 s. O primeiro APK levou
1.072,2 s por downloads/configuração inicial; a confirmação incremental final
levou 6,9 s na etapa Gradle. Tempos são registros deste ambiente, não promessa
de desempenho. APK debug universal: 152.962.092 bytes, **não versionado**.

LCOV final: **798 de 857 linhas instrumentadas (93,12%)**. Essa medida cobre
os arquivos carregados pela suíte; não equivale a auditoria completa nem a
validação de todos os sistemas operacionais.

## Cobertura funcional dos testes

- 27 identificadores únicos, DF e exclusão de ZZ da enumeração de UFs.
- Somas nominais, válidos, brancos, nulos, comparecimento, abstenção, limites,
  denominadores, agregação nacional e votos nacionais de cada candidato.
- Determinismo, coleção imutável, eleição não suportada, zeros à esquerda e
  discriminadores adicionais da chave eleitoral.
- Controller: seleção/turno/tema, retry, resposta antiga ignorada e dispose.
- Geometria real: 27 âncoras internas corretas, DF/GO, litoral/Norte, bounds,
  Polygon/MultiPolygon, ilhas e buracos, transformação inversa e ponteiro
  sobre todas as 27 UFs.
- Câmera: interrupção/substituição, retorno nacional e redução de movimento.
- Widgets: busca (incluindo Enter rápido), seleção/painel, troca de turno,
  comparação, retorno, deep link, tema, metodologia, erros/retry de dados e
  geometria, carga realmente pendente e recorte vazio.
- Layouts **1920×1080, 1366×768, 768×1024, 390×844 e 280×700**, além da
  transição entre tamanhos na mesma sessão preservando UF e turno.
- Diretrizes Flutter de **contraste textual nos dois temas** e **alvos de
  toque Android**, além do retorno do sistema a partir de um deep link.

Não há baseline golden versionado: as verificações visuais foram feitas em
runtime e registradas como imagens de referência, sem apresentar isso como
teste automatizado de pixels entre plataformas.

## Plataformas e inspeção visual

| Plataforma | Compilação | Execução/UX realmente observada |
| --- | --- | --- |
| Windows x64 | Release aprovado | Executável final aberto localmente; mapa e painel nacional renderizados; semântica nativa inspecionada |
| Web | Release JS aprovado | Build servido somente em localhost e aberto no navegador integrado Chromium; busca DF, zoom, painel estadual, turno, comparação, temas, Voltar/Avançar e layout mobile conferidos; nenhum erro de console capturado na sessão final |
| Android | APK debug aprovado | **Não executado** em emulador ou dispositivo físico nesta entrega |

As imagens [desktop](images/m1-desktop.jpg) e [mobile](images/m1-mobile.jpg)
são capturas do aplicativo funcional, usando o conjunto fictício. Os testes
de widget em diferentes resoluções não substituem testes em hardware físico.
Não foi feita auditoria com NVDA/TalkBack; mapa oferece busca/lista acessíveis
como alternativa aos polígonos. Não declaramos conformidade WCAG integral.

## Dependências e materiais

| Dependência resolvida | Motivo |
| --- | --- |
| Flutter / flutter_localizations | UI multiplataforma, estado ChangeNotifier, semântica, temas e pt-BR |
| `go_router 17.5.0` | URLs, histórico e deep links declarativos |
| `intl 0.20.2` | Contagens/percentuais em português brasileiro |
| `cupertino_icons 1.0.9` | Fontes de ícones adaptativos referenciadas pelo framework |
| `flutter_test` / `flutter_lints 6.0.0` | Testes, diretrizes de acessibilidade e análise estática |

Não há dependência cartográfica ou de gráficos de terceiros no runtime.
GeoJSON IBGE com origem, condições de reutilização e SHA-256 documentados em
[CARTOGRAPHY.md](CARTOGRAPHY.md); `.gitattributes` impede conversão dos bytes no
checkout Windows. Roboto acompanha licença Apache 2.0 e aviso de origem no
asset. Ícones temporários são arte geométrica original, reproduzível pelo
script `tools/generate_app_icons.ps1`.

## Limitações e próximos passos

- Dados inteiramente fictícios, sem exterior, municípios, zonas, seções ou BU
  populados. O mock não representa distribuição real de população ou votos.
- API, pipeline TSE, reconciliação, banco, exportação, autenticação e publicação
  não implementados; pertencem aos marcos seguintes.
- Tema somente na sessão; internacionalização preparada, mas catálogo ARB
  completo e segundo idioma ainda pendentes. Identidade visual oficial futura.
- Mapa simplificado, sem medição, pan livre, pinch zoom, tiles ou fronteiras
  eleitorais; seleção/enquadramento são as interações do M1.
- Build Android validado, uso em dispositivo físico/emulador ainda pendente.
- GitHub Actions preparado em três jobs (qualidade/Web, Windows, Android), com
  permissões de leitura e sem deploy. **Não executado no GitHub**, pois não houve
  push. Revisão de acessibilidade com usuários e goldens estáveis são melhorias.

Próxima prioridade: testar Android físico e leitores de tela; depois inventariar
fontes TSE no M2, validar schemas/chaves/cobertura e implementar o adaptador API
com testes de contrato, preservando proveniência e a distinção de dados reais.

## Execução manual e revisão Git

O [README](../README.md#executar-o-aplicativo) contém os comandos Windows, Web,
Android e de testes. Fluxo manual recomendado: abrir Brasil; buscar `DF`; trocar
turno; comparar; abrir fontes; alternar tema; selecionar outra UF; retornar ao
Brasil; verificar Voltar/Avançar na Web e redimensionar a janela.

Commits de implementação e testes:

- `4ec569939b39aaa4d79bebcd3a38f0a56c3241e4` — aplicativo e contratos.
- `ed98d765e8e3d8f82d10028ea4c6adabd43a45d1` — testes e CI.

A documentação e as capturas ficam em um terceiro commit. Para listar o conjunto:
`git log --oneline main..HEAD`. Revisão final incluiu arquivos não rastreados,
busca de padrões de segredos e tamanhos: nenhum ZIP eleitoral, SDK, APK,
executável ou cache entrou nos commits. Nenhum arquivo versionado excede 1 MiB.
