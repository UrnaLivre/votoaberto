# Publicação Web do Voto Aberto

> Estado M6.1: [candidato tecnicamente elegível](WEB_DATA_PROVENANCE_FINALIZATION.md),
> **READY_FOR_DATA_APPROVAL**. Os dados mantêm o ID eleitoral; a nova release de
> metadados é `cf1a3b405d96fb5dd676f025`, com manifesto/dossiê próprios.
> [Decisão proposta e hashes exatos](WEB_DATA_APPROVAL_DECISION.md).
> `web-data-approval.json` já contém os valores propostos, mas ambas as aprovações
> continuam `false`. Primeiro registrar a decisão humana; depois preflight/bundle.
> `WEB_DEPLOY_ENABLED` não foi ativada. As notas M6 abaixo são históricas.

> Revisão M6: [proveniência e redistribuição](WEB_DATA_PROVENANCE_REVIEW.md).
> Foram obtidas 56 referências oficiais novas, sem divergências com os digests
> retidos. A base continua `not_ready`; a revisão documental não é aprovação
> humana. O preflight permanece bloqueado e `WEB_DEPLOY_ENABLED` não foi ativada.
> Consultar a revisão antes de preencher a aprovação vinculada ao manifesto.

## Estado desta preparação

**Produção bloqueada pelos dados, não liberada por esta branch.** A base local
`e4e9c9cb5189ab5d4e124bfc` declara presidente/2026, turnos 1 e 2, 27 UFs e ZZ.
O manifesto conserva `public_readiness.status: not_ready`, com
`source_hashes_reused_from_local_cache` e `operator_trusted_hashes_incomplete`.
Os termos de redistribuição do recurso eleitoral ainda exigem revisão registrada.
Não é correto mudar esses campos para liberar deploy. A origem não foi autenticada
e a completude de todas as seções não foi avaliada. Ver [política de dados](DATA_POLICY.md).

Os JSONs reais não estão no Git. Um checkout limpo consegue validar a aplicação
com **fixtures fictícias**, mas não produz uma publicação real sem uma base
aprovada, fornecida pelo operador. Fixtures nunca passam pela barreira de produção.
Os resultados medidos nesta missão estão em [WEB_RELEASE_REPORT.md](WEB_RELEASE_REPORT.md).

## Arquitetura e ferramentas

Flutter compila JavaScript (`dart2js`) e usa CanvasKit e fontes do próprio host.
Não há backend, API, CORS externo, analytics ou tiles remotos. Os JSONs municipais
são carregados por UF, com validações e cache limitado já existentes no app.
O Worker **`votoaberto-web`** serve apenas `apps/votoaberto_flutter/build/web` via
Workers Static Assets. Ele não compartilha configuração ou deploy com `urnalivre-web`.

O link institucional usa o delegate oficial `url_launcher_web` **2.4.3** e
`url_launcher_platform_interface` **2.3.2**, por imports condicionais. Foi necessário
para oferecer href, nova aba e teclado sem dupla navegação acessível. Não se
adicionam os plugins Android/Windows/iOS do launcher; o rodapé continua exclusivo
da Web. A única dependência transitiva nova adicional é `plugin_platform_interface`.

| Ferramenta | Versão fixa / referência |
| --- | --- |
| Flutter stable | **3.47.8**, revisão `737ba8f885dc774b53b442759999a312c9461e4e` |
| Dart do Flutter | **3.13.7** |
| Python CI | **3.12**; ferramentas existentes aceitam também 3.11 |
| Node CI e testes | **22.23.4**, arquivo `.node-version` do app |
| Wrangler | **4.156.0**, lockfile npm |
| Playwright | **1.64.1**, lockfile npm |
| compatibility_date | **2026-10-30**, suportada pelo workerd desta versão |

Não atualizar Flutter ou dependências implicitamente para publicar. Conservar
`pubspec.lock` e `package-lock.json`; upgrades precisam de revisão e nova validação.

