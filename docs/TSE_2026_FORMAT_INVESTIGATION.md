# Investigação dos arquivos TSE 2026 e primeira importação de SC

Data da investigação: **29/10/2026**. Atribuição: Tribunal Superior Eleitoral.
Este relatório descreve os bytes locais fornecidos e as comparações executadas;
não é certificação da eleição. Flutter M1 permanece com seu mock. Originais
ficaram imutáveis, em diretório externo informado pelo operador. Nenhum ZIP, CSV
grande ou banco real faz parte do Git.

## Inventário observado

Foram encontrados três ZIPs e dois auxiliares SHA-512, totalizando 399.556.604
bytes de ZIP, em vez de assumir o volume aproximado da especificação inicial.
Cada ZIP tem um CSV e um PDF na raiz; não há BU binário nesta amostra. Índices
sem duplicatas, criptografia, aninhamento ou caminhos perigosos. Leitura amostral
precedeu os parsers; processamento posterior percorreu os membros até EOF e
conferiu os CRCs. Não houve extração integral de CSVs: somente os pequenos
leiautes PDF foram copiados para investigação local e lidos com pypdf.

| Nome original | Bytes ZIP | SHA-256 calculado |
| --- | ---: | --- |
| `bweb_1t_SC_051020261403.zip` | 153178332 | `af9e03f17cefe6f4a0be48093a920974d61feb9b07d3ea69b1b84fb7c9a7599f` |
| `bweb_2t_SC_261020260742.zip` | 4487185 | `6f169b88a07858e920b3c9e974f3ae5238f36dfe6e6d138a1758764c5b4de697` |
| `votacao_secao_2026_BR.zip` | 241891087 | `c928321f63f2d095706fca73d4607c048d2ada23bda6876455d6911aaf1bc9c1` |

| ZIP | Membro | Descompactado declarado | Compactado declarado | CRC32 |
| --- | --- | ---: | ---: | --- |
| `bweb_1t_SC_051020261403.zip` | `bweb_1t_SC_051020261403.csv` | 978668939 | 152986410 | `a9dc5e6e` |
| `bweb_1t_SC_051020261403.zip` | `_leiame-boletimurnaweb.pdf` | 207085 | 191642 | `6d50843c` |
| `bweb_2t_SC_261020260742.zip` | `bweb_2t_SC_261020260742.csv` | 29698108 | 4295263 | `3ace29fd` |
| `bweb_2t_SC_261020260742.zip` | `_leiame-boletimurnaweb.pdf` | 207085 | 191642 | `6d50843c` |
| `votacao_secao_2026_BR.zip` | `votacao_secao_2026_BR.csv` | 1578545088 | 241710212 | `1f09ce4b` |
| `votacao_secao_2026_BR.zip` | `leiame.pdf` | 192420 | 180631 | `7d7e4419` |

Os auxiliares locais têm 158 bytes cada e usam uma linha GNU de digest, dois
espaços e nome do ZIP, terminada por LF. O rótulo do portal é “Hash SHA2”; o
arquivo `.sha512` e seus 128 caracteres hexadecimais identificam SHA-512.

## Referências efetivamente consultadas

