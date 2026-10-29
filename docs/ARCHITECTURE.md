# Arquitetura do VotoAberto

> M1 implementa Flutter + mock. O próximo marco (M2) implementará o motor de importação e a CLI do Auditor; backend/API permanecem futuros.
> Decisões efetivas: [mapa vetorial](adr/0001-vector-map.md) e
> [estado, domínio e navegação](adr/0002-state-data-navigation.md).

## Componentes

```text
[TSE: ZIPs oficiais completos, preservados fora do Git]
                           |
              [Data Engine compartilhado]
               inventário / filtros / validação
                      /           \
         [perfil público]     [perfil analista]
         SQLite compacto       dados técnicos
         + manifesto           + relatórios
              |                     |
       [API/arquivo futuro]  [Auditor CLI: Win/Linux]
              |
   [Flutter: Windows | Web | Android]
              |
     ElectionRepository
       mock (M1) / real (futuro)
```

**M1:** apenas **Flutter + mock**, sem servidor, banco ou ZIP oficial. **M2:** importador compartilhado + Auditor CLI, com SQLite público de saída e manifestos. A troca do mock por dados reais continuará atrás do contrato de repositório, em etapa posterior à validação.

## Estrutura-alvo (ajustável durante o scaffold)

```text
apps/
  votoaberto_flutter/         # Flutter Windows, Web e Android
  votoaberto_auditor/         # CLI local Windows/Linux planejada para M2
backend/                      # ASP.NET Core (futuro)
pipelines/
  tse_importer/              # importação compartilhada planejada para M2
docs/                         # escopo, decisões, fontes
data/
  raw/                        # fora do Git
  processed/                  # fora do Git
  samples/                    # apenas pequenos dados sintéticos/licenciados
```

A estrutura Flutter existe para Windows, Web e Android. `backend/` e `pipelines/`
contêm somente README de escopo futuro, sem implementação fictícia. O contrato
de dados fica em `features/elections/domain`; UI em `features/explorer/presentation`;
renderização geográfica em `features/map`. O composition root é `lib/main.dart`.

## Modelo de domínio (conceitual)

- `Election`: identificação, ano, cargo.
- `Round`: primeiro ou segundo turno; não inferir disponibilidade apenas pelo número da eleição.
- `GeographicScope`: Brasil, UF, município, exterior quando aplicável.
- `ElectoralLocation`: município, zona, seção, identificadores oficiais e eventuais particularidades.
- `CandidateResult`: candidato, número, votos e contexto da apuração; **sem dados reais na fase mock**.
- `VoteTotals`: aptos, comparecimento, abstenção, válidos, brancos/nulos, quando disponíveis; tipos e definições explícitas.
- `BallotReportReference`: fonte, identificadores, caminho, hash e status de correspondência, introduzido na fase de importação.
- `DataProvenance`: origem, versão, data de coleta e transformações; usar nos dados reais.

Nunca usar apenas o número de seção como chave global. Chaves de consulta devem considerar eleição, turno, UF, município, zona e seção, e outros campos que os arquivos reais demonstrarem necessários.

## Requisitos de arquitetura do frontend

- UI desacoplada de fonte e transporte de dados.
- Estado de seleção/navegação centralizado, reprodutível, com back/forward quando possível.
- Camada de mapa isolada da navegação de domínio; oferecer adaptador/substituição se o pacote cartográfico não funcionar em alguma plataforma.
- Resultados agregados tipados e testáveis; não calcular medidas incompatíveis sem validar denominadores.
- Camada de apresentação preparada para localização e acessibilidade.
- Testes unitários para agregações fictícias, widgets para navegação, smoke tests e testes de compatibilidade de plataformas.
- Sem segredos ou credenciais embarcados em aplicativo público.

## Mapas

M1 usa GeoJSON simplificado do IBGE com `CustomPainter`, transformação e hit-test,
sem tiles nem WebView. MapLibre e flutter_map foram avaliados documentalmente;
não foram incorporados nem declarados testados. Detalhes e tradeoffs no ADR 0001;
proveniência/condições em [CARTOGRAPHY.md](CARTOGRAPHY.md). Não há polígonos de
zonas, seções, urnas ou exterior.

## Importação, Auditor e backend (M2 e etapas posteriores)

- Implementar **um motor de importação reutilizável**, configurável por cargo, turno, território e perfil. O padrão é **presidente, ambos os turnos e perfil público compacto**; outros cargos dependem de suporte validado por schema.
- O **VotoAberto Auditor** começa como CLI em Python para Windows/Linux e poderá trabalhar com os ZIPs integrais e metadados técnicos.
- O **VotoAberto público não armazena BUs completos**: receberá somente o que for necessário à consulta presidencial por seção e suas referências de proveniência. Os ZIPs e BUs continuam sendo insumos e fontes de conferência do Auditor/pipeline.
- Preservar arquivos originais fora do Git e jamais apagá-los automaticamente; calcular SHA-256 de cópia e conferir referências oficiais SHA-256/SHA-512 **quando estiverem disponíveis**, sem confundir hash com assinatura digital.
- Escolher o schema concreto após a inspeção dos datasets. **SQLite versionado + manifesto de integridade + relatório de validação** é a primeira forma de exportação pública proposta; DuckDB/Parquet podem ser usados internamente para análise e reconciliação.
- API ASP.NET Core, banco hospedado e distribuição pública serão decididos após medir volume, latência e cobertura. O Flutter não deverá carregar todos os dados por navegador/móvel sem estratégia de consulta.

Veja [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md), [ADR 0003](adr/0003-public-data-and-auditor.md) e [DATA_POLICY.md](DATA_POLICY.md).
