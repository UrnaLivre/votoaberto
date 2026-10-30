# M4 — Correção do wrapper Windows e revisão da comparação

Revisão local em 30/10/2026 na branch `feat/m4-embedded-municipal-results`, a
partir de `132d019ea747dad950d7bd771cbf7a18dba1e2cf`. Nenhuma outra branch,
importação nacional, atualização de agregações ou publicação faz parte da correção.

## Causa confirmada

O [workflow 41093427469](https://github.com/UrnaLivre/votoaberto/actions/runs/41093427469)
passou em Web e Android, mas falhou no job Windows `124192911296`. O log foi lido
pelo conector GitHub: instalação do SDK e `flutter pub get` passaram; o preflight
validou o fixture e imprimiu os pins. Às 16:51:45 UTC, a chamada registrada era
`["flutter", "build", "windows", "--release", ...]`, seguida imediatamente de
`[WinError 2] The system cannot find the file specified`, antes de iniciar Flutter.

A causa também foi reproduzida localmente com o SDK no PATH: `shutil.which("flutter")`
encontra `flutter.BAT`, enquanto `subprocess.run(["flutter", "--version"])` falha
com WinError 2. A resolução direta de CreateProcess não faz a seleção PATHEXT que
o shell faz ao executar `flutter pub get`. O problema não era manifesto, CMake
ou compilação Dart/C++.

## Correção

`resolve_flutter` usa `shutil.which`, respeitando PATH/PATHEXT no Windows e
executáveis no Linux. `--flutter` com caminho relativo usa o diretório do operador,
e o caminho resolvido é convertido em absoluto antes da troca de cwd para o app.
Caminhos com espaços permanecem um único argumento; caminhos explícitos inválidos
não são substituídos silenciosamente por outro SDK. Não se usa `shell=True` nem
comando concatenado. O mesmo caminho resolvido atende run/build/native-test.

Há três situações distintas: executável não encontrado (preflight, código 2),
falha de inicialização do caminho resolvido (código 2 com causa original) e comando
Flutter efetivamente iniciado que retorna erro (código original, por exemplo 17).
Nenhuma dessas situações desativa a restauração byte a byte do pubspec/lock ou a
seleção exclusiva de assets. Modo, dataset ID e hash do manifesto continuam pinados.

Regressões exercitam resolução simulada de `flutter.bat`/Linux, lookup real no PATH,
PATHEXT e execução de script com caminho/argumento contendo espaços nos jobs
Windows/Linux, caminhos explícitos absolutos/relativos, ausência de SDK, sucesso,
retorno não zero e falha ao lançar. O teste de build confere também os pins e o
conteúdo temporário do pubspec, com restauração em todos os desfechos.

## Identidade entre turnos e categorias parciais

O catálogo do motor é único por eleição/número. A comparação recebe dois turnos
do mesmo `ElectionDataset` presidencial de ano/cargo validado; portanto não precisa
usar a grafia do nome como identidade. Agora usa número textual e recusa equivalência
se os dois `source_candidate_id` disponíveis discordarem. Sem número, o mock usa
seu ID interno estável. Não há chave global entre cargos/anos, normalização dos
nomes históricos ou tabela inventada de equivalências.

A leitura somente do manifesto real existente confirmou que os candidatos comuns
aos dois turnos têm número e SQ_CANDIDATO coincidentes: 13 → `280002542548`,
22 → `280002551544`. Nenhum SQL/JSON foi regravado. Se uma entrada futura tiver
IDs contraditórios para o mesmo número, a UI mostra correspondência de identidade
não confirmada, sem inventar mudança de candidato ou ausência de participação.
Testes cobrem mudança de caixa/acento, falta de ID de fonte, IDs conflitantes,
números diferentes, mock e participante sem registro naquele recorte.

O resumo já identificava somas parciais de brancos/nulos. A comparação, porém,
convertia essas somas para `null` na apresentação e as mostrava como indisponíveis.
Agora conserva o valor informado com `registros parciais` e mantém indisponível
somente o cálculo de comparação de totais completos. Ausência total é distinta.
O teste cobre inclusive zero explícito parcial; nenhuma ausência de linha é
reinterpretada como zero e nenhuma regra de agregação foi modificada.

## Validação local e limite do CI

O build Windows local usa **fixture**, por meio de `flutter`
no PATH, sem `--flutter`, reproduzindo a forma de invocação do job.
Não se afirma que o GitHub Actions já passou com a correção: o novo código precisa
ser enviado pelo mantenedor para execução remota. Nenhum push, merge ou rerun
do código antigo é executado automaticamente.

| Verificação local | Resultado |
| --- | --- |
| Ruff format/check, escopo completo do workflow Data Engine | Passou, 27 arquivos formatados |
| Regressões isoladas do wrapper | 10 passaram, 13,88 s |
| pytest completo | 121 passaram, 2 integrações oficiais opcionais puladas, 373,98 s |
| Dart format / Flutter analyze | Passaram, nenhuma issue |
| Flutter test com coverage | 64 passaram, 7 testes reais opcionais pulados, 19 s |
| Windows release com fixture, resolução via PATH | Passou, 82,8 s |
| `pip check`, `git diff --check` | Passaram |

Invocação local, a partir da raiz (apenas o PATH do processo recebe o SDK local):

```powershell
$env:PATH = "$PWD\.local\flutter\bin;$env:PATH"
.venv/Scripts/python apps/votoaberto_flutter/tool/embedded_build.py windows --mode fixture
```

O comando resolvido registrou `.../flutter/bin/flutter.bat build windows --release`
com os pins originais do fixture: dataset `96eb0d23029a4db459deecd8` e SHA-256 do
manifesto `102cf7945e5dd4df184442b7e5628e64b9cd43776aa4ce7aa705ee274f2e8cc5`.
Inspeção do pacote: **32 JSONs sintéticos, 67.036 bytes**, hashes idênticos aos
fixtures do repositório e **zero JSONs reais**. O executável em
`apps/votoaberto_flutter/build/windows/x64/runner/Release/votoaberto.exe` desta
rodada é de **demonstração com fixtures**, substituindo somente a saída local do
build Windows anterior. Não é um novo build real, nem uma nova exportação de dados.

Preservação conferida antes/depois: SHA-256 dos **32 JSONs reais locais** iguais,
SQLite nacional de 935.424.000 bytes com tamanho/mtime/dispositivo/inode iguais,
pubspec com SHA-256 igual e lock removido. Os ZIPs não foram abertos, copiados ou
processados. Não foram alterados o exportador, regras de agregação, mini-base,
resumos numéricos ou relatórios históricos M3.1/M4. Prontidão pública permanece
`not_ready`. Os sete testes reais opcionais Flutter não foram repetidos nesta
correção de apresentação/launcher; as regressões usam fixtures sem reimportar dados.

A execução local é Windows/Python 3.12/Flutter 3.47.8/Dart 3.13.7. A suíte Python
está configurada também para Linux e Python 3.11; as regressões nativas de PATH
e script exercitam o sistema do respectivo runner. Linux e a nova revisão do
GitHub Actions ainda precisam ser confirmados pelo CI após o push do mantenedor.

Commits locais de código:

| SHA | Correção |
| --- | --- |
| `862e5d9b3e488a0b9eb36afe6cf9756365ad4fc7` | Resolução Flutter por PATH/PATHEXT e regressões de execução/restauração |
| `01e35d11153c0a1e61f7e0ed95613bc403f71942` | Identidade entre turnos, apresentação de somas parciais e testes Flutter |

Este relatório e o guia operacional são registrados em commit documental
posterior, cujo SHA é informado na entrega. A branch e o histórico são
preservados; working tree limpa ao concluir. Sem push, nova branch ou merge.

## PR #4 — Caminhos sem extensão no Python 3.11

Correção pontual adicional em 30/10/2026, a partir de `6604865`, na mesma branch.
O [run 41118760004](https://github.com/UrnaLivre/votoaberto/actions/runs/41118760004),
job `124279732298`, confirmou a falha apenas no Windows/Python 3.11 ao resolver
um caminho absoluto terminado em `flutter`, quando o arquivo é `flutter.bat`.
A [documentação do Python 3.12](https://docs.python.org/3.12/library/shutil.html#shutil.which)
registra a mudança: `which` passou a expandir PATHEXT também para comandos com
componentes de diretório. No 3.11, esse caminho recebe apenas a checagem direta.

`resolve_flutter` mantém `shutil.which` como primeira escolha. Se ele falhar no
Windows para um caminho **explícito sem extensão**, tenta os sufixos de PATHEXT
na ordem declarada, exclusivamente no diretório já resolvido em relação ao cwd
do operador. Entradas com separadores/componentes de diretório são ignoradas.
Cada candidato precisa ser arquivo regular e passar em `os.access(F_OK | X_OK)`.
Na ausência de PATHEXT, usa os sufixos padrão COM/EXE/BAT/CMD. Não procura outro
SDK no PATH; Linux, argumentos individuais e `shell=False` ficam inalterados.

Primeiro foi executado o teste indicado pelo revisor: passou no Python 3.12.10
local. Duas regressões que reproduzem a checagem direta do Python 3.11 falharam
antes do ajuste (absoluto/relativo sem extensão), confirmando o defeito mesmo
sem um interpretador 3.11 instalado localmente. Após a correção, passaram.
As regressões Windows cobrem os dois comportamentos de `which`, caminhos com
espaços absolutos/relativos, com/sem `.bat`, ordem/restrição de PATHEXT, arquivo
ausente, diretório e acesso de execução recusado. A matriz CI continua executando
as versões nativas 3.11/3.12 em Windows e Linux.

O teste originalmente apontado passou novamente e os **22 testes do wrapper**
passaram em 4,80 s, incluindo restauração do pubspec/lock após todos os desfechos,
pinagem de dataset/hash e passagem de argumentos com espaços. Ruff format/check
do escopo completo do workflow também passaram. A execução conjunta de
`tests/test_embedded_build.py` e `tests/test_embedded_exporter.py` aprovou
**41 testes em 30,98 s**. `git diff --check` passou. Não se repetiram builds ou
testes de widgets, pois esta correção altera somente a resolução Python do SDK.

Nenhuma alteração em exportador, arquitetura Flutter, SQLite, ZIPs, JSONs reais,
totais eleitorais ou histórico de resultados. Os testes usam apenas fixtures
sintéticos; não houve importação/exportação nacional real. A execução remota do
novo commit ainda depende do push do mantenedor; não houve push ou merge automático.
