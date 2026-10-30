# M4 — MVP municipal embarcado: entrega e validação local

Execução local em Windows, 29–30/10/2026. Branch
`feat/m4-embedded-municipal-results`, criada da main limpa e atualizada
`e854184238b2b37d00c63526878770baf2cdfa83` após fetch. Nenhuma branch auxiliar,
reescrita de histórico, publicação, push, PR ou merge. O remoto só tinha main
na conferência inicial. Não houve conflitos de merge nesta missão.

## Entrega

Data Engine/Auditor exportam JSONs municipais determinísticos a partir da release
SQLite validada, exclusivamente leitura. Totais de seção e candidatos têm
agregações separadas e comparação SQL independente antes da promoção. Foram
acrescentados manifesto, validação JSON autônoma, instalação controlada de assets
e wrapper de build que impede ausência/mistura de dados e fallback fictício.

O Flutter evolui o M1: repositório `AssetBundle`, cache LRU de três abrangências,
carregamento municipal por UF, proteção contra respostas obsoletas, candidatos
por turno, ausências explícitas, Brasil doméstico separado do total com ZZ,
busca municipal sem acento, URLs e gráficos adaptados. Mock, mapa vetorial,
tema, navegação por UF e testes anteriores são preservados. Sem API/backend,
SQLite no cliente, BUs integrais ou novo mapa municipal.

[Operação e contrato](EMBEDDED_DATA_MVP.md), [ADR 0004](adr/0004-embedded-municipal-data.md).
Dados completos permanecem locais/ignorados. O pequeno
[resumo de validação](M4_VALIDATION_SUMMARY.json) versiona somente métricas,
totais agregados e hashes, incluindo todos os arquivos e totais por abrangência.

## Fonte e identidade do derivado

| Artefato | Valor |
| --- | --- |
| Release SQLite M3.1 | `6305f74561d4687a23bd3054` |
| SQLite original | 935.424.000 bytes |
| SHA-256 SQLite | `c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4` |
| Release JSON | `e4e9c9cb5189ab5d4e124bfc` |
| SHA-256 manifesto JSON | `c4dcddacb8092ff1dfffb35b07b739dbf360232e701e080087f52a4a09e20637` |
| Contrato | JSON schema 1; regras `municipal-1`; SQLite schema 1 |
| Exportador que gerou este pacote | commit `986d5c71e1b772dff74c3224cd98aa60757149be` |

O pacote foi gerado uma vez em `data/processed/embedded-presidential-2026/` e
instalado em `apps/votoaberto_flutter/assets/data/real/`. O exportador verificou
hash e validação da release, agregou e comparou todo o conteúdo serializado com
o SQLite. Nenhum dos 57 ZIPs foi reprocessado ou baixado; não houve cópia completa
do banco. Identidade/tamanho/mtime/inode/dispositivo do SQLite e tamanhos das três
áreas anteriores foram comparados antes/depois. O hash inicial foi conferido pelo
validador da release; a conferência final de preservação usa a identidade do arquivo.

Correções posteriores reforçaram validação da fonte, mutex de promoção e estado
do retorno de validação; não alteraram consultas, agrupamentos ou valores desta
mini-base. Não se reexportou só para trocar o hash de código. Uma exportação com
regras finais terá outra identidade de versão, mesmo com totais iguais.

## Cobertura e matemática observadas

Foram encontrados **5.571 códigos municipais domésticos** (incluindo a unidade
TSE do DF) e **145 códigos de localidades ZZ** na união dos turnos. Não são
contagens obtidas de catálogo IBGE nem declaração de cobertura eleitoral exaustiva.
Primeiro turno: 5.571 domésticos + 145 ZZ = 5.716 registros municipais.
Segundo: 5.571 + 144 = 5.715. Total: **11.431 registros município/turno**.
As 28 abrangências possuem ambos os turnos; uma localidade ZZ não possui resultado
no segundo. Não foi criada linha artificial para completar a união.

Catálogo nominal: **13 candidatos no primeiro turno e 2 no segundo**; brancos e
nulos são categorias separadas. IDs de eleição `6257` e `6258` e códigos TSE
permanecem textuais. Municípios homônimos são separados por UF/código.

| Total com exterior | 1º turno | 2º turno |
| --- | ---: | ---: |
| Votos válidos | 119.306.034 | 124.082.273 |
| Brancos publicados | 2.300.798 | 1.430.496 |
| Nulos publicados | 3.669.003 | 2.723.305 |
| Contabilizados / comparecimento | 125.275.835 | 128.236.074 |
| Aptos | 158.745.007 | 158.744.977 |
| Abstenção | 33.469.172 | 30.508.903 |
| Votos do número 13 | 53.879.538 | 64.256.232 |
| Votos do número 22 | 56.104.503 | 59.826.041 |

| Total doméstico, sem ZZ | 1º turno | 2º turno |
| --- | ---: | ---: |
| Válidos | 118.975.029 | 123.710.622 |
| Contabilizados / comparecimento | 124.934.069 | 127.854.631 |
| Aptos | 157.828.968 | 157.828.819 |
| Abstenção | 32.894.899 | 29.974.188 |

