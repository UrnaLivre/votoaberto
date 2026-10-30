# ADR 0004 — JSON municipal embarcado no MVP

Estado: aceito para implementação e validação local no M4.

## Contexto

A release nacional M3.1 contém resultados presidenciais reconciliados em SQLite
de 935.424.000 bytes. O cidadão precisa consultar Brasil, UF e município sem
baixar esse banco, ZIPs ou depender de uma API. A prontidão pública da fonte
continua `not_ready`. Os ADRs 0001–0003 e as fronteiras público/Auditor permanecem.

## Decisão

Acrescentar ao Data Engine um exportador independente do Flutter que lê a release
em modo somente leitura, agrega municípios e confere os JSONs por consultas SQL
independentes. Totais por seção são somados sem JOIN multiplicador por candidato.
Uma release imutável e determinística contém manifesto, Brasil, UFs e um JSON
municipal por abrangência, com catálogo nominal normalizado por eleição/turno.
Ausências permanecem explícitas; códigos TSE textuais e exterior são preservados.

O Flutter mantém `ElectionRepository`, acrescenta carregamento municipal por
`AssetBundle`, cache limitado e navegação incremental. Não incorpora SQLite,
servidor, API, BUs integrais ou novo mapa municipal. Build real exige pacote
validado e pins de identidade; fixture/demo são modos explícitos separados.
O pacote real é gerado/instalado localmente, fora do Git e sem publicação automática.

## Consequências

A primeira carga tem só Brasil/UFs; custo municipal é por UF. A normalização
reduziu os arquivos de dados medidos de 11.130.583 para 4.448.955 bytes, antes
dos manifestos. O pacote completo medido tem 4.475.495 bytes. Não é necessário
GZIP no cliente. Atualizações exigem outro build/pacote completo validado; consulta
por seção e dados adicionais continuam destinadas à futura API, sem antecipá-la.

Hashes detectam mudanças de bytes; não autenticam a origem eleitoral. A avaliação
M3.1 é propagada integralmente e permite apenas a prévia local autorizada. Web
usa arquivos estáticos; offline entre sessões/PWA não é anunciado sem solução
de cache validada. Operação, falhas e atualização:
[EMBEDDED_DATA_MVP.md](../EMBEDDED_DATA_MVP.md).
