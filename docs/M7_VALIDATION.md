# M7 — Validação da fundação nativa

Implementação e operação: [NATIVE_RELEASES.md](NATIVE_RELEASES.md).
Validação em 2026-11-01. Sem publicação nativa, merge ou mudança manual de produção.
PR: https://github.com/UrnaLivre/votoaberto/pull/10, branch `feat/native-release-foundation`.

## Evidências locais

Windows, Flutter **3.47.8**, Dart **3.13.7**, Python **3.12**.

| Verificação | Resultado |
| --- | --- |
| `flutter analyze --no-pub` | Nenhum problema |
| `dart format --output=none --set-exit-if-changed lib test integration_test` | 55 arquivos, nenhuma alteração |
| Suíte Flutter completa | **171 aprovados, 7 condicionais ignorados** |
| Testes específicos de atualização | **16 aprovados**, incluídos na suíte completa |
| Smoke com dados reais (`RUN_REAL_EMBEDDED=true`, readiness aprovada) | **7 aprovados** |
| Suíte Python completa | **272 aprovados, 2 condicionais ignorados** antes das duas verificações finais de checkout |
| Testes finais de release nativa | **31 aprovados**, incluindo as duas verificações adicionais |
| Ruff em todos os caminhos do CI | Aprovado |
| actionlint em todos os workflows | Aprovado |
| Build Web fixture + auditoria | Aprovado, 82 arquivos, dataset fixture exclusivo |
| Playwright Web fixture | **7 aprovados, 1 condicional de dados reais ignorado** |
| Download e unpack da release aprovada | Aprovado com manifesto/hashes/proveniência |
| Preflight Windows e AAB de produção (`--dry-run`) | Aprovado, mesma identidade de dados da Web |

Os condicionais existentes exigem dados reais ou fontes oficiais opt-in; não foram
removidos. O smoke real foi executado separadamente. Os testes de navegador cobrem
startup, histórico/deep links, quatro dimensões de viewport, tema/zoom, ausência
de requisições externas inesperadas, cabeçalhos/cache e retirada do worker legado.

As evidências transitórias ficam em `.local/m7/` (fora do Git); o relatório e o CI
registram o resultado reproduzível. A elevação do SDK mínimo para Dart 3.13 exige
formatação mecânica de arquivos existentes; não altera seus testes ou cálculos.

## Identidade dos dados

- Release existente: `web-data-2026-v1`, asset `votoaberto-web-data.zip`, **5.703.023 bytes**.
- SHA-256 do ZIP informado pelo GitHub: `6e065f31ee56d1c2fbbb51a80cbcd5d9f041d27ba176e5fe8a32647ab573513b`.
- Dataset: `e4e9c9cb5189ab5d4e124bfc`.
- Metadata release: `cf1a3b405d96fb5dd676f025`.
- Manifesto: `c1dd2ae876eecfd685d67bb5f53bb7efd223c8db5772a76a83b773b0da2a54e3`.

O unpack utilizou `web_release.py`, sem reexportar dados nem reescrever aprovações.
O dry-run nativo mostra `--release`, `VOTOABERTO_DATA=real`, dataset, hash e commit.
Não constitui compilação nativa real nem validação de assinatura.

## CI remoto

O primeiro CI confirmou o build Windows. Identificou diferenças de formatação
Dart 3.13 e um import Kotlin sombreado na configuração de assinatura Android;
ambos corrigidos no commit `991d159`. As matrizes finais serão conferidas antes
de encerrar a entrega. Não há auto-merge configurado por esta missão.

## Arquivos e responsabilidades

- `lib/features/updates/`: modelos, serviço, adaptadores Android/Windows/Web, aviso e Sobre.
- `lib/app/votoaberto_app.dart`, `lib/features/explorer/presentation/explorer_page.dart`:
  composição da interface, preservando router e consulta eleitoral.
- `pubspec.yaml`, `pubspec.lock`, `windows/flutter/generated_plugins.cmake`:
  dependências resolvidas e registro gerado de plugin.
- `tool/embedded_build.py`, `tool/native_release.py`, `tests/test_native_release.py`:
  gates de produção, proveniência e auditoria do AAB/bundle.
- `test/update_service_test.dart`: versões, estados, Play, seleção Windows e interface.
- `android/app/build.gradle.kts`, `android/app/src/main/AndroidManifest.xml`,
  `android/key.properties.example`, `.gitignore`: API 36, rede Play e upload key protegida.
- `windows/runner/Runner.rc`: versão obrigatória do Flutter, preservando ícone/nome.
- `.github/workflows/native-production.yml`: builds manuais sem publicação;
  `.github/workflows/flutter.yml`: validação de progressão de versão adicionada.
- `README.md`, `apps/votoaberto_flutter/README.md`, `docs/ROADMAP.md`,
  `docs/NATIVE_RELEASES.md`, este relatório: estado atual e critérios M8/M9.
- Demais fontes/testes Dart existentes: somente formatação pelo SDK declarado.

`deploy-web.yml`, `web-data-approval.json`, Worker, domínio, assets geográficos,
resultados e limitações metodológicas permanecem preservados.

## Limites e próximos marcos

O Windows local não permite a criação dos symlinks exigidos pelo plugin transitivo
JNI; tentativas locais falharam nesse requisito de ambiente. Não alteramos o modo
de desenvolvedor do sistema. O build Windows remoto é a validação dessa plataforma.

M8 depende de upload key exclusiva sob controle do operador, Play App Signing,
AAB real assinado, listagem/políticas e testes de atualização em faixa Play com
versionCode maior. M9 depende do instalador completo, assinatura, validação dos
bytes/publisher, consentimento e testes de instalação/upgrade/desinstalação.
Download e execução de instalador Windows permanecem desabilitados.
