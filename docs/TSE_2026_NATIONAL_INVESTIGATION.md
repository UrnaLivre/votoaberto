# Investigação e primeira importação presidencial nacional — M3.1

Em 29/10/2026 foi concluída a importação local dos arquivos fornecidos, para
presidente em ambos os turnos, com presença dos **56 pares de 27 UFs + ZZ**.
A elegibilidade local é **eligible** e a prontidão
pública permanece **not_ready**. Presença territorial e correspondência
entre fontes não comprovam completude de todas as seções ou integridade eleitoral.

Release canônica: `data/processed/national-2026/releases/6305f74561d4687a23bd3054/`.
`current.json` aponta essa única base ativa. SQLite com **935.424.000 bytes**;
SHA-256: `c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4`. Não houve publicação remota nem troca do mock Flutter.

## Fontes, hashes e atualização pelo operador

Foram inventariados 57 ZIPs (56 BWEBs e um nacional de votação por seção) e 56
auxiliares SHA-512, em subpastas de primeiro/segundo turno por UF/ZZ e `Votação por Seção/`.
Total inicial: 4.457.109.026 bytes; atual:
5.463.538.463 bytes. Nenhuma duplicata de bytes foi encontrada.
O motor só leu os originais; não os moveu, renomeou, alterou, recompactou ou extraiu
integralmente. Não fez downloads.

O primeiro preflight identificou nove ZIPs sem índice final válido, também recusados
por `zipfile.is_zipfile`, com SHA-512 divergente dos auxiliares locais. O operador
informou novos downloads e conservação dos backups antigos; substituiu os arquivos
no diretório de entrada. Todos os **56 BWEBs atuais coincidem com os auxiliares**
e passaram depois pela leitura integral/CRC. Os auxiliares não mudaram de identidade
de bytes entre os snapshots. Não foi determinada a causa das diferenças anteriores,
nem comparado o conteúdo eleitoral dos backups, conforme adiamento solicitado.

| BWEB do primeiro turno atualizado | Bytes do snapshot inicial | Bytes atuais |
| --- | ---: | ---: |
| ES | 61.791.678 | 81.978.606 |
| GO | 48.234.496 | 157.210.218 |
| MG | 115.638.272 | 489.306.781 |
| MS | 41.226.498 | 51.978.602 |
| MT | 20.663.182 | 63.492.478 |
| PA | 9.764.864 | 172.050.487 |
| PB | 10.382.587 | 77.916.707 |
| PE | 9.764.864 | 204.972.135 |
| PI | 41.226.960 | 66.216.824 |

[Inventário de fontes](TSE_2026_NATIONAL_SOURCE_INVENTORY.json) registra os hashes
SHA-256/SHA-512 completos, os estados anteriores/atuais, membros internos, tamanhos
de expansão e referências efetivamente disponíveis. Os catálogos integrais/amostras
ficam em `.local/`, fora do Git. A diferença de tamanho de um arquivo local não
determina, sozinha, o que mudou em uma publicação remota; não foi atribuída explicação.

As referências de SC/1 e SC/2 e suas URLs consultadas no M2 foram reutilizadas.
Os outros auxiliares são referências locais sem confiança automaticamente atribuída.
O ZIP nacional continua sem checksum oficial suficiente identificado. Seus hashes
calculados preservam identidade local, sem assinatura ou autenticação de origem.
O cache opcional usa tamanho/mtime/dispositivo/identidade, com recálculo dos arquivos
alterados e reavaliação de índices/referências; não substitui uma nova leitura contra
um agente hostil que restaure metadados. Seu uso bloqueia prontidão pública.

## Formatos confirmados e particularidades

Os 57 CSVs eleitorais foram lidos integralmente em fluxo, com conferência CRC:
BWEB com 45 campos, votação por seção com 26, Latin-1 e separador `;`. Presidente
exige cargo 1/descrição `Presidente`; eleição ordinária BWEB 0 versus seção 2/F/BR.
Nominais e códigos 95/96 representam categorias distintas, sem converter ausências
em zero. Tipos votáveis BWEB 1/2/3 e tipo de urna 1 foram aceitos no recorte;
schemas desconhecidos, tipo 97 e outras situações presidenciais continuam não
suportados e abortam, sem descarte silencioso. 57 PDFs auxiliares foram lidos
até CRC, explicitamente sem parser eleitoral.

Identificadores são texto com zeros preservados; município TSE não é código IBGE.
Chave comparada: eleição + UF + município + zona + seção + votável; local também
conferido. Contextos BWEB derivam dos campos originais de carga/urna/emissão/recepção
e agregações; não identificam universalmente equipamento físico. Nenhuma expansão
de seções agregadas ou soma de votos das duas fontes foi feita.

