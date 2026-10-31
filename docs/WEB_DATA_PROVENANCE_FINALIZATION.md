# M6.1 — Finalização técnica da proveniência

Data: 31/10/2026. Branch `feat/web-production-cloudflare`.
**READY_FOR_DATA_APPROVAL** — critérios técnicos concluídos, decisão formal
do operador ainda pendente. Nenhum push, merge, tag, release ou deploy executado.

## Entrega e evidências

- [Recálculo dos 57 ZIPs](WEB_DATA_CURRENT_HASHES.json).
- [Testemunho de aquisição explicitamente fornecido pelo operador](WEB_DATA_ACQUISITION_TESTIMONY.json).
- [Política geral implementada e testada](DATA_PROVENANCE_POLICY.md).
- [Preservação de artefatos históricos e dados eleitorais](WEB_DATA_M61_PRESERVATION.json).
- [Reavaliação, testes, build, auditoria e preflight](WEB_DATA_M61_VALIDATION.json).
- [Candidato exato](WEB_DATA_APPROVAL_CANDIDATE.json) e
  [decisão consolidada para revisão humana](WEB_DATA_APPROVAL_DECISION.md).

M6 permanece como fotografia histórica em `WEB_DATA_PROVENANCE_REVIEW.md` e
seus JSONs. O testemunho novo foi extraído da mensagem M6.1, sem inventar nome,
data do download, transcript HTTPS, assinatura ou aprovação de publicação.
O estado inicial estava limpo em `a983642`, na branch solicitada.

## 1. Recálculo atual, sem reprocessamento eleitoral

`tools/provenance/rehash_local.py` leu os 57 arquivos sequencialmente, uma vez
por ZIP, atualizando SHA-256 e SHA-512 no mesmo loop. Foram lidos exatamente
**5.463.538.463 bytes**, entre **21:38:26.649747 e 21:38:38.855754 UTC**.
Nenhum membro ZIP foi extraído/interpretado; não houve rede nesse comando.

| Verificação | Resultado |
| --- | ---: |
| ZIPs recalculados | 57/57 |
| SHA-256 atuais iguais aos históricos | 57/57 |
| SHA-512 atuais iguais aos históricos | 57/57 |
| Tamanhos e leituras completas | 57/57 |
| BWEBs iguais ao SHA-512 oficial capturado em M6 | 56/56 |
| Fonte nacional: hashes locais atuais iguais aos históricos | 1/1 |
| Divergências / arquivos ausentes | 0 / 0 |
| Downloads ZIP / extrações / novas importações | 0 / 0 / 0 |

O relatório registra caminho relativo, bytes, horários, algoritmo/método,
digests históricos/atuais e resultado. Os fingerprints só ajudam a detectar
mudanças durante a leitura; não substituem a evidência atual de bytes.
O manifesto nacional histórico conserva `reused_local_fingerprint_cache`.

RR não é fonte ausente. A anomalia das duas entradas de catálogo que apontam
ao mesmo `.sha512` permanece preservada em M6 e no dossiê. A linha oficial
nomeia exatamente o ZIP; o digest coincide agora também com os bytes atuais.
Não foi consultada a URL inferida do ZIP nem feita essa afirmação.

## 2. Fonte nacional sem checksum e avaliação legítima

A política `tse-presidential-documented-provenance-1` exige cumulativamente:
catálogo oficial; aquisição documentada, aqui por testemunho do operador;
integridade local atual; ausência de referência nos endpoints examinados;
metadados oficiais coerentes; fontes BWEB com referência oficial cobrindo os
pares UF/turno; reconciliação completa das linhas selecionadas; integridades
matemática/referencial/estrutural; cobertura explícita e derivados preservados.

Não há exceção por dataset ID, UF ou ano. Teste com ano 2030 demonstra que a
metodologia independe da eleição atual; isso não habilita parsers de leiautes
futuros, que continuam restritos pelo importador. A via sem checksum é limitada
ao formato `section` relacionado aos BWEBs analisados. BWEB sem referência,
HTTP indisponível confundido com ausência, testemunho ausente, fontes extras,
hash divergente ou reconciliação incompleta são recusados.

O avaliador recalcula as condições a partir dos documentos vinculados, sem
confiar em flags `trusted`/`match`. As propostas M6 mantêm `trusted: false`.
A aprovação humana de referências e política passa a ser uma decisão explícita
separada, obrigatória no preflight, vinculada ao hash do dossiê e à política.
Não houve atribuição automática de confiança humana.

Resultados atuais:

