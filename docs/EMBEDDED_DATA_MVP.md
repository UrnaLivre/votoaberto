# MVP municipal embarcado — M4

O cliente consulta presidente/2026 por Brasil, UF e município, nos dois turnos,
com JSONs locais e sem API de resultados. A prévia real é **local**:
`public_readiness: not_ready` da release M3.1 é preservado. O modo demonstração
M1 continua disponível e explicitamente fictício. Evidências medidas:
[relatório M4](M4_COMPLETION_REPORT.md). Decisão: [ADR 0004](adr/0004-embedded-municipal-data.md).

## Exportar a partir da release existente

Na raiz do repositório, com Python 3.11/3.12 e o Auditor instalado conforme
[seu README](../apps/votoaberto_auditor/README.md):

```powershell
votoaberto-auditor export-embedded --dataset data/processed/national-2026 --output data/processed/embedded-presidential-2026 --json .local/embedded-export.json
votoaberto-auditor validate-embedded --dataset data/processed/embedded-presidential-2026 --json .local/embedded-validation.json
```

`--dataset` aceita uma release ou diretório cujo `current.json` aponta para ela.
O exportador verifica schema SQLite 1, manifesto, tamanho e SHA-256 declarado,
validação da release, integridade física, matemática e referencial. Abre SQLite
com `mode=ro` e `query_only`, sem copiar o banco ou reler ZIPs. Verifica a identidade
do arquivo e do manifesto antes/depois da operação. Fonte e saída devem ser separadas.

Totais de seção são agregados independentemente das linhas por candidato.
Uma segunda consulta confere os JSONs municipais, candidatos, categorias e
identidades diretamente contra o SQLite; consultas estaduais independentes e
somas hierárquicas conferem UF, Brasil doméstico e Brasil incluindo ZZ.
Qualquer diferença impede promoção; a release anterior e `current.json` são preservados.
Uma promoção idempotente confere os arquivos existentes; não sobrescreve uma versão incompatível.

`validate-embedded` revalida hashes, schema e somas dos JSONs já produzidos. Seu
relatório explicita `sqlite_comparison: not_repeated`: não repete nem substitui
a comparação SQL feita durante a exportação. Não transforma cobertura ou origem
limitadas em certificação eleitoral.

Orçamento padrão: 8 GiB de trabalho, reserva livre de 15 GiB. Flags
`--max-work-disk-bytes` e `--min-free-disk-bytes` permitem ajuste consciente.
Temporários SQLite ficam na área própria monitorada de `WorkRun`; promoção e
registro de propriedade compartilham o mesmo mutex. Apenas arquivos próprios
podem ser limpos. `.runs/` guarda recibos; `.work/` não retém intermediários após sucesso.
O pico por diferença do volume é conservador, pois inclui atividade externa;
o relatório também separa bytes visíveis e temporários SQLite observados.

## Contrato JSON 1

```text
embedded-presidential-2026/
  current.json
  releases/<dataset_id>/
    manifest.json
    national.json
    states.json
    validation.json
    municipalities/{AC,...,TO,ZZ}.json
```

UTF-8 compacto, chaves ordenadas, newline final, sem compressão obrigatória.
`dataset_id` incorpora hash SQLite e hash das regras; metadados voláteis de
tempo/memória/disco ficam no recibo da execução, fora do pacote imutável.
O manifesto registra `schema_version`, `rules_version`, exportador/hash de código,
`source_release`, `source_sqlite_sha256`, natureza, ano/cargo, eleições, catálogo
de candidatos, territórios, contagens municipais, hashes/tamanhos dos demais
artefatos, atribuição e avaliação da fonte. O hash do próprio manifesto é fixado
no build, evitando uma autorreferência impossível. SHA-256 detecta diferenças de
bytes sob essas premissas; não é assinatura digital nem autenticação do TSE.

O catálogo é específico de eleição/turno. Cada candidato preserva `number`,
`source_candidate_id` e nome; a chave interna combina eleição e número.
Cada município preserva código **TSE textual** e nome da fonte, identificado
por UF/ZZ + código, nunca somente pelo nome. Não há conversão para código IBGE
nem catálogo externo para completar uma quantidade teórica de municípios.