`DS_SECOES_AGREGADAS` inclui códigos únicos/listas separadas por `/` e sentinelas.
Os indicadores abaixo contam grupos de local/contexto com o campo preenchido,
não equipamentos ou seções artificiais. ZZ/2 contém duas linhas de cargo -1,
contadas fora do perfil público; AC/2 contém 8.925 linhas de governador. As gerações
e representações de data efetivamente lidas constam abaixo. Um CSV pode conter
mais de um grupo de geração/data de eleição. Não se inventa explicação para diferenças.

| Formato | Geração | Hora | Data de eleição original | CSVs com esse grupo | Linhas selecionadas |
| --- | --- | --- | --- | ---: | ---: |
| bweb | 05/10/2026 | 14:03:43 | 2026-10-04 00:00:00 | 28 | 3.800.511 |
| bweb | 26/10/2026 | 07:42:38 | 2026-10-25 00:00:00 | 28 | 1.931.103 |
| section | 26/10/2026 | 12:07:25 | 04/10/2026 | 1 | 3.800.511 |
| section | 26/10/2026 | 12:07:25 | 25/10/2026 | 1 | 1.931.103 |

| Fonte | Linhas lidas | Presidenciais selecionadas | Outros cargos ignorados | Grupos com agregação indicada |
| --- | ---: | ---: | ---: | ---: |
| bweb | 69.947.081 | 5.731.614 | 64.215.467 | 32.284 |
| section | 5.731.614 | 5.731.614 | 0 | 0 |

Quarentena: 0. A política
é estrita: registros selecionados inválidos/não suportados interrompem a carga.
Não há descarte permissivo ou correção automática para fechar totais.

## Cobertura observada e reconciliação

Contrato: NATIONAL, turnos 1/2, perfil público compacto. Cobertura esperada e
observada: 56 pares; `section_completeness` permanece `not_assessed`, pois não há
inventário independente exaustivo das seções esperadas. Municípios/zonas são códigos
observados dentro de cada UF; pares município/zona são informados separadamente no
resumo JSON. Exterior é ZZ, sem tratá-lo como uma 28ª UF.