O SDK fixado **não oferece `--web-content-hash`** (ajuda e código do SDK conferidos).
Não copiar flags da documentação de versões mais novas sem verificar suporte.
O build não usa `--wasm`; os `.wasm` de CanvasKit são recursos do renderizador,
não compilação WASM da aplicação. Não é preciso habilitar COOP/COEP.

## Comandos locais

Na raiz, com Flutter no PATH (ou a instalação local já existente):

```powershell
$env:PATH = "$PWD\.local\flutter\bin;$env:PATH"
$env:FLUTTER_SUPPRESS_ANALYTICS = 'true'
$env:DART_SUPPRESS_ANALYTICS = 'true'
python -m pip install ".[dev]"
cd apps/votoaberto_flutter
flutter --version
flutter pub get --enforce-lockfile
dart format --output=none --set-exit-if-changed lib test integration_test
flutter analyze
flutter test --coverage
npm ci
```

Validar um checkout sem dados reais (não publicar o resultado):

```powershell
python tool/embedded_build.py web --mode fixture
python tool/web_release.py audit --mode fixture --report ../../.local/web-fixture-audit.json
npx playwright install chromium
npm run test:browser
npm run deploy:check
```

Validar os dados reais **já existentes**, sem reimportar ou regenerar a base:

```powershell
python tool/embedded_build.py web --mode real --source ../../data/processed/embedded-presidential-2026
python tool/web_release.py audit --mode real --report ../../.local/web-real-audit.json
flutter test test/real_embedded_smoke_test.dart --dart-define=RUN_REAL_EMBEDDED=true
npm run test:browser
npm run deploy:check
```

`--flutter ../../.local/flutter/bin/flutter.bat` pode ser passado ao wrapper no
Windows. O wrapper adiciona `--release --base-href / --no-web-resources-cdn
--pwa-strategy=none`, modo, ID de dataset e SHA256 do manifesto. Ele valida a base,
seleciona exclusivamente seus assets e restaura o pubspec byte a byte.
Antes de compilar, limpa apenas `build/web` gerado, com verificação de caminho e
recusa de links/reparse points. Isso evita restos de outro modo entre builds
locais consecutivos. Os dados de origem, APKs e saídas de outras plataformas não
são removidos. O wrapper Web usa exclusivamente a saída padrão, sem `--output`.
Para evitar a sondagem WASM opcional do SDK, é possível acrescentar
`-- --no-wasm-dry-run`. A compilação principal continua JavaScript.

O comando genérico `flutter build web --release` usa a demonstração por padrão.
**Não utilizá-lo para publicação.** Os comandos `--production` e `npm run deploy`
recusam dados sintéticos, hashes divergentes e aprovação ausente.

`npm run preview` inicia somente o emulador local em `http://127.0.0.1:8787`.
O Playwright o inicia automaticamente. `PLAYWRIGHT_CHROMIUM_EXECUTABLE` pode apontar
para um Chrome instalado; na validação local foi usado o Chrome existente.
CI instala o Chromium do Playwright. `WRANGLER_SEND_METRICS=false` desativa métricas
do CLI; isso não injeta telemetria no produto. Em ambientes com filesystem restrito,
`WRANGLER_LOG_PATH` pode apontar para um arquivo dentro de `.local/`.

## Estrutura e integridade do artefato

```text
apps/votoaberto_flutter/
  wrangler.jsonc
  web-data-approval.json          aprovação explícita, inicialmente vazia
  build/web/
    index.html                   base href /
    flutter_bootstrap.js         loader local e retirada do worker legado
    flutter.js
    main.dart.js
    flutter_service_worker.js    vazio, gerado com pwa-strategy=none
    web-build.json               identidade do build e avaliação herdada
    _headers                     regras interpretadas pela Cloudflare
    manifest.json, icons/, favicon.png
    canvaskit/                   renderizador local do SDK
    assets/AssetManifest.bin, FontManifest.json, NOTICES
    assets/assets/geo/           cinco JSONs/GeoJSONs e manifesto existente
    assets/assets/fonts/         fontes e licença
    assets/assets/data/real/     manifesto, Brasil, UFs, validação e 28 JSONs por UF/ZZ
```