Totais nacionais coincidem com M3.1. A comparação municipal/candidato/categoria,
UF direta por SQL e somas nacional/doméstico retornou **zero diferenças**.
Integridade física, matemática e referencial de origem passaram. Ausência de
linhas para categorias não é convertida em zero: `available_sections` preserva
cobertura por campo. A UI marca somas parciais de brancos/nulos e não calcula
comparação de totais completos nesses casos, ainda que as somas publicadas
sejam compatíveis com o total contabilizado.

O comando posterior `validate-embedded` também passou em hashes/schema/hierarquia,
com `sqlite_comparison: not_repeated`. Essa verificação adicional não é apresentada
como uma segunda execução da comparação SQL.

## Volume e recursos medidos

32 JSONs: manifesto, validação, Brasil, UFs e 28 arquivos municipais.
**4.475.495 bytes** no pacote completo; 53.178 bytes no carregamento inicial de
manifesto/Brasil/UFs. Maior arquivo: MG, 659.492 bytes; SP 506.260, RS 377.891,
SC 226.900, AC 17.393 e ZZ 103.887. Tamanhos e SHA-256 de todos os arquivos
estão no resumo JSON vinculado acima.

Representação com metadados de candidatos repetidos: 11.130.583 bytes;
normalizada: 4.448.955 bytes para os arquivos de dados, excluindo manifesto/validação.
A comparação mediu serialização em memória; não guardou uma segunda mini-base.

Exportação: **508,489 s**, pico de memória **88.158.208 bytes** (Windows
`PeakWorkingSetSize`, processo exportador). Disco: pico conservador por variação
do volume de 333.283.328 bytes; pico visível de 244.286.064 e trabalho de
244.284.368. Foram observados 19 temporários SQLite, liberados pelo SQLite;
journals 0, trabalho remanescente 0. Reserva mínima observada 440.124.907.520 bytes.
O pico por volume inclui outras atividades do sistema; não equivale a medição
exclusiva de I/O. Recibo da exportação registrou 4.499.441 bytes próprios retidos,
incluindo metadados/ledger. Inventário final exato fica no resumo JSON.

## Verificações e builds

Ruff format/check, pytest, `pip check`, CLI, Flutter format/analyze/test e smokes
reais foram executados localmente; resultados finais e commits são registrados
no fechamento abaixo. Workflows foram atualizados para fixtures e builds nas
três plataformas; não foram executados remotamente porque não houve push.

Teste de integração nativo Windows abriu a aplicação compilada com `rootBundle`
real, conferiu Brasil nos dois turnos, SP, São Paulo e Adamantina, com
`HttpOverrides` recusando criação de clientes HTTP. Resultado: **1 teste passou,
zero tentativas de HTTP da aplicação**. Isso não altera a rede do computador nem
representa teste de firewall. Tempos debug medidos no harness:

| Operação | ms |
| --- | ---: |
| `app.main()` até quadro nacional estabilizado | 1.184,433 |
| Alternar turno nacional | 532,461 |
| Selecionar SP | 937,577 |
| Digitar busca municipal | 396,896 |
| Selecionar São Paulo | 111,674 |

Esses valores incluem pumps/estabilização do teste debug. Não medem partida fria
do processo pelo sistema operacional, distribuição estatística, dispositivo
Android ou desempenho de release. Smoke adicional de arquivos reais verifica
Brasil, SP, AC, RS, SC e ZZ, ambos os turnos, lazy loading e duas localidades por
abrangência. Tempos de decodificação/busca são guardados localmente em `.local/`.

Builds finais: Web release **109,0 s**, Windows release **79,1 s**, APK debug
**236,4 s**. Os três pacotes foram inspecionados
por arquivo: 32 JSONs reais, hashes idênticos à mini-base e nenhum JSON sintético.
Tamanho de diretório de build inclui runtime/fontes/cartografia; tamanho de assets
reais é informado separadamente. APK debug não é pacote de produção assinado.

Inspeção visual do build Web real em 1366×768, 390×844 e 768×1024: mapa/UF,
busca sem acento, seleção por Enter, URL municipal, troca de turno, comparação e
tema escuro. Sem overflow observado nesses recortes. Capturas locais em
`.local/qa/m4-*.png`, ignoradas. Não houve avaliação com usuários/leitor de tela
externo nem teste em celular Android físico. Testes semânticos/teclado são básicos.

O SDK local ainda assume `offlineFirst` quando a estratégia não é informada.
A inspeção detectou isso e o wrapper passou a usar `--pwa-strategy=none`.
O bootstrap final não registra esse worker; a opção depreciada deve ser revista
ao atualizar Flutter. Não habilitamos PWA experimental.
O teste Web usa host estático local de QA, não backend do produto. Primeira visita
exige conexão ao host; offline após reiniciar o navegador **não é garantido**.