| UF/ZZ | Turno | Seções | Resultados | Municípios | Códigos de zona | Seções matched | Não verificáveis |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AC | 1 | 2.270 | 16.145 | 22 | 9 | 2.270 | 0 |
| AL | 1 | 7.101 | 50.972 | 102 | 42 | 7.101 | 0 |
| AM | 1 | 8.157 | 58.575 | 62 | 60 | 8.157 | 0 |
| AP | 1 | 1.914 | 13.996 | 16 | 11 | 1.914 | 0 |
| BA | 1 | 35.476 | 251.417 | 417 | 199 | 35.476 | 0 |
| CE | 1 | 23.765 | 167.164 | 184 | 109 | 23.765 | 0 |
| DF | 1 | 6.969 | 55.819 | 1 | 19 | 6.969 | 0 |
| ES | 1 | 9.844 | 75.629 | 78 | 50 | 9.844 | 0 |
| GO | 1 | 15.686 | 112.157 | 246 | 92 | 15.686 | 0 |
| MA | 1 | 18.093 | 124.673 | 217 | 105 | 18.093 | 0 |
| MG | 1 | 52.062 | 415.799 | 853 | 304 | 52.062 | 0 |
| MS | 1 | 7.106 | 52.380 | 79 | 49 | 7.106 | 0 |
| MT | 1 | 8.287 | 60.750 | 142 | 57 | 8.287 | 0 |
| PA | 1 | 20.827 | 143.701 | 144 | 101 | 20.827 | 0 |
| PB | 1 | 10.712 | 76.265 | 223 | 68 | 10.712 | 0 |
| PE | 1 | 21.418 | 156.699 | 185 | 122 | 21.418 | 0 |
| PI | 1 | 10.225 | 69.308 | 224 | 74 | 10.225 | 0 |
| PR | 1 | 27.142 | 211.052 | 399 | 186 | 27.142 | 0 |
| RJ | 1 | 37.675 | 301.535 | 92 | 165 | 37.675 | 0 |
| RN | 1 | 8.115 | 58.164 | 167 | 60 | 8.115 | 0 |
| RO | 1 | 4.698 | 33.649 | 52 | 29 | 4.698 | 0 |
| RR | 1 | 1.519 | 10.588 | 15 | 9 | 1.519 | 0 |
| RS | 1 | 27.547 | 213.540 | 497 | 165 | 27.547 | 0 |
| SC | 1 | 17.326 | 136.979 | 295 | 100 | 17.326 | 0 |
| SE | 1 | 5.923 | 43.373 | 75 | 29 | 5.923 | 0 |
| SP | 1 | 103.656 | 848.063 | 645 | 393 | 103.656 | 0 |
| TO | 1 | 4.384 | 30.084 | 139 | 33 | 4.384 | 0 |
| ZZ | 1 | 1.309 | 12.035 | 145 | 1 | 1.309 | 0 |
| AC | 2 | 2.270 | 8.697 | 22 | 9 | 2.270 | 0 |
| AL | 2 | 7.101 | 27.419 | 102 | 42 | 7.101 | 0 |
| AM | 2 | 8.157 | 30.991 | 62 | 60 | 8.157 | 0 |
| AP | 2 | 1.914 | 6.973 | 16 | 11 | 1.914 | 0 |
| BA | 2 | 35.476 | 137.040 | 417 | 199 | 35.476 | 0 |
| CE | 2 | 23.765 | 91.087 | 184 | 109 | 23.765 | 0 |
| DF | 2 | 6.969 | 27.453 | 1 | 19 | 6.969 | 0 |
| ES | 2 | 9.844 | 38.829 | 78 | 50 | 9.844 | 0 |
| GO | 2 | 15.686 | 61.031 | 246 | 92 | 15.686 | 0 |
| MA | 2 | 18.093 | 66.190 | 217 | 105 | 18.093 | 0 |
| MG | 2 | 52.062 | 203.235 | 853 | 304 | 52.062 | 0 |
| MS | 2 | 7.106 | 26.734 | 79 | 49 | 7.106 | 0 |
| MT | 2 | 8.287 | 30.873 | 142 | 57 | 8.287 | 0 |
| PA | 2 | 20.827 | 76.003 | 144 | 101 | 20.827 | 0 |
| PB | 2 | 10.712 | 41.416 | 223 | 68 | 10.712 | 0 |
| PE | 2 | 21.418 | 83.243 | 185 | 122 | 21.418 | 0 |
| PI | 2 | 10.225 | 37.819 | 224 | 74 | 10.225 | 0 |
| PR | 2 | 27.142 | 105.761 | 399 | 186 | 27.142 | 0 |
| RJ | 2 | 37.675 | 147.600 | 92 | 165 | 37.675 | 0 |
| RN | 2 | 8.115 | 31.496 | 167 | 60 | 8.115 | 0 |
| RO | 2 | 4.698 | 17.265 | 52 | 29 | 4.698 | 0 |
| RR | 2 | 1.519 | 5.332 | 15 | 9 | 1.519 | 0 |
| RS | 2 | 27.547 | 106.789 | 497 | 165 | 27.547 | 0 |
| SC | 2 | 17.326 | 67.266 | 295 | 100 | 17.326 | 0 |
| SE | 2 | 5.923 | 22.732 | 75 | 29 | 5.923 | 0 |
| SP | 2 | 103.656 | 410.145 | 645 | 393 | 103.656 | 0 |
| TO | 2 | 4.384 | 16.709 | 139 | 33 | 4.384 | 0 |
| ZZ | 2 | 1.308 | 4.975 | 144 | 1 | 1.308 | 0 |

ZZ apresenta 1.309/1.308 seções e 145/144 códigos de município observados nos
turnos 1/2. São contagens das fontes concordantes; não foi determinada uma causa
para essa diferença nem presumida uma seção ausente. As demais abrangências
possuem a mesma quantidade de seções entre os turnos neste conjunto.

Reconciliação: **5.731.614 linhas correspondentes**,
0 diferenças, 0 exclusivas
da fonte seção, 0 exclusivas BWEB,
0 locais ambíguos e 0
erros matemáticos BWEB. O resumo exato por código/UF/turno e o detalhe limitado
acompanham a release. Ausência de fonte, seção ou votável permanece distinta de
diferença de votos/local, ambiguidade e matemática. Truncamento nunca é apresentado
como enumeração completa.

## Totais e integridade

| Turno | Seções/turno | Contabilizados | Nominais | Brancos | Nulos | Aptos disponíveis | Comparecimento disponível | Abstenção disponível | Seções sem totais BU completos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 499.206 | 125.275.835 | 119.306.034 | 2.300.798 | 3.669.003 | 158.745.007 | 125.275.835 | 33.469.172 | 0 |
| 2 | 499.205 | 128.236.074 | 124.082.273 | 1.430.496 | 2.723.305 | 158.744.977 | 128.236.074 | 30.508.903 | 0 |