Cada resultado contém eleição original, turno, seções, mapa de votos por candidato,
`totals` e `available_sections`. Totais: `counted`, `valid`, `blank`, `null`,
`eligible`, `turnout`, `abstention`. Ausência total é JSON `null`; disponibilidade
parcial conserva a soma disponível e a quantidade de seções informantes. O cliente
não apresenta essa soma parcial como total completo nem calcula razões indevidas.
Brancos/nulos são categorias separadas; não integram o catálogo nominal.
Candidatura ausente no outro turno é **não participou**; registro ausente de
uma candidatura participante é **sem dado**, nunca zero fabricado.

`national.rounds` inclui ZZ; `national.domestic_rounds` soma só as 27 UFs.
`ZZ` é exterior, não uma 28ª UF nem um polígono. Localidades do exterior usam os
códigos existentes, sem inventar coordenadas ou equivalência com município brasileiro.
Turnos podem ter quantidades diferentes de seções, localidades, aptos e candidatos.

## Instalar e compilar sem misturar modos

Use o wrapper a partir da raiz, com Flutter 3.47.8 / Dart 3.13.7:

```powershell
python apps/votoaberto_flutter/tool/embedded_build.py windows --mode real --source data/processed/embedded-presidential-2026 --flutter .local/flutter/bin/flutter.bat
python apps/votoaberto_flutter/tool/embedded_build.py web --mode real --flutter .local/flutter/bin/flutter.bat
python apps/votoaberto_flutter/tool/embedded_build.py apk --mode real --flutter .local/flutter/bin/flutter.bat
python apps/votoaberto_flutter/tool/embedded_build.py run --mode real --flutter .local/flutter/bin/flutter.bat -- -d windows
```

Na primeira instalação, `--source` copia **só os JSONs validados** para
`assets/data/real/`, ignorado pelo Git. Nas próximas, pode ser omitido. A origem
pode ser release ou diretório canônico. O destino recusa arquivos desconhecidos,
versões diferentes e mistura de versões. Para atualizar, prepare outro diretório
de build/checkout e instale a nova release revisada; não há exclusão automática
da versão anterior. `--dry-run` executa o preflight sem compilar.

O wrapper resolve Flutter por `shutil.which` antes de executar o comando. Um nome
simples usa PATH e, no Windows, PATHEXT para localizar `flutter.bat`; um caminho
explícito com `--flutter` é resolvido em relação ao diretório de quem invocou a
CLI, inclusive com espaços. Caminho explícito inválido não recorre a outro SDK
do PATH. A chamada mantém lista de argumentos e `shell=False`. Ausência do SDK
é erro de preflight; falha ao iniciar o caminho resolvido é diagnosticada
separadamente; comando iniciado que retorna falha preserva seu código de saída.
Detalhes da regressão Windows: [correção do CI](M4_CI_WINDOWS_FIX.md).

O modo real exige os 56 pares de UF/ZZ + turno, presidente/2026, schema suportado,
hashes e somas válidos. Ausência ou incompatibilidade falha **antes** de executar
Flutter. O wrapper fixa ID e SHA-256 do manifesto por `dart-define`. O cliente
confere esses valores; uma execução manual com `VOTOABERTO_DATA=real` sem os pins
também é recusada. Erros reais não acionam fallback fictício.

O wrapper seleciona temporariamente apenas as duas pastas de assets do modo
escolhido (pai e `municipalities/`, listadas explicitamente no `pubspec.yaml`).
Um lock impede builds simultâneos. Ao terminar, inclusive por falha normal, restaura
os bytes originais do pubspec. Edição externa concorrente é preservada e reportada.
Não edite o pubspec durante o build. Em encerramento abrupto do processo/máquina,
confira a ausência do build antes de revisar manualmente o bloco marcado e o lock;
a restauração não é garantia contra queda de energia.

Para CI e revisão sem arquivos reais:

```powershell
python apps/votoaberto_flutter/tool/embedded_build.py web --mode fixture
python apps/votoaberto_flutter/tool/embedded_build.py windows --mode fixture
python apps/votoaberto_flutter/tool/embedded_build.py apk --mode fixture
```

