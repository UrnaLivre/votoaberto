# ADR 0005 — Geografia separada e exterior com cobertura explícita

Status: adotada no M5.

## Contexto

O M4 é uma release eleitoral imutável. Município TSE e município IBGE são
identificadores diferentes. A abrangência técnica ZZ contém localidades
eleitorais, não países, e as planilhas de planejamento não fornecem uma junção
municipal direta. Uma visualização nacional de ranking dentro da seleção
municipal produzia contexto contraditório.

## Decisão

Manter somente Resumo/Comparar e migrar links antigos. Acrescentar Brasil/Mundo
com uma hierarquia exclusiva de navegação. Reutilizar painter vetorial,
MapViewport, animação e resultados existentes, com uma camada Natural Earth
estática. Não introduzir API, tiles ou dependências cartográficas no cliente.

Versionar pontos, correspondência exterior e mapa em pacote independente com
manifesto e hashes verificados. Associar municípios apenas por identificadores
TSE↔IBGE oficiais. Associar exterior por seção única observada e país do edital
TRE-DF; rejeitar associações contraditórias. A ausência de país não remove votos.

Somar países somente a partir das localidades verificadas. Preservar o total
exterior original; reconciliar os países com a cobertura mapeada e acrescentar
um residual explícito para reconciliar o exterior completo. Exportar um novo
derivado determinístico em diretório independente, sem instalar sobre o M4.

## Consequências

Os pontos têm cobertura doméstica auditada integral; a cobertura exterior é
parcial. Países desconhecidos não são inferidos por nomes. Percentuais de país
ficam indisponíveis enquanto houver lacunas globais. A metodologia e o relatório
documentam as diferenças entre planejamento e votação observada. O app continua
pequeno e offline; novas fontes verificáveis podem ampliar a cobertura mediante
outro pacote geográfico e outro derivado, preservando os anteriores.

Detalhes, fontes e reprodução: [Explorador geográfico](../GEOGRAPHIC_EXPLORER.md).