As somas nacionais incluem ZZ explicitamente. Categorias sem linha permanecem
ausentes; totais disponíveis precisam ser lidos junto da contagem de indisponibilidade.
Não se presume igualdade de aptos entre turnos ou transferência individual de votos.

| Turno | Número | Nome publicado | Categoria | Votos, incluindo ZZ |
| --- | --- | --- | --- | ---: |
| 1 | 13 | LUIZ INÁCIO LULA DA SILVA | nominal | 53.879.538 |
| 1 | 14 | RENAN ANTONIO FERREIRA DOS SANTOS | nominal | 2.675.887 |
| 1 | 16 | HERTZ DA CONCEICAO DIAS | nominal | 43.103 |
| 1 | 21 | EDMILSON SILVA COSTA | nominal | 22.693 |
| 1 | 22 | FLAVIO NANTES BOLSONARO | nominal | 56.104.503 |
| 1 | 27 | CLARIANA ZACARKIM BARAO | nominal | 40.043 |
| 1 | 28 | LEONARDO ALVES DE ARAUJO | nominal | 5.246 |
| 1 | 29 | RUI COSTA PIMENTA | nominal | 15.024 |
| 1 | 30 | ROMEU ZEMA NETO | nominal | 326.488 |
| 1 | 35 | WILSON GRASSI JUNIOR | nominal | 16.881 |
| 1 | 55 | RONALDO RAMOS CAIADO | nominal | 2.605.148 |
| 1 | 70 | AUGUSTO JORGE CURY | nominal | 3.448.569 |
| 1 | 80 | SAMARA MARTINS DA SILVA FEITOSA | nominal | 122.911 |
| 1 | 95 | VOTO BRANCO | blank | 2.300.798 |
| 1 | 96 | VOTO NULO | null | 3.669.003 |
| 2 | 13 | LUIZ INÁCIO LULA DA SILVA | nominal | 64.256.232 |
| 2 | 22 | FLAVIO NANTES BOLSONARO | nominal | 59.826.041 |
| 2 | 95 | VOTO BRANCO | blank | 1.430.496 |
| 2 | 96 | VOTO NULO | null | 2.723.305 |

`PRAGMA integrity_check`: ok; foreign_key_check:
[]. Erros matemáticos: 0; agregados:
0; totais de seção/categoria:
0/0; vínculo de eleição:
0. Somas por categoria/seção e agregados estaduais foram
recalculados. Consultas municipais/zonais somam os registros conferidos, sem tabela
duplicada de votos; referências externas independentes de totais não foram obtidas.

O resumo [TSE_2026_NATIONAL_VALIDATION_SUMMARY.json](TSE_2026_NATIONAL_VALIDATION_SUMMARY.json)
contém candidatos por UF/turno, origens dos resultados, totais disponíveis, dimensões
de avaliação, artefatos e métricas. A conferência pós-importação foi somente leitura,
com temporários controlados e medidos separadamente. SC manteve as quantidades e
os votos da investigação M2: 17.326 seções por turno, 136.979/67.266 resultados e
4.648.159/4.762.303 votos. Os documentos históricos M2 não foram reescritos.

## Desempenho e armazenamento

Antes de qualquer processamento, o inventário local registrou
**444.714.639.360 bytes livres** e catalogou os artefatos anteriores.
Política da carga: 8 GiB adicionais, reserva mínima de 15 GiB. Projeção empírica:
6.584.854.964 bytes, arredondada para 7 GiB, sem aumentar
o orçamento. Baseou-se no piloto AC/2, contagem nacional de linhas, maior par SP/1,
fator 1,5, journal da base final e 272 MiB fixos; não era medição nacional nem quota.

| Medida da importação nacional | Valor |
| --- | ---: |
| Espaço livre ao iniciar | 443.895.771.136 bytes |
| Menor espaço livre observado | 441.016.598.528 bytes |
| Pico contabilizado conservador | 2.879.172.608 bytes |
| Pico de arquivos visíveis | 2.466.150.529 bytes |
| Pico na área de trabalho | 2.466.053.716 bytes |
| Pico de journals amostrado | 16.376.128 bytes |
| SQLite final | 935.424.000 bytes |
| Bytes lógicos removidos explicitamente | 4.064.248.602 |
| Arquivos removidos explicitamente | 171 |
| Temporários SQLite observados | 328 |
| Trabalho remanescente após sucesso | 0 bytes |
| CSVs descompactados lidos até EOF | 33.996.632.666 bytes |
| Tempo do importador antes do fechamento final | 4834.033 s |
| Parsing / consolidação | 3564.457 / 1211.581 s |
| Validação inicial | 38.2 s |
| Comando completo com revalidação do wrapper | 4914.729 s |
| Pico RSS do processo | 87.543.808 bytes |