| Dimensão | Resultado |
| --- | --- |
| SQLite, estrutura e referências internas | Aprovados no banco existente |
| Matemática | Aprovada, zero erros e totais indisponíveis |
| Reconciliação | 5.731.614 linhas e 998.411 pares seção/turno coincidentes, sem divergências |
| Relação por fonte | Somatórios das linhas selecionadas de cada formato coincidem com o total reconciliado e o banco |
| Cobertura territorial | 56 pares UF/turno, 27 UFs e ZZ, ambos os turnos |
| Integridade local atual | 57 SHA-256/SHA-512 coincidentes com a linhagem histórica |
| Referências externas | 56 BWEBs com SHA-512 oficial coincidente |
| Proveniência nacional sem checksum | Documentada e reconciliada no escopo presidencial |
| Completude exaustiva de seções | `not_assessed`, sem inventário independente |
| Assinatura/autenticação independente | `not_performed` |
| Nova `public_readiness` | `ready_for_declared_scope`, blockers vazios |
| Autorização de publicação | Ainda pendente |

A reconciliação de importação foi reutilizada com vínculo criptográfico ao
relatório histórico, entradas agora novamente hasheadas e banco inalterado.
Não se afirmou ter reprocessado os streams CSV. O banco foi revalidado e os
agregados JSON foram comparados por consultas independentes, somente leitura.
Os formatos oficiais pertencem ao mesmo TSE; não se afirma independência
institucional ou prova absoluta da legitimidade do processo eleitoral.

## 3. Release exclusivamente de metadados

Históricos preservados, sem sobrescrita:

- nacional: `data/processed/national-2026/releases/6305f74561d4687a23bd3054`;
- compacto original: `data/processed/embedded-presidential-2026/releases/e4e9c9cb5189ab5d4e124bfc`;
- seus ponteiros anteriores permanecem iguais.

Novo candidato local:
`data/processed/embedded-public-2026/releases/cf1a3b405d96fb5dd676f025`,
com ponteiro próprio em `data/processed/embedded-public-2026/current.json`.
Nenhum SQLite foi copiado ou reconstruído nessa release.

| Identidade | Valor |
| --- | --- |
| ID do conteúdo eleitoral, preservado | `e4e9c9cb5189ab5d4e124bfc` |
| Nova identidade da release de metadados | `cf1a3b405d96fb5dd676f025` |
| Manifesto original compacto | `c4dcddacb8092ff1dfffb35b07b739dbf360232e701e080087f52a4a09e20637` |
| Manifesto novo | `c1dd2ae876eecfd685d67bb5f53bb7efd223c8db5772a76a83b773b0da2a54e3` |
| Dossiê `provenance.json` | `2b1fadbd610cbe5bbb3be6084519f80a25fc8fd40c8b853c87b27f0652a07a53` |
| SQLite original, preservado | `c9eaefb7e02ab50d2922eb843715ea47346e9e60cf8d4f9c4a6f448c3b27fdc4` |

O ID dos dados não muda porque está dentro de cada JSON de resultados. Alterá-lo
exigiria mudar seus bytes. A identidade nova de metadados e o novo hash do
manifesto distinguem rigorosamente esta avaliação da fotografia anterior.

Foram preservados **31 artefatos anteriores**: 30 JSONs de resultados e
`validation.json`. O manifesto mudou legitimamente e adicionou a referência a
`provenance.json` (1.209.300 bytes). A minibase candidata tem 33 JSONs e
5.699.127 bytes. O dossiê inclui documentos exatos, inventário técnico/caminhos
históricos e evidências, sem ZIPs, SQLite ou dump de registros eleitorais por seção.
Seu hash e o novo manifesto são objetos da revisão humana.

A instalação no app verificou todos os artefatos e substituiu apenas o manifesto,
adicionando o dossiê. Os 45 arquivos históricos/geográficos acompanhados e os
31 artefatos instalados conservaram os hashes. Bruxelas, Trípoli, ausências por
turno, aptos, votos, comparecimento, abstenções e agregações permanecem iguais.
O alerta de cadastro TTE registrado em M6 continua uma ressalva documental,
sem ajuste silencioso de valores.

## 4. Gates e decisão formal

`validate_embedded` verifica a lista estrita de artefatos e os hashes, lê o dossiê
e rederiva a avaliação/manifesto. `build_metadata` expõe também a identidade de
metadados. `web_release.py` mantém todos os critérios anteriores e exige ainda
aprovação de proveniência com política/dossiê, revisor/data e ID de metadados
exatos. O bundle admite 33 arquivos para o dossiê validado, sem aceitar extras.

`web-data-approval.json` contém os valores preparados, mas ambas as decisões
continuam `approved: false`, sem revisor ou data inventados. A tag
`web-data-2026-v1` é proposta, não criada. O preflight retorna **2**, com motivo
de aprovação explícita de proveniência/política pendente. Os antigos blockers
técnicos deixaram de impedir o candidato novo; o histórico continua inalterado.

