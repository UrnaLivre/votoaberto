# VotoAberto

**Explore, compare e confira os resultados eleitorais brasileiros.**

[English summary](#english-summary) · [Visão do projeto](docs/VISION.md) · [Arquitetura proposta](docs/ARCHITECTURE.md) · [Arquitetura de dados](docs/DATA_ARCHITECTURE.md) · [Dados e proveniência](docs/DATA_POLICY.md) · [Roadmap](docs/ROADMAP.md) · [Como contribuir](CONTRIBUTING.md)

> **Flutter M1 — demonstração funcional local.** O aplicativo continua usando **somente dados sintéticos**. M2 implementa Data Engine, Auditor CLI e uma primeira importação local de SC, documentada separadamente. Originais e derivados oficiais ficam fora do Git; não há aplicativo ou base publicados remotamente.

O **VotoAberto** é um projeto de software livre do ecossistema [UrnaLivre](https://urnalivre.com.br/) para facilitar a exploração, a comparação e a conferência independente dos **dados eleitorais oficiais publicados pelo Tribunal Superior Eleitoral (TSE)**. A proposta é transformar conjuntos de dados complexos em consultas transparentes, acessíveis e reproduzíveis — sem substituir os documentos de origem.

![Prévia real do M1 — mapa IBGE e números inteiramente fictícios](docs/images/m1-desktop.jpg)

## O que queremos construir

- **Mapa interativo do Brasil** com navegação de país → unidade federativa → município → zona → seção eleitoral, de acordo com a granularidade efetivamente presente nas fontes.
- **Resultados presidenciais de 2026**, comparando o primeiro e o segundo turnos, com cobertura nacional e do eleitorado no exterior quando disponível.
- **Consulta por seção eleitoral** com votos presidenciais, metadados mínimos e proveniência; os boletins de urna poderão ser usados na conferência e ter suas referências indicadas, **sem armazenar os BUs integrais na base pública**.
- **Painéis, filtros e gráficos** de votação, comparecimento, abstenção e variações entre turnos, respeitando as definições e limitações dos dados.
- **Análises exploratórias reproduzíveis**, com metodologia visível, possibilidade de exportação e explicações sobre hipóteses alternativas.
- **Experiência multiplataforma**: Windows, Web e Android, projetada para acessibilidade e uso por não especialistas.

O recorte inicial é **exclusivamente a eleição para presidente da República de 2026**. Outros anos e cargos podem ser considerados futuramente, mas não fazem parte do primeiro marco.

## Princípios

1. **Fontes primárias e rastreabilidade.** Distinguir sempre dados oficiais, processamento do projeto e interpretações.
2. **Nada de números inventados.** Dados demonstrativos devem ser claramente marcados como **FICTÍCIOS**, sem misturá-los aos resultados reais.
3. **Métodos verificáveis.** Documentar transformações, filtros, versões, algoritmos, hashes e divergências.
4. **Neutralidade político-partidária.** O software não endossa candidatos, partidos ou conclusões predeterminadas.
5. **Rigor nas inferências.** Uma anomalia estatística não prova fraude; a ausência de uma anomalia também não é prova geral de ausência de irregularidades.
6. **Transparência sobre limitações.** Uma seção eleitoral, seu boletim e um equipamento físico não devem ser tratados como equivalentes sem verificar os identificadores e eventos pertinentes.

## Produtos e estratégia de dados

O ecossistema adotará **um motor de importação configurável** e dois consumidores distintos:

- **VotoAberto (público):** Windows, Web e Android, com base derivada **compacta**, inicialmente apenas para **presidente da República em 2026**, nos dois turnos. O cidadão não precisa baixar os ZIPs completos do TSE para consultar os resultados. A base poderá apresentar votos por candidato e seção, totais definidos pelas fontes e proveniência, **sem armazenar boletins de urna integrais**.
- **VotoAberto Auditor (analistas):** ferramenta local para Windows e Linux, implementada inicialmente como CLI, que lê os arquivos oficiais completos, confere integridade, executa análises detalhadas e gera/reproduz as bases do VotoAberto.
- **Data Engine compartilhado:** importador com seleção de cargos, turnos, abrangências e perfis de exportação. Configuração padrão: **presidente, 1º e 2º turnos, perfil público compacto**. Outros cargos só serão habilitados após a validação de seus formatos específicos.

O formato inicial de entrega pública implementado no motor é **SQLite versionado, acompanhado de manifesto e relatório de validação**, antes de decidir a distribuição por API. O Flutter M1 continua usando apenas dados sintéticos. Veja a [decisão arquitetural ADR 0003](docs/adr/0003-public-data-and-auditor.md), a [arquitetura de dados](docs/DATA_ARCHITECTURE.md) e o [roadmap](docs/ROADMAP.md).

## Dados oficiais e responsabilidade

Fonte primária prevista: [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/), especialmente os conjuntos de **resultados por seção eleitoral** e **boletins de urna**. Os arquivos brutos não serão incorporados ao histórico do Git; a proposta é fornecer um pipeline documentado para que outros possam obter os originais e reproduzir os resultados.

O projeto é **independente**: não é mantido, patrocinado, homologado nem endossado pelo TSE. A disponibilização de dados oficiais não implica validação, pelo TSE, das análises feitas aqui. Consulte a [política de dados e atribuição](docs/DATA_POLICY.md) antes de republicar dados de terceiros.

## Tecnologia e estágio atual

A interface Flutter/Dart e o mock estão em `apps/votoaberto_flutter/`. O Data Engine e o Auditor CLI implementam inventário, hashes, parsers de dois layouts reais, reconciliação e SQLite local. [Investigação de SC](docs/TSE_2026_FORMAT_INVESTIGATION.md) e [operação](docs/DATA_ENGINE_OPERATIONS.md) registram evidências e limites. API ASP.NET Core, distribuição pública e integração Flutter continuam futuras, condicionadas à validação e ao dimensionamento.

| Etapa | Estado |
| --- | --- |
| Documento de visão, princípios e plano inicial | Publicado |
| Explorador Flutter com dados sintéticos | Implementado no M1; verificações em [VALIDATION.md](docs/VALIDATION.md) |
| Importador configurável e SQLite presidencial compacto | Implementados no M2; primeira validação local de SC, sem publicação remota |
| Consulta por zona e seção; referências aos boletins de origem | Planejado — M3 |
| Publicação Web / Windows / Android | Planejado |

Para detalhes e critérios de aceitação, consulte o [roadmap](docs/ROADMAP.md).

## Executar o aplicativo

Pré-requisitos: **Flutter 3.47.8 / Dart 3.13.7** (versão de referência do M1),
Git e navegador compatível. Windows requer Visual Studio com **Desktop development
with C++**, MSVC, CMake e Windows SDK. Android requer JDK 17, Android SDK e
licenças aceitas; veja também o diagnóstico `flutter doctor -v`.

```powershell
cd apps/votoaberto_flutter
flutter pub get
flutter run -d windows
# Ou navegador:
flutter run -d chrome
```

Na máquina de desenvolvimento desta entrega o SDK fica em `.local/flutter/`,
ignorado pelo Git, sem alterar o PATH global. Na raiz, para usar essa instalação:

```powershell
$env:PATH = "$PWD\.local\flutter\bin;$env:PATH"
cd apps/votoaberto_flutter
flutter doctor -v
flutter run -d windows
```

### Builds e testes

```powershell
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test --coverage
flutter build windows --release
flutter build web --release --no-web-resources-cdn
flutter build apk --debug
# Com um dispositivo/emulador Android configurado:
flutter devices
flutter run -d <id-do-dispositivo>
```

APK debug serve para validação local; assinatura/distribuição de produção não
estão configuradas. O workflow [Flutter M1](.github/workflows/flutter.yml)
verifica formato, análise, testes e builds, sem publicar artefatos em produção.
Resultados **efetivamente executados** e limitações: [relatório de validação](docs/VALIDATION.md).

### O que experimentar

Selecione uma UF pelo mapa ou pesquise nome/sigla (sem necessidade de acentos).
O mapa enquadra a seleção, o painel apresenta o estado e o seletor de turno
mantém essa seleção. Use **Comparar** para contagens, percentuais dos candidatos
e variações; **Explorar os Dados** para o ranking de comparecimento fictício.
**Brasil** retorna ao país. Tema e fontes ficam no cabeçalho.

No mapa, Tab dá foco; setas percorrem UFs alfabeticamente; Enter seleciona;
Escape/Home retorna ao Brasil. Busca/lista são alternativas para o DF e UFs
pequenas. Gráficos possuem resumos semânticos. A preferência de redução de
movimento desativa a animação do mapa. Desktop tem painel lateral com rolagem;
mobile/tablet usam mapa e painel em sequência, com rolagem vertical.

URLs Web usam o hash padrão do Flutter, por exemplo
`/#/uf/SP?turno=2&visao=comparison`; voltar/avançar recupera o recorte da URL.
Municípios, zonas, seções e boletins são explicitamente futuros, sem números
inventados. `ZZ` está previsto no modelo e não é um polígono do mapa.

### Código, dados e decisões

```text
apps/votoaberto_flutter/
  lib/app/                    composição, tema, strings e roteamento
  lib/core/                   formatação e componentes compartilhados
  lib/features/elections/     domínio, contrato e mock determinístico
  lib/features/explorer/      controller e experiência de exploração
  lib/features/map/           GeoJSON, projeção, hit-test, câmera e renderizador
  assets/geo/                 geometria IBGE e atribuição
  test/                       domínio, controller, mapa e widgets
backend/                      API planejada após validação dos dados
apps/votoaberto_auditor/       CLI Python local
pipelines/tse_importer/        motor compartilhado e SQLite
```

Estado com `ChangeNotifier`/`ListenableBuilder` e navegação com `go_router`.
`intl` e localizações Flutter fornecem pt-BR. O renderizador usa `CustomPainter`,
sem WebView, tiles, fontes externas ou chamadas de rede durante a exploração.
O mock-v1 é determinístico e matematicamente consistente, mas não representa
população, votação ou comportamento real. Brasil soma as 27 UFs; exterior não
incluído. Não inferimos transferência de votos entre pessoas.

- [Arquitetura e substituição pela API](docs/ARCHITECTURE.md)
- [Decisão de cartografia](docs/adr/0001-vector-map.md)
- [Estado, navegação e mock](docs/adr/0002-state-data-navigation.md)
- [Origem, condições de uso e hash do GeoJSON](docs/CARTOGRAPHY.md)

Continuam pendentes no aplicativo: integração TSE, cobertura exterior, API, consulta
granular e BU, exportação, identidade oficial, persistência de preferências,
segundo idioma, avaliação de acessibilidade com usuários e distribuição.

## Relação com o UrnaLivre

O **UrnaLivre** é o ecossistema do qual o VotoAberto faz parte. O VotoAberto **analisa dados já publicados**; é um produto diferente da ideia futura de pesquisa em um **sistema de votação aberto e criptograficamente verificável**, possivelmente com técnicas de criptografia homomórfica. Não confundir as finalidades nem atribuir ao VotoAberto garantias criptográficas que ele não fornece.

## Colaboração e licença

Contribuições, sugestões de acessibilidade, revisão de métodos estatísticos, modelagem geográfica, documentação e testes são bem-vindos. Veja [CONTRIBUTING.md](CONTRIBUTING.md).

**Código-fonte:** licença [MIT](LICENSE), salvo indicação expressa em contrário. **Dados do TSE, cartografia, marcas e demais materiais de terceiros:** sujeitos às suas respectivas licenças e condições; a licença MIT do código **não** se estende automaticamente a eles.

---

## English summary

**VotoAberto** is an independent, open-source project within the **UrnaLivre** ecosystem to explore, compare, and trace Brazil's officially published election results back to their sources. The initial scope is the **2026 presidential election**, both rounds, with a navigable Brazil map and future polling-station/ballot-report consultation.

The **M1 local Flutter explorer** uses a real 27-state IBGE map and deterministic synthetic results. M2 adds a shared Python engine and local Auditor CLI; an actual SC import is documented separately, with generated data excluded from Git. The Flutter app still uses only synthetic data. All sample statistics are visibly marked as **FICTIONAL**. Statistical outliers are **not**, by themselves, proof of misconduct. VotoAberto is **not affiliated with or endorsed by the Brazilian Superior Electoral Court (TSE)**. See the validation report for platform/build evidence and current limitations.

The source code is MIT-licensed; third-party datasets, maps and trademarks retain their own terms.
