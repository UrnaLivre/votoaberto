# M7 — Fundação das releases nativas

M7 prepara distribuição; **Android e Windows ainda não foram publicados**.
Web permanece em https://votoaberto.urnalivre.com.br/, no pipeline existente.
Não há upload para Play, criação de release pública ou instalador nesta etapa.

## Versão única do produto

`apps/votoaberto_flutter/pubspec.yaml` é a fonte de verdade: **0.5.0+3** nesta M7.

| Campo | Regra |
| --- | --- |
| Produto / Android versionName | `X.Y.Z`, semântica pública consistente entre plataformas |
| Android versionCode | `N`, inteiro positivo, sempre maior que qualquer build já enviado à Play |
| Windows FILEVERSION / PRODUCTVERSION | `X,Y,Z,N` (string do produto `X.Y.Z+N`) |
| Sobre | Versão `X.Y.Z`, build `N`, obtidos da instalação por package_info_plus |
| Tag futura do aplicativo | `app-vX.Y.Z+N`, apontando para o commit exato do build |
| Dados aprovados | `web-data-*`, independentes das tags de aplicativos |

Cada componente deve caber em 16 bits (`0..65535`; N começa em 1), limite
compartilhado deliberado para a versão Windows. O limite Android isolado é maior.
Reservar N globalmente para o produto, inclusive faixas de teste; nunca reiniciar
o contador ao mudar X/Y/Z. Mesmo produto com novo pacote de dados exige nova
release do aplicativo e novo N. Incrementar patch para correções/dados, minor
para funcionalidades compatíveis e major para mudanças incompatíveis de produto.
Não derivar N de execuções de CI, relógio, hashes ou versão do dataset.

`native_release.py check-version --previous-ref origin/main` valida a evolução
contra main no CI. Mudanças sem incremento de versão são permitidas durante o
desenvolvimento; a aprovação de uma distribuição deve reservar uma versão inédita,
conferir o maior versionCode na Play Console e nas tags, e fazer commit antes do
build. CI não tem acesso à Play Console e não atesta essa reserva operacional.
Não passar overrides de versão/target/dart-define ao wrapper de produção nativo.

O recibo `build/native-release/<plataforma>/native-release.json` associa produto,
tag proposta, commit, plataforma, dataset_id, metadata_release_id, manifesto e
release de dados aos hashes/tamanhos dos arquivos distribuíveis. O workflow
também registra a versão exata do SDK em `flutter-sdk.json`; lockfile fica no Git.
Builds exigem checkout limpo. Esses registros permitem rastrear/reproduzir a
entrada do build; não prometem builds binariamente idênticos entre toolchains,
timestamps ou assinaturas diferentes. A futura publicação deve anexar o recibo
e os checksums finais do instalador assinado/AAB e preservar os artefatos exatos.

## Serviço de atualização

`lib/features/updates/` contém:

- `AppVersionInfo`: parse estrito de versões estáveis, comparação numérica e versão Windows.
- `PlatformUpdateProvider`, `UpdateCheck` e `UpdateService`: consulta única por sessão,
  timeout de 8 segundos, falha silenciosa e início somente por ação do usuário.
- `AndroidUpdateProvider` / `PlayUpdateClient`: adaptador testável para Play.
- `WindowsUpdateProvider` / `WindowsRelease`: seleção e validação de metadados.
- `ReleaseHost`: estado acima do router, aviso discreto e botão Sobre no cabeçalho.

Estados internos: atualizado, disponível, indisponível, incompatível, em andamento
e pronto para instalar. Nenhum deles vira erro técnico quando offline. A consulta
é independente da leitura dos dados eleitorais e não impede inicialização ou uso.
Não há polling, telemetria, trackers, token GitHub no aplicativo ou dados privados.
Um único valor local `last_update_notice` (SharedPreferencesAsync) evita reapresentar
o mesmo aviso entre rotas e reinicializações; se o armazenamento falhar, limita-se
à sessão. Dispensar um aviso não impede atualizar manualmente pela loja.

**Web:** provider incompatível, sem consulta, preferência ou aviso de atualização.
Sobre lê a versão local apenas ao ser aberto. Publicação/Worker/domínio e regras
de deploy existentes continuam independentes. Debug/profile também não consultam.
**iOS:** provider incompatível; futura implementação deve respeitar a App Store.

### Android: somente Google Play