A revisão documental consolidou TSE CC BY (versão não explícita), Natural Earth
domínio público, IBGE com crédito e fundamento de reutilização de bases públicas,
e fatos do ato oficial TRE-DF. A complementação primária da Câmara está registrada;
não se exige assinatura inexistente, licença SPDX inventada ou contato novo com
o fornecedor como requisito técnico automático. A aceitação dessa fundamentação
e das ressalvas é decisão humana, detalhada no documento de aprovação, sem
pretensão de parecer jurídico formal.

## 5. Validação executada

| Verificação | Resultado |
| --- | --- |
| Pytest completo | 235 passed, 2 skipped, 376,25 s |
| Regressões finais de política/instalação/gate | 55 passed, 12,45 s; incluem oito testes adicionados após a coleta da suíte completa |
| Ruff | 45 arquivos, lint e formatação aprovados |
| Dart format do smoke alterado | Aprovado, zero mudanças |
| Build Web real, Flutter 3.47.8 | Aprovado, novo manifesto fixado por SHA-256 |
| Smoke Flutter real | 7 passed, mesmos totais eleitorais; prontidão esperada explicitamente `ready_for_declared_scope` |
| Browser Chromium real | 8 passed, 54,8 s; incluindo HTTP de todos os 33 JSONs, dispositivos e casos do exterior |
| Auditoria Web | 83 arquivos, 50.289.607 bytes, limites aprovados, `production_approved: false` |
| Preflight produção | Saída 2 esperada: falta aprovação humana vinculada |

Os dois skips são integrações oficiais opt-in, não lacunas da validação nacional
já realizada sobre o banco e a linhagem existente. A suíte completa mais as
regressões finais cobrem todos os testes Python atuais (243 aprovações distintas).
Não se repetiu importação nacional em teste; fixtures temporários são sintéticos.

Comandos centrais, além dos dois comandos de preparação no README:

```powershell
.venv\Scripts\python.exe -m pytest -q --basetemp=.local/m61/pytest-all
.venv\Scripts\python.exe -m pytest -q tests/test_metadata_install.py tests/test_documented_provenance.py tests/test_web_release.py --basetemp=.local/m61/pytest-metadata-gate-final
python apps/votoaberto_flutter/tool/embedded_build.py web --mode real --flutter .local/flutter/bin/flutter.bat --no-pub --no-wasm-dry-run
.local\flutter\bin\flutter.bat test test/real_embedded_smoke_test.dart --no-pub --dart-define=RUN_REAL_EMBEDDED=true --dart-define=EXPECTED_REAL_READINESS=ready_for_declared_scope
python apps/votoaberto_flutter/tool/web_release.py audit --mode real --report .local/m61/web-audit.json
python apps/votoaberto_flutter/tool/web_release.py preflight --source apps/votoaberto_flutter/assets/data/real
```

O smoke é executado dentro da pasta Flutter; `npm run test:browser --
--max-failures=1` também, com Chrome local e servidor Wrangler local. Logs em
`.local/m61`. A primeira tentativa de build sem caminho explícito não encontrou
o SDK; a primeira tentativa do smoke foi bloqueada pelo ambiente/telemetria.
O comando correto usa SDK instalado, telemetria desativada e runner local liberado.
Um teste inicial expôs o acoplamento indevido da política ao ano permitido pelo
parser; foi corrigido sem habilitar novos parsers. As execuções finais passaram.
Uma captura de stderr precisou explicitar UTF-8 no processo filho Windows;
o gate sempre retornou o bloqueio humano esperado.

Regressões cobrem hashes divergentes, nome/algoritmo/referência inválidos, ausência
de fonte/testemunho/dossiê, leitura incompleta, origens divergentes, HTTP insuficiente,
reconciliação/cobertura/matemática incompletas, fonte sem âncora, fixtures,
aprovação de outro dataset/hash/revisão, mistura de arquivos e rollback que
preserva edição concorrente. Aprovação humana não supera falha técnica.

## 6. Próxima ação mínima

O operador revisa e aceita/rejeita **uma decisão consolidada**, com referências,
política, testemunho, limitações, termos e IDs/hashes. Se aprovar explicitamente,
registrar os dois booleanos, revisor e data no arquivo preparado e executar
novamente o preflight/bundle. Não é necessário rehashear ZIPs ou refazer consultas
SQL para apenas assinar essa decisão sobre o candidato preservado.

A preparação da publicação e a autorização de deploy continuam etapas posteriores.
Nenhum workflow de deploy, Cloudflare, DNS, segredo, outro repositório ou variável
de habilitação foi alterado. Os commits são locais e organizados por implementação,
gate Web e evidência/documentação. A branch fica pronta para revisão.

Implementação/política: `418e1cb`. Gate e valores pendentes: `ba65a91`.
O commit documental seguinte registra esta entrega e as evidências. Conferir
`git log a983642..HEAD --oneline` e `git diff --stat a983642..HEAD` para a lista
completa, sem necessidade de incluir os JSONs gerados ou o SQLite no Git.