Tamanhos são comprimentos lógicos; o delta do volume inclui atividade externa e
pode inflar ou mascarar parte do consumo. Amostragem de 100 ms, callbacks SQL/lotes
e margem de até 64 MiB auxiliam a interrupção antes dos limites; **não há quota
rígida do SO nem garantia absoluta de pico**. TEMP/TMP/SQLITE_TMPDIR foram alterados
somente no processo e restaurados. SQLite `etilqs_*` foi observado em `tmp/` e
removido pelo próprio SQLite. Bytes recuperados explícitos não contam novamente
essa liberação. Bytes comprimidos efetivamente lidos pelo SO não foram medidos;
probes de cabeçalho, PDFs e índices não entram na soma dos bytes CSV.

Não foi criado SQLite comprimido para uma medição opcional. O registro `.runs/`
traz métricas finais e arquivos/identidades; validation.json registra o retrato
anterior à promoção/limpeza. Máximos por arquivo não são picos simultâneos e os bytes
do próprio registro mudam ao gravá-lo. O inventário final local mede a saída real,
inclusive ponteiro e registros, separadamente dessa fotografia do guard.

Piloto AC/2: 2.270 seções/8.697 resultados, 22 municípios e 9 códigos de zona
(23 pares município/zona), sem divergências; SQLite 1.699.840 bytes, 64,321 s,
pico contabilizado 130.383.872 bytes, área de trabalho 11.649.231. Regressão SC:
SQLite 32.559.104 bytes, 89,595 s, pico contabilizado 222.257.152 bytes. As cópias
temporárias dos dois testes foram descartadas com conferência de identidade;
12 arquivos/34.350.120 bytes, além dos intermediários já limpos pelo motor.

## Artefatos anteriores preservados e prontidão

| Conjunto anterior, preservado | Bytes lógicos | Situação |
| --- | ---: | --- |
| `data/processed/sc-2026/` | 812529200 | saída M2 com release/intermediários |
| `data/processed/sc-2026-review/` | 580681064 | saída da revisão M2 |
| `.local/pytest*` anteriores | 239714182 | fixtures e derivados anteriores |

Potencial bruto: 1.632.924.446 bytes. Isso inclui releases válidas/ponteiros ativos;
não é classificação automática de lixo. Nenhum arquivo anterior ou backup original
foi apagado. `.local/m31-storage-before.json` lista candidatos, propósito, validade,
checkpoints e necessidade de autorização explícita. Somente áreas de teste desta
missão, ausentes no inventário inicial, foram limpas, com recibos em `.local/`.
Um diagnóstico pequeno do preflight inicialmente recusado permanece por política
de retenção; não há SQLite de staging/checkpoint remanescente da carga concluída.

Prontidão pública: **not_ready**. Motivos: `source_hashes_reused_from_local_cache, operator_trusted_hashes_incomplete`.
SHA convencional não é assinatura; `trusted` é declaração do operador, com
autenticação de origem/assinatura `not_performed`. A falta de checksum nacional
não impediu análise local, nem foi resolvida por relaxamento da política pública.

## Código, testes e limites

Carga produzida pelo núcleo no commit `0760cefc53d0406672afaf83c7fa8bdc99e3f8b5`,
Python 3.12.10/SQLite 3.49.1/Windows; versão 0.3.1, schema 1, assessment 2.
O reforço posterior de caminhos relativos a drive não altera a interpretação
eleitoral desta carga. Foram executados Ruff, pytest sintético, integração SC e
validação nacional independente. Resultados finais e SHAs no
[relatório de conclusão](M3_1_COMPLETION_REPORT.md).

O CI disponível da main
[`40925676557`](https://github.com/UrnaLivre/votoaberto/actions/runs/40925676557)
passou em Windows/Linux, Python 3.11/3.12, no SHA `d27712b`; não é CI desta branch.
Não houve push, abertura de PR ou merge. Flutter permanece com mock.

Limites: sem inventário externo exaustivo de seções ou autenticação criptográfica
da origem; sem comparação dos backups antigos; nomes e valores são os publicados
nos arquivos fornecidos. BWEBs em unidades separadas com UF/turno sobreposto são
recusados; múltiplos contextos dentro da unidade são identificados e não somados.
Retomada dentro de CSV grande, redução de I/O de índices/compactação e quotas do
SO são melhorias futuras. Nenhuma concordância estatística/matemática certifica
as demais etapas do processo eleitoral.