`tool/web_release.py audit` verifica os hashes e somas usando o validador existente,
identidade do build, ausência de mistura fixture/real, todos os assets essenciais,
bytes das fontes/cartografia, bootstrap, raiz, cabeçalhos e limites. Recusa ZIP,
SQLite, dumps de banco, mapas de código e arquivos de segredo no artefato.
Só remove marcadores gerados `.gitkeep` e `.last_build_id` do **build**; preserva
os arquivos de origem. Não transforma JSONs eleitorais.

Limites oficiais do Workers Free: **20.000 arquivos e 25 MiB por arquivo**.
A documentação não define um limite agregado de bytes para este conjunto de
Static Assets; o limite de tamanho do script Worker não deve ser aplicado à soma
dos assets. A auditoria mede também o tamanho total. O transporte CI tem um
orçamento próprio de 256 MiB descompactados, explicitamente distinto de limite
Cloudflare. Não existe R2, KV, banco ou serviço pago nesta configuração.

O SDK inclui variantes de renderizador e arquivos de símbolos que aumentam o
download total do artefato, mas o navegador só busca os recursos que utiliza.
Duplicações de ícones e fonte fallback são registradas no relatório; não foi
removido um recurso interno do Flutter sem comprovar que é dispensável em todos
os navegadores. A futura granularidade por seção precisa de nova auditoria de
volume e estratégia de distribuição; não extrapolar estes tamanhos municipais.

## Dados aprovados em ambiente limpo

Este passo está **bloqueado** para a base atual. O responsável pelos dados deve
resolver as duas pendências por evidência de origem e avaliação independente,
conforme [operação de dados](DATA_ENGINE_OPERATIONS.md) e
[importação nacional](NATIONAL_IMPORT.md). Esta missão não recalcula confiança,
não reprocessa ZIPs e não autentica fontes.

Depois de existir um pacote tecnicamente elegível, revisar em PR
`web-data-approval.json` com seu `dataset_id`, SHA256 exato do `manifest.json`,
`release_tag` imutável e a revisão de redistribuição (`approved`, URL dos termos
do recurso, responsável e data). Não preencher com expectativas ou simplesmente
copiar `true` sobre o estado atual. O preflight exige **ambas** as avaliações
`ready_for_declared_scope`, sem blockers, e a aprovação vinculada aos mesmos bytes.

Os datasets ficam fora do Git. Para transportá-los ao runner sem criar outro
serviço de armazenamento, reutiliza-se um asset de GitHub Release deste mesmo
repositório. O arquivo `votoaberto-web-data.zip` é ZIP_STORED: transporte sem
compressão/transformação, somente manifesto e JSONs declarados. Criá-lo só após
aprovação; nenhuma release ou tag foi criada nesta entrega.

```powershell
# No diretório Flutter, depois da aprovação efetiva:
python tool/web_release.py preflight --source ../../data/processed/embedded-presidential-2026
python tool/web_release.py bundle --source ../../data/processed/embedded-presidential-2026 --output ../../.local/votoaberto-web-data.zip
```

No GitHub, o operador anexa esse arquivo à Release de dados cujo tag foi revisado.
Não substituir o asset de uma release aprovada. Uma nova base usa nova aprovação
e novo tag. A seleção não utiliza `latest`; SHA256 de manifesto e de cada arquivo
impede troca silenciosa. Não publicar o bundle atual `not_ready`.

O workflow usa `gh release download` com `contents: read`, repositório atual e
tag do arquivo revisado, depois `web_release.py unpack`. A extração recusa paths
externos, duplicatas, symlinks, arquivos adicionais e excesso de tamanho; valida
hashes/somas antes de promover para um diretório novo. Não há URLs arbitrárias,
tokens de armazenamento adicionais ou dados de PR usados pelo deploy.

## CI e publicação automática