Escolha: [`in_app_update` 5.0.0](https://pub.dev/packages/in_app_update), MIT,
adaptador das APIs oficiais, mantido com migração recente para Kotlin integrado
do AGP 9. Requer Flutter >=3.44/Dart >=3.12, compatível com Flutter 3.47.8 fixado
no CI e AGP 9.1 do projeto. O lockfile registra a resolução exata. As dependências
resolvidas usam Dart >=3.13, fornecido pelo SDK Flutter fixado. Não há scraper
de loja, link fictício de listagem, download de APK ou atualização imediata padrão.

`package_info_plus` confirma installerStore `com.android.vending` antes de consultar
a Play. Instalação externa, debug, falta da loja, erro de API e offline não mostram
avisos. A Play confirma identidade, propriedade/conta e elegibilidade, além do
versionCode. Só oferecemos fluxo **flexível** quando permitido. O primeiro toque
em Atualizar aciona o consentimento/download oficial em segundo plano; após o
download, um segundo toque permite completar a atualização e reiniciar. Download
já pronto é reconhecido na próxima inicialização; downloads pendentes não disparam
outro aviso. O download fica sob controle da Play, sem timeout que o interrompa.

Mocks validam o contrato, **não validam distribuição real**. M8 deve instalar pela
faixa de testes/internal app sharing, disponibilizar um segundo build maior e
verificar consentimento, recusa, download, conclusão, reinício e recuperação. Veja
[teste oficial](https://developer.android.com/guide/playcore/in-app-updates/test).

### Windows: contrato pronto, instalação desabilitada

Consulta HTTPS sem autenticação à coleção `/repos/UrnaLivre/votoaberto/releases`,
100 registros por página, até 5 páginas. Nunca usa `/releases/latest`. Timeout
por página de 5 s (conexão 3 s), corpo limitado a 2 MiB, redirecionamentos recusados.
O serviço limita o resultado total a 8 s; requisições pendentes têm limite próprio
e são fechadas. Limite incompleto/rate limit/falha resulta em indisponível silencioso.

Uma candidata exige **todos** os critérios:

- Tag `app-vX.Y.Z+N` estável, versão numericamente maior que a instalada.
- `draft == false`, `prerelease == false`; exclusão formal de `web-data-*`, RC e beta.
- Um único asset `votoaberto-X.Y.Z+N-windows-x64-setup.exe`, enviado e não vazio.
- URL HTTPS exata do repositório, tag e nome esperados, sem query/fragmento/credenciais.
- Digest GitHub `sha256:` com 64 dígitos hexadecimais.

Seleciona a maior versão elegível, independentemente da ordem das releases. Sem
release Windows válida não há atualização fictícia. `canStart` permanece **false**,
logo nenhum aviso acionável é apresentado nesta M7, mesmo que haja candidata.
`start()` não baixa nem executa nada. O digest é apenas parte do contrato; não
substitui assinatura/autenticação do publicador. M9 deverá verificar bytes, origem
dos redirecionamentos para assets GitHub e assinatura Authenticode/publisher antes
de habilitar o botão e obter consentimento para execução/reinício.

## Mesmos dados aprovados da Web

O workflow manual `native-production.yml` baixa **a release já aprovada**
`web-data-2026-v1`, asset `votoaberto-web-data.zip`, do próprio repositório.
Lê o tag de `web-data-approval.json`; reutiliza `web_release.py unpack` e
`require_approved`, incluindo manifesto, hashes, escopo público, revisão de
proveniência e aprovação de redistribuição. Não renomeia a release nem duplica
o pacote. Não requer ZIP original TSE/SQLite bruto nem versiona JSONs reais.

O wrapper existente `embedded_build.py` foi estendido para Windows/AAB, mantendo
a seleção exclusiva de assets e restauração byte a byte do pubspec. Produção
exige `--mode real --production`; AAB só aceita esse modo. Overrides nativos são
recusados. Não há fallback para demo/fixture quando dados reais falham.
Após compilar, uma auditoria verifica os **dados dentro do bundle Windows/AAB**
com a mesma aprovação, impede datasets misturados/arquivos não declarados e só
então emite o recibo. Saída nativa anterior é removida da área gerada para impedir
reaproveitamento de artefato antigo. As limitações e resultados metodológicos
originais permanecem nos dados, na interface e na documentação de proveniência.

## Operação de build controlado

CI de qualidade continua criando Web/Windows/APK debug com fixtures e executando
testes Flutter/Python/browser. Isso não constitui uma release pronta para loja.
O novo workflow é **somente workflow_dispatch**, `contents: read`, sem deploy,
criação de GitHub Release ou upload à Play. O operador deve configurar o environment
`native-production` com revisores/restrição de branches antes do uso; o YAML não
cria essas proteções. Escolher um commit revisado, com CI verde, e a plataforma.
Artefatos de Actions expiram em 14 dias e são resultados de preparação; o bundle
Windows não é ainda instalável nem um release público suportado.

Equivalente local, a partir de `apps/votoaberto_flutter`, após obter/verificar o
pacote aprovado em um diretório novo e usar checkout limpo:

```text
flutter pub get --enforce-lockfile
python tool/web_release.py unpack --archive <votoaberto-web-data.zip> --destination <verified>
python tool/embedded_build.py windows --mode real --production --source <verified>
python tool/embedded_build.py appbundle --mode real --production --source <verified>
```

### Android / M8

ApplicationId preservado: `br.com.urnalivre.votoaberto`. Target API explícita **36**,
compile SDK 36 e min SDK 24 do Flutter fixado. A exigência foi conferida em
2026-11-01 na [documentação oficial](https://developer.android.com/google/play/requirements/target-sdk):
novos apps/atualizações devem usar API >=36 desde 2026-08-31. Revalidar na data
do upload e testar mudanças de comportamento/compatibilidade em dispositivos.

O Gradle aceita `android/key.properties` ignorado (modelo `key.properties.example`)
ou variáveis `ANDROID_UPLOAD_STORE_FILE`, `ANDROID_UPLOAD_STORE_PASSWORD`,
`ANDROID_UPLOAD_KEY_ALIAS`, `ANDROID_UPLOAD_KEY_PASSWORD`. Release sem configuração
completa falha; nunca usa assinatura debug como fallback. Chaves/senhas não entram
no recibo ou log. No workflow a chave base64 vem de `ANDROID_UPLOAD_KEY_BASE64`,
é escrita no temporário do runner com modo restrito e removida mesmo após falha.
Não há geração automática de identidade definitiva nem reutilização de outro app.

Para concluir M8, o operador deve:

- Criar/controlar conta Play e listagem real, políticas, privacidade, Data safety,
  classificação, screenshots e demais requisitos aplicáveis da Console.
- Adotar **Play App Signing**, gerar/controlar/guardar backup da upload key exclusiva
  e certificados; configurar os quatro secrets e environment protegido.
- Reservar versão/build, construir AAB real, verificar assinatura/certificado,
  conferir APKs gerados pela Play/bundletool, ABI, tamanho e alinhamento de 16 KiB.
- Testar em Android físico, offline, acessibilidade, instalação e atualizações em
  faixa de teste com conta elegível. Só então autorizar submissão/publicação na Play.

Nada deve oferecer APK público no site ou GitHub Releases.

### Windows / M9

O runner já tem ícone e nome VotoAberto, `votoaberto.exe` e metadados UrnaLivre;
os números vêm do Flutter/pubspec, sem fallback silencioso para 1.0.0. Empacotar
**todo** `build/windows/x64/runner/Release/` (DLLs, ICU, plugins e assets), validado
pelo recibo; o executável isolado não é um pacote distribuível.

Planejamento: Inno Setup para instalador EXE por usuário, sem elevação por padrão.
Identidade estável proposta para M9: `AppId=br.com.urnalivre.votoaberto`, publisher
UrnaLivre, destino `%LOCALAPPDATA%\Programs\UrnaLivre\VotoAberto`, configurações
em diretório de dados separado controlado pelo aplicativo. M9 deve fixar essa
identidade antes da primeira publicação e mantê-la entre versões/arquiteturas.

Critérios M9: script Inno versionado; ícone/metadados; instalação inicial, upgrade,
reversão em falha, detecção do app aberto, atalhos e desinstalador; preservação de
preferências (incluindo aviso dispensado) em upgrade; remoção limpa dos binários
sem apagar preferências silenciosamente. Definir certificado/publisher, assinar
binários e instalador, validar assinatura e SHA-256 após download, pedir consentimento,
testar em máquina Windows limpa e instalação anterior. Só então habilitar update
e publicar asset EXE, checksums/recibo e código exato sob tag `app-vX.Y.Z+N`.

## Verificação e limites

Testes determinísticos cobrem versões/builds, rejeição de fixtures/overrides,
auditoria do AAB, bundle Windows incompleto, filtro de releases, paginação,
offline/timeout, estados, origem Play, consentimento flexível, persistência de
aviso e versão exibida. Suítes existentes preservam navegação, mapas, ausência de
fallback, comparação eleitoral, Web e pipeline de dados. Evidências executadas
na entrega estão em [M7_VALIDATION.md](M7_VALIDATION.md).

Sem credenciais do operador não se atesta assinatura AAB de produção; sem faixa
Play não se atesta In-App Updates real; sem instalador/assinatura M9 não se atesta
upgrade Windows. Um build local/fixture bem-sucedido não elimina essas pendências.
