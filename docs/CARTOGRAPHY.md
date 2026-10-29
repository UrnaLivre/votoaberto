# Cartografia embarcada — IBGE

Material de terceiro, **não relicenciado como MIT**.

- Autor/fonte: Instituto Brasileiro de Geografia e Estatística (IBGE).
- Produto: API de Malhas Geográficas v3, Brasil com intrarregião UF,
  qualidade intermediária. A API descreve o produto como **malha simplificada**.
- [Documentação oficial](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3).
- [Recurso exato](https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=intermediaria&intrarregiao=UF).
- Consulta/download: 2026-10-29; sem parâmetro `periodo`. A versão territorial
  não é declarada no corpo recebido: não afirmar que é malha de 2026.
- Arquivo: `apps/votoaberto_flutter/assets/geo/br_states.geojson`, 251.135 bytes.
- SHA-256: `09bc90c2391229ed1b07f11bbde0986180139f64b5e882379d8926c21eff0052`.
- 27 features, identificadas por `properties.codarea` (código IBGE de UF).
- Nenhuma simplificação adicional, remoção de ilha ou arredondamento aplicado.
  Os bytes recebidos são mantidos; transformação de projeção somente no render.

## Condições de reutilização verificadas

O recurso não contém identificador SPDX ou declaração Creative Commons.
Não o rotulamos arbitrariamente como CC BY ou MIT. A condição de uso adotada
é **reutilização com atribuição ao IBGE**.

Evidência específica: [declaração do Atendimento IBGE, protocolo 8171/2009-1,
preservada na lista pública de imports OSM](https://lists.openstreetmap.org/pipermail/imports/2013-July/001981.html).
A correspondência do órgão informa domínio público dos conteúdos do portal,
condicionando sua utilização à citação da fonte. É uma cópia pública de
correspondência, não uma licença CC emitida para este endpoint.

Contexto primário adicional: [política federal de dados abertos — Governo
Digital](https://www.gov.br/governodigital/pt-br/estrategias-e-governanca-digital/sisp/guia-do-gestor/pda),
que descreve livre utilização de dados abertos com crédito à autoria/fonte;
e [Plano de Dados Abertos do próprio IBGE 2024–2025](https://www.ibge.gov.br/np_download/novoportal/documentos_institucionais/Plano_de_Dados_Abertos_IBGE_2024_2025.pdf).
Os termos da Agência de Notícias não foram usados para licenciar cartografia.

A aplicação credita o IBGE no mapa e no diálogo de fontes. A documentação
registra origem, alterações e limitações. Isso não sugere endosso do IBGE.

## Reprodução e limites

```powershell
Invoke-WebRequest 'https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=intermediaria&intrarregiao=UF' -OutFile br_states.geojson
Get-FileHash br_states.geojson -Algorithm SHA256
```

O endpoint pode mudar o conteúdo: conferir hash antes de substituir o asset,
registrar nova consulta e executar os testes geométricos. Manter a cópia
versionada permite reproduzir a aplicação sem depender da API.

Não usar esta malha simplificada para medições, delimitar zonas eleitorais,
posicionar urnas ou resolver disputas de fronteira. Rótulos são âncoras de
interface, sem significado eleitoral. A projeção de apresentação não conserva
áreas. Exterior ZZ não é uma UF nem possui polígono neste mapa.