O workflow existente `.github/workflows/flutter.yml` foi ampliado, sem criar
outro pipeline de testes Flutter. Faz pub get, formato, análise, testes,
build Web fixture, auditoria, browser e dry-run Wrangler. Conserva os builds
Windows e Android. O workflow Data Engine continua executando Ruff/pytest.
O CI sem dados reais deixa explícita sua cobertura de fixture e nunca a promove.

Somente um push aprovado à `main`, ou execução manual de **Flutter** selecionando
`main`, pode chamar `.github/workflows/deploy-web.yml`, após os três jobs Flutter
passarem. O deploy recompila dados reais aprovados em ambiente limpo, audita,
testa no browser, guarda artefato e publica esse build. Não usa artefatos de PR.
`WEB_DEPLOY_ENABLED` precisa ser `true`; permanece ausente/desativada nesta entrega.
Há permissões `contents: read`, timeouts e concorrência exclusiva de produção.
O job de produção não é cancelado por uma execução nova durante o upload.

No GitHub Settings:

1. Criar environment **`web-production`**, com required reviewers e somente `main`
   como deployment branch (conforme disponibilidade do plano GitHub).
2. Proteger `main`: revisão humana e checks Flutter/Data Engine exigidos.
3. Criar Actions Secrets **`CLOUDFLARE_API_TOKEN`** e **`CLOUDFLARE_ACCOUNT_ID`**.
   O workflow passa apenas esses dois secrets para a rotina reutilizável.
4. Só depois do go/no-go, criar Actions Variable **`WEB_DEPLOY_ENABLED=true`**.
5. Executar **Actions → Flutter → Run workflow → main** para o primeiro deploy.
   As próximas alterações relevantes aprovadas na main seguirão o mesmo caminho.

O arquivo Wrangler tem `name: votoaberto-web`, diretório `./build/web`,
`workers_dev: true`, preview URLs desativadas e nenhuma rota/domínio gerenciados
por código. Não possui `main`, script Worker, bindings ou backend desnecessários.
Não adicionar `urnalivre-web` ou outros Workers à configuração.

**Um único sistema publica produção: GitHub Actions.** Antes de ativá-lo,
conferir no painel do **votoaberto-web** se há Workers Builds/Git integration,
deploy hook ou outra automação conectada e desativar a publicação duplicada
somente deste Worker. Não houve acesso autenticado à conta Cloudflare nesta
missão; a ausência de integração duplicada ainda precisa de confirmação humana.

## Cloudflare: criação e credenciais

Após a aprovação dos dados e do código, um administrador deve criar **apenas**
`votoaberto-web` em Workers & Pages. Pode criar o Worker no painel, sem conectar
o Git para Builds, ou permitir a primeira criação pelo deploy autorizado. Não
publicar placeholders ou a fixture no domínio oficial.

Recomenda-se criar o Worker como administrador e então gerar um token dedicado
com **Workers Editor/Edit no recurso individual votoaberto-web**, na conta correta.
A autorização granular atual permite limitar o token a um Worker existente;
não é possível selecionar um recurso que ainda não existe. Isso reduz a exposição
do site institucional e dos demais projetos. O token não precisa administrar DNS,
KV, R2, D1, Pages ou rotas de zona. Não usar Global API Key. Caso a conta ainda
apresente somente a permissão legada Account / Workers Scripts / Edit, ela é mais
ampla: não a tratar como isolamento por Worker e revisar essa exceção antes de
ativar publicação na conta compartilhada.

Criar o token no painel de API Tokens, selecionar a conta e o Worker individuais,
guardar diretamente no secret do GitHub e registrar expiração/rotação com o operador.
O Account ID é obtido no painel da conta. Não inserir tokens em arquivos,
comandos versionados, screenshots ou relatórios. Os testes locais e dry-run não
exigiram ler nem criar credenciais.

## Primeiro endereço e domínio definitivo

O primeiro deploy autorizado publica em
`https://votoaberto-web.<subdominio-da-conta>.workers.dev`. Usar o endereço mostrado
nos logs do Wrangler; não adivinhar o subdomínio. Validar raiz, JSONs, mapas,
turnos, histórico, casos especiais, link e recarga antes de associar o domínio.

