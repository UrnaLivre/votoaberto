# Arquitetura do VotoAberto

> M1 implementa Flutter + mock. Backend, API e pipelines do diagrama continuam futuros.
> Decisões efetivas: [mapa vetorial](adr/0001-vector-map.md) e
> [estado, domínio e navegação](adr/0002-state-data-navigation.md).

## Componentes

```text
[Flutter: Windows | Web | Android]
          |
          | ElectionRepository (contrato)
          +------------------+
          |                  |
 [MockRepository]       [ApiRepository]   <-- implementação futura
                              |
                       [ASP.NET Core API]  <-- futura
                              |
               [base normalizada/indexada]
                              ^
                              |
                 [pipeline Python / DuckDB]
                              ^
                              |
             [arquivos oficiais do TSE, imutáveis]
```

**Etapa inicial:** implementar apenas o **Flutter + mock**, sem requerer servidor, banco, download de dados nem rede para carregar as estatísticas de demonstração. A troca do mock por API deve ocorrer atrás do contrato de repositório.

## Estrutura-alvo (ajustável durante o scaffold)

```text
apps/
  votoaberto_flutter/         # Flutter Windows, Web e Android
backend/                      # ASP.NET Core (futuro)
pipelines/                    # importação/validação (futuro)
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

## Backend e dados (etapas futuras)

- Processar ZIPs **fora do Git**, preservando originais e manifesto de SHA-256.
- Avaliar Python + DuckDB para normalização e conferência, ASP.NET Core para API, PostgreSQL para índices e object storage para artefatos originais.
- Só fixar schema, índices, arquitetura de hospedagem e custo após examinar arquivos reais.
- API paginada e agregações pré-calculadas para evitar transferir bases completas ao cliente.
- Um modo de auditoria local/reproduzível deverá poder reprocessar as fontes sem confiar nos totais da nossa API.

Detalhes da rastreabilidade em [DATA_POLICY.md](DATA_POLICY.md).
