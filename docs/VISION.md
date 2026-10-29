# Visão e experiência do produto

## Propósito

O VotoAberto pretende tornar os resultados eleitorais oficiais do Brasil **fáceis de consultar, contextualizar e conferir**, com metodologia aberta. Seu primeiro recorte é a eleição **presidencial de 2026**, nos dois turnos. O público inclui cidadãos, jornalistas, pesquisadores e desenvolvedores.

**Não é** um sistema de votação, um substituto para o TSE, uma certificação de integridade de urnas ou um mecanismo capaz de provar a regularidade/irregularidade de uma eleição só com estatística.

## Jornada principal

1. Na página inicial, um **mapa político do Brasil** ocupa a área visual principal; um painel lateral contém opções de exploração.
2. Ao selecionar uma **UF**, a região fica destacada e o mapa aproxima a seleção. O painel muda de contexto e mostra estatísticas do **primeiro e segundo turnos**.
3. O usuário pode pesquisar/selecionar **município**, depois navegar por **zona e seção eleitoral**, conforme a identificação oficial.
4. Uma seção apresenta resultados por turno e, futuramente, links para o **registro de boletim de urna correspondente** e seus metadados de proveniência.
5. O usuário pode voltar pelos breadcrumbs até o nível nacional, ajustar filtros, comparar métricas e acessar explicações acessíveis sobre cada cálculo.
6. No futuro, uma área **Explorar os Dados** oferece achados interessantes e análises reprodutíveis sem induzir conclusões.

A navegação geográfica é por **UF e município**. **Zonas e seções** podem ser selecionadas em listas, filtros e busca; não criar polígonos fictícios de zonas ou pontos exatos de seções sem fonte geográfica adequada.

## Experiência de uso

- **Desktop/Web largo:** mapa à esquerda/centro, painel contextual à direita; seleção com destaque e zoom suave.
- **Mobile:** mapa e painel em sequência ou painel inferior; sem esconder funcionalidades importantes atrás de interações não descobríveis.
- **Acessibilidade:** teclado, foco visível, contraste, labels semânticos, leitura de gráficos em texto/tabelas, redução de movimento.
- **Confiabilidade:** estados de carregamento, erro, ausência de resultados e fontes indisponíveis.
- **Linguagem:** português brasileiro inicialmente; preparar strings para internacionalização.

## Controles e visualizações esperados (por etapas)

- Mapa nacional: selecionar UF, recuperar seleção e zoom, buscar UF.
- Painel estadual: comparativo 1º/2º turno, votos válidos, brancos/nulos e comparecimento quando disponível e conceitualmente correto.
- Visão município/zona/seção: filtros hierárquicos e comparação sem pressupor equivalência automática de equipamento físico.
- Consulta ao BU: renderização legível **com proveniência explícita**, sem alegar ser o documento oficial se for apenas uma interpretação.
- Módulo de análises: histograma, distribuição, diferenças entre turnos, explicações e exportação com dados de origem.

## Critérios de confiança

Toda métrica deve responder: **de qual fonte veio?**, **qual conjunto/versão?**, **quais filtros?**, **qual fórmula?**, **o que não se pode concluir a partir dela?**

Na fase de protótipo, todos os valores sintéticos deverão ser visivelmente identificados como **FICTÍCIOS / DEMONSTRAÇÃO**. Evitar nomes, números ou percentuais que possam ser confundidos com resultados publicados.
