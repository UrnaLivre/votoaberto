# ADR 0001 — Cartografia vetorial local no M1

Estado: aceito. Data: 2026-10-29.

## Contexto

Windows, Web e Android são obrigatórios. M1 precisa de limites de 27 UFs,
hit-test, destaque, teclado e enquadramento; não precisa de ruas ou tiles.

Fontes consultadas:

- [maplibre 0.3.7](https://pub.dev/packages/maplibre): Android/iOS nativos,
  Web com maplibre-gl-js e Windows/macOS via WebView. Não executamos um spike
  MapLibre: a dependência de WebView já acrescenta uma camada dispensável ao M1.
- [maplibre_gl](https://pub.dev/packages/maplibre_gl): documentação não declara
  suporte desktop. Suporte do motor MapLibre Native não implica suporte do plugin.
- [flutter_map 8.3.2](https://pub.dev/packages/flutter_map): alternativa madura,
  pure Flutter e multiplataforma. Adequada se precisarmos de pan/tiles/projeções;
  adiciona dependências e recursos que o recorte atual não exige.

## Decisão

GeoJSON do IBGE embarcado, decodificado em `Path` com preenchimento even-odd,
preservando Polygon, MultiPolygon e anéis internos. `BrazilGeometry`,
`MapViewport` e `BrazilMap` isolam parsing, projeção e apresentação. Não há
tile remoto, WebView, token nem chamada de rede durante o uso.

Projeção equiretangular com paralelo padrão 14°S: escala uniforme na tela,
latitude invertida, longitude multiplicada por cos(14°). É uma projeção de
apresentação, não usada para áreas ou distâncias. Toda geometria recebida,
inclusive componentes insulares, participa dos limites. Não inventamos
polígonos para ZZ, zonas, seções ou equipamentos.

A câmera interpola retângulos geográficos, substitui a animação a partir da
posição atual e respeita `disableAnimations`. O enquadramento impõe extensão
mínima de 2,5 graus para regiões pequenas. Hit-test ordena limites menores
primeiro; busca/lista evita depender de acertar o DF em escala nacional.
Hover, foco por teclado e seleção têm estados distintos. Controles ficam como
irmãos do GestureDetector, impedindo propagação de cliques ao mapa.

Leitores de tela recebem um resumo do mapa e usam a lista/busca acessível de
UFs, equivalente funcional à seleção por polígonos. Evitamos 27 regiões
semânticas móveis sobrepostas durante o zoom; o teclado do mapa e a lista
oferecem todas as UFs independentemente do tamanho do polígono.

## Consequências

Mesmo desenho Flutter nas três plataformas; sem dependência cartográfica de
runtime. O projeto assume a manutenção do fit, hit-test e semântica, cobertos
por testes. Não oferece pan livre, pinch zoom, medição ou tiles. Um futuro
adaptador MapLibre/flutter_map pode substituir `BrazilMap` preservando o
contrato de seleção por UF e o repositório eleitoral.

Licenciamento/proveniência em [CARTOGRAPHY.md](../CARTOGRAPHY.md).