Depois de aprovação humana:

1. Abrir **Workers & Pages → votoaberto-web → Settings → Domains & Routes**.
2. Selecionar **Add → Custom Domain** e informar somente
   **`votoaberto.urnalivre.com.br`** na zona já existente.
3. Conferir se já há A/AAAA/CNAME para esse hostname. Se houver conflito, identificar
   o proprietário e destino antes de alterar **somente** esse registro autorizado.
   Não apagar registros de `urnalivre.com.br`, `www` ou outros projetos.
4. Aguardar ativação do registro e do certificado SSL gerenciado pela Cloudflare.
5. Abrir a URL final, conferir HTTPS sem erro, hostname no certificado, resposta
   200 da raiz e o mesmo dataset/hash de `web-build.json`.

**Não trocar nameservers, não criar wildcard route e não editar o domínio raiz.**
O domínio institucional já funciona na Cloudflare. O vínculo de domínio é manual
e não faz parte de `wrangler.jsonc`, evitando alteração prematura e evitando que
uma execução futura tente gerenciar o site institucional.

Se o certificado ficar pendente, conferir o hostname exato, a zona selecionada,
eventuais CAA e o estado mostrado no painel. Resolver apenas o conflito demonstrado,
sem relaxar configurações SSL de toda a zona. Certificados e DNS não foram alterados
nem validados nesta entrega.

## Rotas, cache, segurança e atualização

As rotas atuais usam hash: `/#/uf/SC?modo=2`, `/#/mundo?modo=1` e
`/#/mundo/localidade/29432?modo=comparacao`. O fragmento não chega ao servidor.
`not_found_handling: none` preserva 404 de JS/JSON/imagens/WASM inexistentes;
`html_handling: auto-trailing-slash` resolve `/` para `index.html`. Não há motivo
para fallback SPA que transforme assets ausentes em HTML 200. Links sem `#`
para rotas internas não fazem parte do contrato atual.

Todos os recursos usam `Cache-Control: public, max-age=0, must-revalidate` e
ETag do Static Assets. Não há cache imutável. HTML, bootstrap, scripts e JSONs
revalidam a cada uso; não sobrepor essa regra com Cache Rules de zona que forcem
TTL de browser para esse subdomínio. A CSP limita apenas `frame-ancestors 'none'`,
sem bloquear a execução Flutter/CanvasKit. `_headers` também define nosniff,
Referrer-Policy, Permissions-Policy e X-Frame-Options DENY.

O build desativa o service worker offline-first legado. O bootstrap remove
apenas registros `flutter_service_worker.js` no escopo raiz deste app e os três
caches conhecidos do Flutter; se necessário faz uma recarga para abandonar o
controller antigo. Não registra um worker novo nem apaga caches de outros apps.
Uma instalação antiga pode precisar receber primeiro a atualização do worker
vazio para deixar de servir um HTML antigo; conferir isso na migração em produção.
Não há promessa de funcionamento offline depois de reiniciar o browser.

Uma aba aberta pode manter código/dados já carregados. Se um deploy trocar a base,
as verificações existentes recusam mistura de hashes em leituras tardias; recarregar
a aba obtém o conjunto novo. No go/no-go, testar também uma aba aberta durante o
deploy real. Não se usa hashing de caminhos que exigiria retenção de versões de
assets antigas. Novas releases não exigem limpar cache manualmente; uma recarga
normal pode ser necessária para uma aba que permaneceu aberta entre versões.

## Rollback

1. Desativar temporariamente `WEB_DEPLOY_ENABLED` e aguardar/encerrar qualquer
   job de deploy pendente antes de operar rollback, para evitar sobreposição.
2. No painel, abrir **votoaberto-web → Deployments**, escolher a versão funcional
   registrada nos logs da última entrega e **Rollback**. Conferir nome e versão.