- [Catálogo BWEB 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna).
- [Catálogo de resultados 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026).
- [Recurso nacional presidencial](https://dadosabertos.tse.jus.br/dataset/resultados-2026/resource/01ea4ccd-f443-469c-9f29-c69ff97f7d4c).
- Metadados dos recursos consultados também pela API CKAN `package_show` dos
  dois catálogos, em 29/10/2026; URLs precisas preservadas na configuração e resumo JSON.

Os catálogos indicam Creative Commons Attribution/Atribuição. Preservamos esse
rótulo, sem inventar uma versão específica da licença; MIT licencia o código.
Não houve download dos ZIPs durante esta missão. Foram consultadas apenas páginas,
metadados e as duas pequenas referências de hash abaixo:

- [bweb_1t_SC_051020261403.zip: referência SHA-512](https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/buweb/bweb_1t_SC_051020261403.zip.sha512):
  `618c1cacf80bc2964d3bb5e6274ba3e2adeed853077083bc01004e5110e79615868cf3c39b490e283c181c716275d4473da35d11f407111f4170fc91a8a93db7`. **Coincide** com o SHA-512 calculado e com o auxiliar local.
- [bweb_2t_SC_261020260742.zip: referência SHA-512](https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/buweb/bweb_2t_SC_261020260742.zip.sha512):
  `01b1e9638654fa6914ad4d8a9001de33cb4fc5386d280ccdea7576d7c993c04e9162075db0a1fed8f571e87ce5349151e6a44bc4d5300b3e828a0123c6b90c8e`. **Coincide** com o SHA-512 calculado e com o auxiliar local.

O cliente web não leu os auxiliares por causa do Content-Type application/zip;
a consulta HTTPS direta retornou 158 bytes de texto por referência, comparados
com os digests locais. Origem identificada no catálogo oficial, não inferida
apenas pelo nome. Nenhuma referência oficial suficiente para o ZIP nacional foi
encontrada nas consultas realizadas: seu SHA-256 é catalogação própria e seu
estado permanece **unverified**. O derivado combinado também é unverified quanto
às referências de origem, mesmo tendo passado nas verificações matemáticas.
Correspondência de hash é comparação de bytes sob confiança na referência;
não é assinatura digital, prova de autenticidade eleitoral ou ausência de fraude.

## Formatos, campos e tipos

Os dois leiautes BWEB são iguais: **45 colunas**. Votação por seção tem **26
colunas**. Relação completa e exata: [schemas.json](../pipelines/tse_importer/schemas.json).
Os PDFs internos declaram Latin-1; amostras e leitura integral são compatíveis.
Separador `;`, cabeçalho entre aspas e linhas com texto entre aspas. Apesar do
leiaute dizer que inclusive números são entre aspas, há números sem aspas nos
CSVs efetivos; csv.reader aceita ambas as formas. Não assumir UTF-8/CSV por nome.

| Grupo | Campos identificados e interpretação adotada |
| --- | --- |
| Geração | DT_GERACAO, HH_GERACAO; strings originais de geração da fonte |
| Eleição | ANO_ELEICAO, NR_TURNO; CD_ELEICAO textual, único por eleição/turno; CD_TIPO_ELEICAO/NM_TIPO_ELEICAO e DS_ELEICAO |
| Pleito BWEB | CD_PLEITO, DT_PLEITO; adicionais originais, sem confundir pleito com eleição |
| Abrangência seção | TP_ABRANGENCIA=F, SG_UE=BR, NM_UE; DT_ELEICAO |
| Localidade | SG_UF, CD_MUNICIPIO, NM_MUNICIPIO, NR_ZONA, NR_SECAO, NR_LOCAL_VOTACAO; códigos como texto, município TSE e não IBGE |
| Cargo | BWEB: CD_CARGO_PERGUNTA/DS_CARGO_PERGUNTA; seção: CD_CARGO/DS_CARGO |
| Votável | NR_VOTAVEL, NM_VOTAVEL, QT_VOTOS; seção acrescenta SQ_CANDIDATO, distinto do número de campanha |
| Totais BWEB | QT_APTOS, QT_COMPARECIMENTO, QT_ABSTENCOES repetidos por votável; deduplicar por contexto antes de somar |
| Tipos BWEB | CD_TIPO_URNA/DS_TIPO_URNA e CD_TIPO_VOTAVEL/DS_TIPO_VOTAVEL |
| Contexto BWEB | NR_URNA_EFETIVADA, códigos de carga/flashcard/data de carga, DT_BU_RECEBIDO, DT_EMISSAO_BU; não equivalem a um identificador físico criado pelo projeto |
| Particularidades | DS_CARGO_PERGUNTA_SECAO; DS_SECOES_AGREGADAS, lista separada por /; abertura/encerramento, biometria, junta/turma |
| Não necessários ao público | Partido e campos técnicos BWEB; nome/endereço do local de votação do CSV nacional; permanecem na fonte original |

Sentinelas documentadas: #NULO/-1 para ausência, #NE/-3 para informação não
registrada; arquivos usam também a forma com # final. Preservar distinção e não
converter em zero. Contagens não negativas são inteiros; códigos com zeros à
esquerda são strings. Há horários em formatos diferentes entre os formatos;
os valores de data são preservados, sem supor timezone em campos não documentados.

Uma inconsistência do próprio leiaute BWEB merece registro: a descrição de
CD_MUNICIPIO/NM_MUNICIPIO mistura conceitos de abrangência/unidade eleitoral,
sugerindo BR/Brasil no âmbito federal. Os registros presidenciais observados têm
códigos municipais locais de SC, coincidentes com a votação por seção. O motor
preserva os valores efetivos; não os substitui por BR.

## Diferenças reais entre fontes e turnos

- BWEB define ordinária como CD_TIPO_ELEICAO=0; seção define como 2. Não usar uma
  regra universal para esse campo. Essa diferença está nos leiautes e nos dados.
- CD_ELEICAO presidencial: 6257 no primeiro turno e 6258 no segundo; BWEB traz
  CD_PLEITO 3220/3221 e datas 04/10/2026 e 25/10/2026. Não juntar turnos só pelo ano.
- BWEB 1º turno gerado 05/10/2026 14:03:43, contém cinco cargos; BWEB 2º turno
  gerado 26/10/2026 07:42:38, contém apenas presidente em SC. CSV nacional gerado
  26/10/2026 12:07:25, contém presidente nos dois turnos, 27 UFs e ZZ.
- BWEB 1º turno: 2.118.318 linhas totais, das quais 136.979 presidenciais;
  governador 124.002, senador 192.681, deputado federal 779.776 e estadual 884.880.
  BWEB 2º turno: 67.266 linhas, todas presidenciais. Encontrar cargos não significa
  que o motor tenha regras de importação implementadas para eles.
- CSV nacional: 5.731.614 registros; o nome BR corresponde aqui à cobertura
  presidencial nacional, não a todos os cargos. Sua cobertura foi percorrida
  integralmente; somente SC foi exportada/conferida nesta missão.
- BWEB não traz SQ_CANDIDATO e usa nomes de urna/curtos, enquanto votação usa
  outros nomes: por exemplo, ZEMA/ROMEU ZEMA NETO e LULA/LUIZ INÁCIO LULA DA SILVA.
  O relacionamento confirmado usa número do votável e contexto eleitoral.
- Há 13 números nominais no primeiro turno e dois no segundo nesta amostra.

## Identificação presidencial e chaves de relacionamento

Código 1 e descrição Presidente em ambos os formatos; BWEB tipos nominais 1,
brancos 2 (votável 95), nulos 3 (96). Todos os BWEB presidenciais importados são
tipo de urna 1, apurada. Não foram observados registros presidenciais 97 em SC.
97 e outras situações de BU seguem explicitamente não suportados; não atribuir
significado definitivo a dados ainda não encontrados/validados.

A chave tabular `(CD_ELEICAO, SG_UF, CD_MUNICIPIO, NR_ZONA, NR_SECAO, NR_VOTAVEL)`
relacionou todos os registros presidenciais de SC entre as duas fontes, com
unicidade observada e igualdade de NR_LOCAL_VOTACAO. Para BWEB, conferir também
contexto de urna/carga/emissão/recepção/agregação antes de permitir comparação.
Um contexto único foi encontrado por chave de seção/eleição na amostra. Nenhuma
correspondência universal seção/BU/equipamento físico foi inferida.

Foram observados **226 grupos com DS_SECOES_AGREGADAS preenchido em cada turno**.
Exemplo de ambos: município 80020, zona 65, seção 110, agregada 112. Não expandimos
esses grupos em novas linhas nem duplicamos votos. As 17.326 seções abaixo são
chaves de seção principal presentes nos resultados, não contagem de todas as
seções cadastrais ou de equipamentos físicos. Os conjuntos de chaves locais
coincidem entre turnos; isso não demonstra permanência de equipamento.

## Primeira importação real e conferências executadas

Foram exportados exclusivamente presidente/SC, em ambos os turnos, preferindo
votação por seção como fonte de resultados. BWEB forneceu conferência e totais
disponíveis. Base pública sem BUs completos ou logs. Dados brutos foram lidos em
streams sequenciais; checkpoints guardam somente o recorte presidencial escolhido.

| Métrica | Primeiro turno | Segundo turno |
| --- | ---: | ---: |
| Código de eleição | 6257 | 6258 |
| Chaves de seção | 17.326 | 17.326 |
| Registros presidenciais por fonte | 136.979 | 67.266 |
| Votos nominais somados | 4.501.081 | 4.638.385 |
| Brancos | 69.007 | 48.674 |
| Nulos | 78.071 | 75.244 |
| Contabilizados / comparecimento BWEB | 4.648.159 | 4.762.303 |
| Aptos BWEB, uma vez por contexto | 5.734.651 | 5.734.687 |
| Abstenções BWEB | 1.086.492 | 972.384 |
| Seções sem linha de branco | 720 | 1.387 |
| Seções sem linha de nulo | 579 | 651 |

295 municípios e 100 números de zona em SC. Os aptos somados diferem em **36**
entre os turnos; registramos a diferença sem inferir causa. Ausência de linha de
branco/nulo permanece NULL na projeção por seção, embora o somatório das linhas
presentes esteja acima; não inventamos uma linha de zero. A identidade matemática
foi conferida por seção/contexto, além dos agregados.

Totais por número e nome **conforme o CSV fornecido**, sem validação externa do
resultado eleitoral agregado:

| Turno | Número | Nome na votação por seção | Votos |
| --- | --- | --- | ---: |
| 1 | 13 | LUIZ INÁCIO LULA DA SILVA | 1127168 |
| 1 | 14 | RENAN ANTONIO FERREIRA DOS SANTOS | 132795 |
| 1 | 16 | HERTZ DA CONCEICAO DIAS | 1503 |
| 1 | 21 | EDMILSON SILVA COSTA | 828 |
| 1 | 22 | FLAVIO NANTES BOLSONARO | 3000020 |
| 1 | 27 | CLARIANA ZACARKIM BARAO | 1429 |
| 1 | 28 | LEONARDO ALVES DE ARAUJO | 184 |
| 1 | 29 | RUI COSTA PIMENTA | 643 |
| 1 | 30 | ROMEU ZEMA NETO | 16718 |
| 1 | 35 | WILSON GRASSI JUNIOR | 560 |
| 1 | 55 | RONALDO RAMOS CAIADO | 79911 |
| 1 | 70 | AUGUSTO JORGE CURY | 134273 |
| 1 | 80 | SAMARA MARTINS DA SILVA FEITOSA | 5049 |
| 2 | 13 | LUIZ INÁCIO LULA DA SILVA | 1418314 |
| 2 | 22 | FLAVIO NANTES BOLSONARO | 3220071 |

Conferências: **204.245 linhas coincidentes**, zero diferenças de votos/local,
zero linhas exclusivas de fonte dentro do recorte SC, zero contextos ambíguos,
zero duplicatas da chave no contexto, zero falhas nas identidades matemáticas.
34.652 pares seção/turno recebem comparison=matched. SQLite integrity_check=ok,
foreign_key_check vazio, somas por seção/categoria/agregações e vínculos
eleitorais dos candidatos passaram. Essas conclusões se restringem às operações
executadas. Não comparamos com totalização independente da web, RDV, log, BU
binário/impresso, assinatura digital ou todos os eventos de substituição.

## Execução reproduzível e desempenho

Instalação/semântica/schema: [DATA_ARCHITECTURE](DATA_ARCHITECTURE.md).
A [configuração de referência](../config/sc-2026-reference.json) contém caminhos
relativos dos três arquivos, digests oficiais efetivamente consultados e
metadados de origem. A estrutura de subpastas precisa corresponder à inventariada;
se reorganizar uma cópia local, ajustar os caminhos relativos da configuração.
Os originais desta investigação não foram reorganizados.

```powershell
votoaberto-auditor import --config config/sc-2026-reference.json --input "D:\MODELOS_TSE"
votoaberto-auditor validate --dataset data/processed/sc-2026
$env:TSE_REAL_INPUT = "D:\MODELOS_TSE"
$env:TSE_REAL_CONFIG = "$PWD/config/sc-2026-reference.json"
python -m pytest -q -m official
```

O teste oficial é opt-in e verifica contagens e valores concretos de SC. CI
utiliza apenas fixtures pequenos e um volume sintético gerado de 20.000 linhas.
Resultado final: **46 testes passaram**, incluindo a integração oficial opt-in;
Ruff format/check e git diff --check passaram. Na execução sem fontes oficiais,
o teste real é pulado e os 45 sintéticos continuam independentes desses arquivos.
Instalação limpa do wheel e entrada CLI foram verificadas localmente no Windows
com Python 3.12.10 e SQLite 3.49.1. Workflow Ubuntu/Windows, Python 3.11/3.12, foi preparado;
**não foi executado um ambiente Linux nem o GitHub Actions nesta missão**.

Medição da execução final registrada: **60.841 s**, SQLite **30089216 bytes** (28.70 MiB), pico **80601088 bytes** (76.87 MiB), método Windows PeakWorkingSetSize. Execução dentro do pytest, incluindo seu runtime; 0 checkpoints reutilizados. Não confundir pico de processo com memória exclusiva do parser. Inclui inventário, hashes das fontes, leitura completa dos três CSVs (7.917.198 linhas), filtragem, consolidação e validação SQLite; medido antes do manifesto/promoção final. Não é benchmark nacional de exportação.

Release local: `16048b78c3065046c7464fcd`; SHA-256 SQLite: `371dbe72ef0bcf2ff156191a8733d905307d63b9285c49d77e9645a0a446a534`. O manifesto completo e relatórios estão sob `data/processed/sc-2026/releases/16048b78c3065046c7464fcd/`, ignorados pelo Git. [Resumo pequeno versionado](tse_2026_reference_summary.json) preserva inventário, métricas e contagens sem dados volumosos.

## Limitações e próximos passos

1. SC não representa todas as situações de outras UFs/ZZ. Só presidente e leiautes
   observados estão habilitados; outros cargos e casos excepcionais são recusados.
2. Presença nacional/ZZ foi confirmada no CSV lido, mas não fizemos importação
   nacional nem conferência BWEB fora de SC. Para expandir, fornecer BWEB por UF/turno,
   referências e metadados, testar schemas/coberturas e medir execução completa.
3. Testar padding, localidades do exterior, trânsito, agregações divergentes,
   contextos concorrentes, seções não instaladas/anuladas, alterações de schema e
   arquivo 97 antes de criar regras. Não inferir equipamento por número de seção.
4. Fonte nacional sem checksum oficial suficiente: manter unverified; procurar
   referência publicada adicional, sem tratar SHA-256 próprio como referência oficial.
5. Arquivos podem refletir momentos diferentes de publicação. Não inventar causas
   para divergências futuras. Manter versões separadas e fonte/linha dos registros.
6. Não é validação independente do TSE: ambos os datasets vêm do mesmo órgão.
   Igualdade tabular não certifica eleição; discrepância também não prova fraude.
7. Futuro adaptador Flutter/API exige revisão de disponibilidade, granularidade,
   cobertura/ZZ e denominadores. Esta missão não substitui o mock.
8. O importador limita streams/índice/cache, sem quota rígida de RSS/disco;
   interrupção abrupta reinicia membro incompleto, não retoma no meio do DEFLATE.

Branch de trabalho: `feat/m2-tse-importer`, criada a partir de `37c066b`.
Commit de implementação/testes/CI: `32dbb02`. A documentação e os metadados
investigativos são consolidados em commit subsequente na mesma branch.
Sem merge, push, PR ou publicação remota. Commits finais constam no relatório
de entrega e no histórico da branch. As restrições de originais e dados grandes
são mantidas por leitura dos arquivos externos e exclusões no .gitignore.
