# Explorador geográfico M5

Atualização M5.2 (31/10/2026): **143/145 localidades, 100 países/territórios**,
pacote `geography-2026-2`, correspondência v2. O cadastro TSE de locais de votação
de 2026 confirma 26 associações adicionais por código/zona/seção/local/turno,
com literais de país revisados individualmente. Bruxelas e Trípoli permanecem
no residual. Fontes, critérios, conflitos e reprodução em
[M5.2 — investigação ZZ](M5_2_ZZ_COUNTRY_INVESTIGATION.md) e
[vetores de reconciliação](M5_2_VALIDATION_SUMMARY.json).
As contagens e a descrição do edital nas seções históricas abaixo documentam
o ponto de partida M5; os JSONs eleitorais M4 e a cartografia foram preservados.

O app continua offline, sem API/backend, tiles, SQLite embarcado ou pacote novo de
mapas. Resumo e Comparar usam os mesmos componentes em Brasil, UF, município,
Mundo, país/território e localidade eleitoral. O total Brasil continua incluindo
o exterior; Mundo contém exclusivamente o exterior e não o adiciona novamente.

## Navegação

`/`, `/uf/SP`, `/uf/SP/municipio/71072`, `/mundo`, `/mundo/US` e
`/mundo/US/localidade/29416` aceitam `turno=1|2` e
`visao=summary|comparison`. `visao=insights` redireciona para `summary`, preservando
o restante do endereço. Os links anteriores `/uf/ZZ[/municipio/<código>]`
redirecionam para `/mundo[/localidade/<código>]`. Essa última forma também mantém
acesso direto a localidades sem país confirmado. Chaves incompatíveis não
fabricam resultados. Voltar segue localidade → país → Mundo → Brasil ou
município → UF → Brasil, conservando turno e visualização.

O país selecionado altera câmera e painel. Setas/Enter permitem selecionar UFs
e países com dados; Home/Escape retornam à visão geral do mapa. Busca, lista,
seletor de país e breadcrumbs oferecem alternativas acessíveis. Países ativos
são recalculados para o turno selecionado. Resultados assíncronos antigos não
podem substituir a seleção atual.

## Pontos municipais