3. Alternativamente, no diretório Flutter com credenciais do Worker correto:

```powershell
npx wrangler deployments list --name votoaberto-web
npx wrangler rollback ID_DA_VERSAO --name votoaberto-web --message "Rollback aprovado pelo operador"
```

O ID é um argumento real obtido do histórico; nunca executar literalmente o
placeholder acima. A sintaxe dos comandos foi conferida na ajuda do Wrangler
fixado, mas nenhum rollback remoto foi executado. A Cloudflare mantém até 100
versões recentes para rollback. Conferir novamente raiz, `web-build.json`, JSONs,
cabeçalhos e navegação. Reativar o CI somente depois de corrigir/reverter o código
que publicou a versão problemática por PR revisado.

Guardar o artefato aprovado do job por 30 dias e arquivar a cópia junto à evidência
operacional se retenção maior for necessária. Se uma versão não estiver disponível
para rollback, recompilar o commit revisado com sua aprovação/dataset exatos em
checkout separado, repetir auditoria/testes e fazer novo deploy autorizado.
Não resetar main nem reconstruir usando uma base diferente com o mesmo nome.

## Go / no-go do operador

- [ ] Os dois blockers de origem foram resolvidos por avaliação documentada;
      manifesto tecnicamente elegível, redistribuição revisada e aprovação com hash.
- [ ] Bundle aprovado disponível no tag revisto deste mesmo repositório.
- [ ] PR revisado; CI Flutter e Data Engine verdes em runner limpo.
- [ ] Worker correto criado, token dedicado limitado, secrets e environment configurados.
- [ ] Apenas GitHub Actions publica `votoaberto-web`; nenhuma integração duplicada.
- [ ] Primeiro deploy autorizado em workers.dev e validação real concluída.
- [ ] Certificado e hostname definitivo ativos sem alterar o site institucional.
- [ ] Desktop/mobile, zoom, navegação, recarga, Brasil/UF/município/exterior e
      Bruxelas/Trípoli conferidos; ausência de dados permanece explícita.
- [ ] Aba antiga durante deploy, revalidação e recuperação de cache conferidas.
- [ ] ID da versão estável e artefato registrados; rollback operacional ensaiado.

**Não executar o primeiro deploy enquanto houver item impeditivo pendente.**
A tag de produto sugerida é `v0.5.0`, coerente com `0.5.0+3` do pubspec e sem
tags existentes no repositório no início da missão. É proposta, não autorização.
Notas propostas em [WEB_RELEASE_NOTES.md](WEB_RELEASE_NOTES.md). Não criar tag ou
GitHub Release de produto até aprovação humana.

Tarefa posterior, em outro repositório, depois de confirmar produção:
**Habilitar o Voto Aberto no site institucional, apontando para
https://votoaberto.urnalivre.com.br.** Nenhum flag institucional foi confirmado
nesta missão; não assumir `votoAbertoWebEnabled` nem alterar `UrnaLivre/urnalivre`.

## Referências oficiais consultadas

Configuração e limites conferidos em 31/10/2026:

- [Static Assets](https://developers.cloudflare.com/workers/static-assets/)
- [Limites Workers](https://developers.cloudflare.com/workers/platform/limits/)
- [Billing de Static Assets](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/)
- [Resolução HTML](https://developers.cloudflare.com/workers/static-assets/routing/advanced/html-handling/)
- [Cabeçalhos](https://developers.cloudflare.com/workers/static-assets/headers/)
- [Autorização por Worker](https://developers.cloudflare.com/workers/authorization/workers/)
- [CI externo](https://developers.cloudflare.com/workers/ci-cd/external-cicd/)
- [Configuração Wrangler e rotas geridas pelo painel](https://developers.cloudflare.com/workers/wrangler/configuration/)
- [Rollback](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/)
- [Inicialização Flutter Web](https://docs.flutter.dev/platform-integration/web/initialization)

As capacidades descritas na documentação Flutter mais nova não substituem a
verificação da ajuda e do código do SDK 3.47.8 fixado neste projeto.