`fixture` usa os pequenos JSONs **FICTÍCIOS** versionados em `assets/data/synthetic/`.
Podem ser recriados com `python tools/generate_embedded_fixture.py`.
Os JSONs de fixture têm LF fixado em `.gitattributes` para que os hashes também
coincidam em checkout Windows com `core.autocrlf=true`.

`demo` preserva
o mock M1 em memória e omite os JSONs de resultados. Execução Flutter comum sem
defines continua em `demo`. O wrapper empacota exclusivamente o modo escolhido;
ter assets reais instalados não os inclui num build fixture/demo.

## Cliente, consulta e limitações

`EmbeddedElectionRepository` usa `AssetBundle` em Web/Windows/Android; nenhuma
dependência de SQLite, `dart:io` ou HTTP na camada compartilhada. Inicialização lê
manifesto, Brasil e UFs. Municípios carregam por UF sob demanda, com cache LRU de
três abrangências, deduplicação de leituras e descarte de respostas obsoletas no
controller. Decodificação/verificação usa `compute` em plataformas com isolates;
na Web executa no runtime Web. O tamanho máximo observado por UF é documentado
no relatório; não se promete paralelismo Web nem benchmark de memória do app.

Navegação: Brasil → UF → município; busca sem acento/caixa, lista por botão,
Enter/Tab, foco e resumos semânticos. URLs, por exemplo:
`/#/uf/SP/municipio/71072?turno=2&visao=comparison`. Código inexistente, turno ou
visualização inválidos exibem indisponibilidade. Voltar/avançar preserva a seleção.
Tema claro/escuro e mapa M1 são mantidos. Consulta a zona/seção permanece futura.

Percentuais nominais usam votos válidos; participação usa aptos somente com
denominador completo e positivo. Comparações não inferem transferência de votos
entre eleitores. A metodologia mostra versão, fonte e limitações; o banner real
identifica **prévia local** e verificação de origem limitada, sem banner fictício.

Na comparação dos dois turnos da mesma eleição lógica (ano/cargo), a identidade
usa o número nominal do catálogo e confere compatibilidade de `source_candidate_id`
quando presente nos dois lados. Grafia do nome não define identidade; nomes e
listas originais são preservados. IDs de fonte contraditórios impedem equivalência
e exibem correspondência não confirmada. Não é uma chave global entre anos/cargos.
Participante sem registro no recorte continua distinto de candidatura ausente.
Somas parciais de brancos/nulos são exibidas com o valor disponível e o rótulo
`registros parciais`, também na comparação; ausência total continua `Indisponível`.
Variações de totais completos não são calculadas a partir de somas parciais.
Um zero explicitamente informado permanece zero; nenhuma linha ausente vira zero.

Windows/Android carregam resultados empacotados sem servidor. O teste nativo
opcional bloqueia HTTP **dentro da aplicação**, sem alterar a rede do computador:

```powershell
python apps/votoaberto_flutter/tool/embedded_build.py native-test --mode real --flutter .local/flutter/bin/flutter.bat
# No diretório Flutter, smoke adicional de leitura dos arquivos locais reais:
flutter test test/real_embedded_smoke_test.dart --dart-define=RUN_REAL_EMBEDDED=true
```

Web é um build estático; primeira visita exige conectividade ao host dos assets.
O Flutter de referência ainda usa service worker legado por padrão; o wrapper
passa `--pwa-strategy=none` para desativá-lo explicitamente. Essa opção é depreciada
no SDK e deverá ser revista ao atualizar Flutter. Não há cache PWA próprio.
O bootstrap final é inspecionado; **não há garantia de uso offline
após fechar/reabrir o navegador**. PWA e política de atualização de cache ficam
para outra etapa. Nenhum backend/API de resultados foi introduzido.

Os workflows continuam usando fixtures, Ruff/pytest e Flutter format/analyze/test,
com builds Web, Windows e APK debug. Não baixam ZIPs/SQLite reais nem publicam dados.
Assinatura Android de produção, distribuição pública, autenticação das fontes e
completude de todas as seções continuam pendentes.