## Limites e prontidão

`public_readiness` continua **`not_ready`** por
`source_hashes_reused_from_local_cache` e `operator_trusted_hashes_incomplete`;
autenticação da origem não foi realizada. SHA-256/SHA-512 não são assinaturas
digitais e confiança de referência é atribuída pelo operador. M4 não alterou as
conclusões históricas de SC/M3.1 nem comparou backups dos ZIPs antigos/novos.

Pronto para revisão de código e testes locais do MVP. Publicação pública depende
de revisão de proveniência, termos de distribuição e prontidão da base. API por
zona/seção, Android físico, PWA entre sessões e métricas de partida fria são
trabalhos posteriores. Nada aqui certifica integridade de todo o processo eleitoral.

## Fechamento verificável

| Verificação | Resultado local |
| --- | --- |
| Ruff format/check, 27 arquivos Python | Passou |
| pytest completo | 113 passaram; 2 integrações oficiais opcionais puladas; 435,95 s |
| Regressão após opção explícita de service worker | 2 testes do wrapper passaram; 1,78 s |
| `pip check`, CLI help e `validate-embedded` | Passaram |
| Dart format e Flutter analyze | Passaram; análise sem issues |
| Flutter test com coverage | 57 passaram; 7 testes reais opcionais pulados |
| Execução explícita desses 7 testes reais | 7 passaram, 8 s |
| Integração nativa Windows, HTTP bloqueado na aplicação | 1 passou; 0 tentativas HTTP |
| `git diff --check` | Passou |
| Fixtures após filtros de checkout Git/Windows | 31 artefatos conferidos; zero diferenças; LF fixado em `.gitattributes` |

Os skips Python preservam as integrações oficiais anteriores e não representam
reimportação M3.1 nesta missão. O smoke real Flutter foi executado separadamente,
portanto seus skips na suíte fixture não escondem a validação real.

| Pacote final local | Bytes do build | JSONs reais (bytes) |
| --- | ---: | ---: |
| Web release, diretório | 47.804.004 | 4.475.495 |
| Windows release, diretório | 33.890.390 | 4.475.495 |
| APK debug, arquivo | 171.151.665 | 4.475.495 descomprimidos; 1.042.490 comprimidos |

SHA-256 do APK debug:
`07df7f14dd58bab8e64c9c09c041133e89e9a4b24073072be59ba36b7d0e83e5`.
Executável: `apps/votoaberto_flutter/build/windows/x64/runner/Release/votoaberto.exe`.
Distribuir Windows exigiria a pasta Release completa, não apenas o `.exe`;
essa distribuição não foi feita. Não havia dispositivo Android físico/emulador
utilizado nesta validação; APK é evidência de compilação, não de teste em hardware.

Saída canônica final: **4.499.541 bytes**, incluindo ponteiro e recibo;
instalação nos assets: **4.475.495 bytes**. As áreas anteriores mantiveram
936.423.406 bytes (nacional), 812.529.200 (SC) e 580.681.064 (SC review).
O SQLite preservou sua identidade e não sofreu escrita. Foram removidos
**56.854.759 bytes lógicos** de 13 diretórios pytest criados nesta missão,
arquivo por arquivo com verificação de identidade e recusa de links/reparse.
Nenhum arquivo desconhecido, release anterior ou insumo oficial foi removido.
Capturas, logs e recibos locais foram conservados como evidência; o resumo JSON
registra o inventário de pacotes e a reserva livre no momento da medição.

Correção incidental validada: um teste revelou corrida entre a varredura de disco
e o rename de staging. A promoção/retorno ao staging agora compartilha o mutex
do monitor e diretórios desaparecidos entre walk/stat recebem o tratamento já
usado para arquivos. Regressão específica e suíte completa passaram; nenhuma
regra eleitoral de M3.1 foi alterada. Outro ajuste corrigiu o estado retornado
por `validate_embedded` de `pending` para `passed` após verificação bem-sucedida;
o manifesto e os artefatos da primeira mini-base já estavam corretamente aprovados.

Commits locais de implementação, na mesma branch:

| SHA | Conteúdo |
| --- | --- |
| `986d5c71e1b772dff74c3224cd98aa60757149be` | Exportador municipal, CLI, fixtures geráveis e testes SQL/JSON |
| `58048bdc25c83312e3c91ac383c509bc2b74909c` | Guardas de fonte/validação, relatório autônomo e promoção sincronizada |
| `b4a15e6ab9dce8ff22062ed5ba80abe25b5b8a9b` | Flutter municipal, modos de assets, smokes, builds e CI |

Este relatório e os documentos de arquitetura/operação são registrados em commit
documental posterior; seu SHA é o HEAD informado na entrega e em `git log`.
O diretório de trabalho fica limpo ao concluir. Nenhum ZIP, SQLite, JSON eleitoral
real ou build foi adicionado ao Git; somente fixtures fictícios pequenos e este
resumo numérico de validação. Servidores estáticos temporários de QA foram encerrados.
