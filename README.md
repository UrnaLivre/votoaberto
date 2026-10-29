# VotoAberto

**Explore, compare e confira os resultados eleitorais brasileiros.**

[English summary](#english-summary) · [Visão do projeto](docs/VISION.md) · [Arquitetura proposta](docs/ARCHITECTURE.md) · [Dados e proveniência](docs/DATA_POLICY.md) · [Roadmap](docs/ROADMAP.md) · [Como contribuir](CONTRIBUTING.md)

> **Em fase inicial de desenvolvimento.** Ainda não há aplicativo publicado nem resultados processados neste repositório. As primeiras interfaces poderão usar apenas dados sintéticos, identificados como demonstração.

O **VotoAberto** é um projeto de software livre do ecossistema [UrnaLivre](https://urnalivre.com.br/) para facilitar a exploração, a comparação e a conferência independente dos **dados eleitorais oficiais publicados pelo Tribunal Superior Eleitoral (TSE)**. A proposta é transformar conjuntos de dados complexos em consultas transparentes, acessíveis e reproduzíveis — sem substituir os documentos de origem.

## O que queremos construir

- **Mapa interativo do Brasil** com navegação de país → unidade federativa → município → zona → seção eleitoral, de acordo com a granularidade efetivamente presente nas fontes.
- **Resultados presidenciais de 2026**, comparando o primeiro e o segundo turnos, com cobertura nacional e do eleitorado no exterior quando disponível.
- **Consulta a boletins de urna (BU)**, com referência inequívoca ao arquivo/registro de origem, identificação e informações de integridade.
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

## Dados oficiais e responsabilidade

Fonte primária prevista: [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/), especialmente os conjuntos de **resultados por seção eleitoral** e **boletins de urna**. Os arquivos brutos não serão incorporados ao histórico do Git; a proposta é fornecer um pipeline documentado para que outros possam obter os originais e reproduzir os resultados.

O projeto é **independente**: não é mantido, patrocinado, homologado nem endossado pelo TSE. A disponibilização de dados oficiais não implica validação, pelo TSE, das análises feitas aqui. Consulte a [política de dados e atribuição](docs/DATA_POLICY.md) antes de republicar dados de terceiros.

## Tecnologia e estágio atual

A arquitetura **proposta** considera Flutter/Dart para a interface, API ASP.NET Core, processamento Python/DuckDB e armazenamento indexado. São decisões iniciais que serão testadas e documentadas; não significa que esses componentes já tenham sido implementados.

| Etapa | Estado |
| --- | --- |
| Documento de visão, princípios e plano inicial | Em elaboração |
| Protótipo de interface com dados sintéticos | Planejado |
| Importação e validação dos arquivos do TSE | Planejado |
| Consulta por zona, seção e boletins originais | Planejado |
| Publicação Web / Windows / Android | Planejado |

Para detalhes e critérios de aceitação, consulte o [roadmap](docs/ROADMAP.md).

## Relação com o UrnaLivre

O **UrnaLivre** é o ecossistema do qual o VotoAberto faz parte. O VotoAberto **analisa dados já publicados**; é um produto diferente da ideia futura de pesquisa em um **sistema de votação aberto e criptograficamente verificável**, possivelmente com técnicas de criptografia homomórfica. Não confundir as finalidades nem atribuir ao VotoAberto garantias criptográficas que ele não fornece.

## Colaboração e licença

Contribuições, sugestões de acessibilidade, revisão de métodos estatísticos, modelagem geográfica, documentação e testes são bem-vindos. Veja [CONTRIBUTING.md](CONTRIBUTING.md).

**Código-fonte:** licença [MIT](LICENSE), salvo indicação expressa em contrário. **Dados do TSE, cartografia, marcas e demais materiais de terceiros:** sujeitos às suas respectivas licenças e condições; a licença MIT do código **não** se estende automaticamente a eles.

---

## English summary

**VotoAberto** is an independent, open-source project within the **UrnaLivre** ecosystem to explore, compare, and trace Brazil's officially published election results back to their sources. The initial scope is the **2026 presidential election**, both rounds, with a navigable Brazil map and future polling-station/ballot-report consultation.

The project is at an **early planning stage**. No real results have yet been processed here. Any early sample statistics must be visibly marked as **FICTIONAL**. Statistical outliers are **not**, by themselves, proof of misconduct. VotoAberto is **not affiliated with or endorsed by the Brazilian Superior Electoral Court (TSE)**.

The source code is MIT-licensed; third-party datasets, maps and trademarks retain their own terms.