Fonte de correspondência: [catálogo TSE↔IBGE](https://dadosabertos.tse.jus.br/dataset/codigos-oficiais-de-uf-e-municipios-segundo-o-tse-e-o-ibge),
recurso `c6c767d7-f341-4256-8dff-010683a9c796`. O catálogo foi criado em 2025,
mas o ZIP efetivamente recebido tem Last-Modified de **25/10/2026 12:00:33 UTC**.
O CSV interno declara geração **25/10/2026 09:00:09** e contém 5.571 linhas.
Licença declarada pelo portal: Creative Commons Attribution (sem versão
especificada nessa declaração). Não aplicar a licença MIT do código a esse dado.

Os pontos vêm de [IBGE, Localidades do Brasil, Censo 2022](https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/),
`Localidades_Brasil_gpkg.zip`, 6.477.540 bytes, publicado em **19/11/2025**.
O GeoPackage tem atualização interna de 14/11/2025, EPSG:4674 (SIRGAS2000).
São usados apenas pontos de cidade/sede e o distrito de Fernando de Noronha,
com `CD_LOCALIDADE = CD_MUN`. Duplicatas idênticas de capitais são consolidadas;
coordenadas divergentes para a mesma chave são recusadas. Não se juntam nomes.

Junção: `(UF, código TSE preenchido à esquerda até cinco dígitos)` →
`CD_MUNICIPIO_IBGE` → `(SIGLA_UF, CD_MUN)`. O asset preserva tanto a grafia
textual do código M4 (`1007`) quanto o código textual oficial (`01007`), além do
IBGE (`1200138`). Essa normalização trata zeros de apresentação de um mesmo
identificador; não converte códigos TSE em códigos IBGE.

As coordenadas são transformadas por PROJ/pyproj, operação SIRGAS2000 → WGS84 (1),
precisão declarada de 1 metro, e arredondadas a seis casas. Isso não implica que
o ponto original ou a malha simplificada tenham precisão métrica. Todos os
**5.571 identificadores domésticos do M4 têm ponto confirmado**, incluindo
Brasília/DF, Fernando de Noronha/PE e Boa Esperança do Norte/MT. DF e Fernando
de Noronha são rotulados `representative`; os demais são `seat`.

`municipal_locations.json` é um catálogo compacto com colunas declaradas, fontes,
versão, transformação e ausências. Não contém polígonos municipais. O marcador
não representa urna, escola ou local de votação. O mapa mantém a câmera estadual
e amplia o enquadramento quando necessário para incluir uma ilha, como Noronha.
Uma chave sem ponto confiável continua mostrando seu resultado sem marcador.

Condições adotadas para IBGE: reutilização de dados públicos com atribuição,
sem atribuir uma licença CC/SPDX que o recurso não declara. O índice oficial
identifica os arquivos como públicos. Ver também a documentação anterior em
[CARTOGRAPHY.md](CARTOGRAPHY.md); os termos da Agência de Notícias não são usados
para relicenciar cartografia.

## Exterior: associação por identificadores, com lacunas explícitas

Foram inspecionadas as três planilhas oficiais ligadas à
[notícia TRE-DF de 02/09/2026](https://www.tre-df.jus.br/comunicacao/noticias/2026/Setembro/eleicoes-2026-consulte-os-locais-e-as-secoes-eleitorais-para-votacao-no-exterior).
Os arquivos anunciados como XLS são, efetivamente, ZIPs contendo XLSX.
As planilhas eletrônica/manual relacionam país, cidade, endereço, aptos e
quantidades, mas não fornecem códigos TSE de município nem números individuais
das seções. Na planilha de dispensadas, o campo Código é de **local de votação**
(por exemplo, 1015 se repete); não é código de município e não foi usado como tal.

A associação implementada usa o
[edital oficial de carga e lacração de 2026](https://www.tre-df.jus.br/comunicacao/noticias/arquivos/edital-carga_e_lacracao_das_urnas_eletronicas__df_e_zz____2026/@@download/file),
Last-Modified **15/09/2026 15:32:26 UTC**, 1.116.535 bytes. As primeiras 30 páginas
contêm país e seções principais; páginas posteriores com dados de pessoal não
são extraídas para os assets. Conferência visual da estrutura e extração de
tabelas são feitas com pdfplumber. Usa-se **somente a coluna Seções Principais**.
Não usar a coluna Seções Agregadas: há números repetidos/inconsistentes nela.

O SQLite M3.1 não contém país em suas tabelas nem nos metadados. A consulta
`SELECT DISTINCT municipality, zone, section FROM sections WHERE uf='ZZ'`
fornece as identidades observadas. Todas estão na zona `1`; cada número de seção
identifica uma única localidade/zona na união dos turnos observados. Somente
essas chaves únicas são juntadas às seções do edital exterior. Uma localidade
só recebe país se **todas as evidências encontradas para seu código concordam**.
O asset guarda código TSE, nome original, ISO, país de apresentação, status e
evidência `(ISO, zona, seção, página)`. Nomes de cidades não atribuem países.

O edital contém 1.282 seções principais únicas (uma repetição idêntica, 3310).
Há 1.309 seções distintas observadas na união dos turnos, 1.281 compartilhadas,
28 apenas observadas e uma apenas planejada (936). Esses conjuntos não são
intercambiáveis: o edital trata de planejamento/carga eletrônica do primeiro
turno, enquanto o M4 contém registros efetivamente observados, inclusive manuais.

Resultado histórico M5: **117/145 localidades associadas a 80 países/territórios**.
Há 27 sem junção verificável e uma contraditória: código `29432`, BRUXELAS.
Seções 1935–1940, 3097, 3212, 3293, 3356, 3455 e 3681 apontam para BE na página 4;
1946 e 1947 apontam para LU na página 22, embora pertençam ao mesmo código nos
dados observados. O código inteiro fica sem país atribuído. Não resolver essa
contradição por nome, maioria de seções ou consulado.

Escócia/Reino Unido são consolidados em ISO GB. Hong Kong, Taiwan, Palestina e
Guiana Francesa preservam a identidade ISO usada para apresentação cartográfica;
isso não constitui afirmação sobre soberania. As traduções/aliases de **nomes de
países**, revisadas no construtor, não são inferências a partir de cidades.
O edital é um ato oficial público, creditado ao TRE-DF; não se atribui licença
MIT ou Creative Commons não declarada a esse documento.

## Cartografia mundial

Foram investigados [Natural Earth 1:110m](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/)
e [1:50m](https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-0-countries-2/),
ambos versão 5.1.1. A camada 110m omite países pequenos. Adotaram-se
`ne_50m_admin_0_map_units` e os nomes de país de `ne_50m_admin_0_countries`,
obtidos do espelho oficial NACIS após timeout no S3. As unidades separam Guiana
Francesa e outros territórios e são agrupadas por ISO_A2_EH; unidades sem ISO
ficam neutras com identificador cartográfico próprio. São 250 grupos renderizados,
incluindo unidades neutras, e não uma contagem política de países.

Simplificação com tolerância de 0,04 grau e preservação topológica em Shapely;
arredondamento a quatro casas. Polígonos, múltiplas partes e anéis interiores são
mantidos. A câmera usa um corte no maior intervalo vazio de longitudes e cópias
periódicas para tratar o antimeridiano. Países pequenos têm alvo mínimo de toque
e ponto de apresentação, com alternativa na lista. A projeção não conserva área.

[Licença Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/):
domínio público, inclusive modificações e redistribuição. Crédito: colaboradores
Natural Earth. Fronteiras são cartográficas e não expressam reconhecimento
oficial de disputas territoriais.

## Integridade, agregação e reprodução

Os quatro arquivos novos ficam em `assets/geo/`, independentes dos 32 JSONs M4.
`manifest.json` declara versões, licenças, fontes e SHA-256. Seu próprio hash é
fixado em `GeographicAssets`; o cliente verifica todos os bytes antes de usar
pontos, correspondência ou mundo. O mapa mundial é lido sob demanda. Uma
correspondência de outra versão eleitoral não ativa países neste dataset.

O cliente soma somente as localidades verificadas para o país; o total exterior
original continua sendo usado na visão Mundo. O exportador leve reproduz essa
partição com inteiros, campos ausentes, cobertura por seção e catálogo real de
candidatos. Países sem segundo turno não ganham uma linha artificial. Não são
exportados percentuais. A UI suprime percentuais de países enquanto existirem
lacunas globais de correspondência e também respeita campos eleitorais parciais.

O contrato v2 acrescenta `verified_official_section_register`, com fonte oficial,
hash do ZIP e do CSV, versão e referência de registro para cada turno observado.
O cliente e o exportador recusam país por nome, evidências conflitantes,
identificadores repetidos e cobertura de seções/turnos incompatível. `NM_BAIRRO`
não é um código de país: somente literais revisados e corroborados podem ser
usados. As evidências originais `verified_section_join` continuam compatíveis.
O exportador atual usa regras `country-2`, fixa o hash das regras e propaga
integralmente `public_readiness` do M4. O derivado histórico `country-1` permanece
intacto em seu diretório original.

```powershell
$env:PYTHONPATH = 'pipelines'
python -m tse_importer.country_exporter `
  --source apps/votoaberto_flutter/assets/data/real `
  --correspondence apps/votoaberto_flutter/assets/geo/overseas_correspondence.json `
  --output .local/m5_2/country-export-repro
```

Isso cria um derivado separado `releases/<id>/countries.json` + manifesto. O ID
depende da versão M4, hash do manifesto, hash da correspondência e regras
`country-2` e hash das regras. Repetir entradas reproduz bytes; divergência numa
versão existente é recusada. Não altera release, instalador ou ponteiro M4. A reconciliação exige
igualdade integral de candidatos, categorias, seções e disponibilidade:
países = localidades mapeadas; países + residual não mapeado = exterior M4.
Uma partição parcial nunca é rotulada como total completo.

O construtor `tools/geography/build_geography.py` recebe somente fontes auxiliares
locais já inspecionadas e SQLite em modo somente leitura. Dependências de autoria
estão em `tools/geography/requirements.txt`; não entram no app ou na CI de votos.
Ele recusa diretório de saída existente. Seus nomes de entrada estão documentados
no módulo. Os downloads/fontes brutas permanecem na área local ignorada. Nenhum
dos ZIPs eleitorais anteriores é aberto ou reprocessado por esse construtor.

A CI usa a mini-base **sintética**, geometrias eleitorais fictícias nos testes de
interação e assets cartográficos estáticos na verificação de hashes/coordenadas.
Não precisa dos dados eleitorais reais, de fontes externas ou do SQLite nacional.
Para compilar prévias reais sem sobrepor builds anteriores:

```powershell
python tools/geography/prepare_preview.py --target .local/m5/preview
cd .local/m5/preview/apps/votoaberto_flutter
flutter pub get --offline
python tool/embedded_build.py windows --mode real -- --no-pub
python tool/embedded_build.py web --mode real -- --no-pub
python tool/embedded_build.py apk --mode real -- --no-pub
```

O destino deve ser novo. O script copia fontes e assets sem deletar arquivos,
sem Git/branch adicional e sem modificar originais. O executável Windows requer
toda a pasta Release. Web usa somente arquivos estáticos do próprio host; não
garante primeira visita ou reinício offline do navegador. PWA segue fora do marco.
APK debug não comprova execução em aparelho físico. Ver resultados e lacunas em
[M5_COMPLETION_REPORT.md](M5_COMPLETION_REPORT.md).
