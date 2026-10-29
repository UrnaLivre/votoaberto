# Importação presidencial nacional e controle de disco — 0.3.1

O motor e a CLI continuam independentes do Flutter. O perfil público contém
resultados presidenciais e proveniência, sem BUs completos. A investigação real
está em [TSE_2026_NATIONAL_INVESTIGATION.md](TSE_2026_NATIONAL_INVESTIGATION.md).

## Preparar e planejar

Preserve os originais fora do Git e da saída. O inventário percorre subpastas;
não infere cobertura pelo nome. `source_paths` permite escolher ZIPs explicitamente
por caminho relativo, sem copiá-los. Um ZIP inválido não é ignorado pelo filtro de
UF: corrija a entrada ou declare um conjunto parcial explícito e suas limitações.
SHA-512 divergente, ZIP inválido e schema desconhecido bloqueiam a importação.

Copie [national-2026.example.json](../config/national-2026.example.json) para uma
configuração local ignorada. Informe os caminhos reais. Caminhos JSON são relativos
à pasta da configuração; flags CLI substituem seus respectivos campos, com
caminhos relativos ao diretório de execução. Não versione caminhos pessoais.

```powershell
votoaberto-auditor plan --config .local/national.json --json .local/national-plan.json
# Piloto com os mesmos originais, somente AC no segundo turno:
votoaberto-auditor import --config .local/pilot.json --territory AC --round 2
# Após aceitar as fontes e fundamentar a projeção:
votoaberto-auditor import --config .local/national.json
votoaberto-auditor validate --dataset data/processed/national-2026
votoaberto-auditor report --dataset data/processed/national-2026 --json .local/national-report.json
```

O piloto usa uma saída temporária própria, não a saída canônica nacional. Seu JSON
precisa selecionar apenas os ZIPs necessários com `source_paths`, retirar a exigência
NATIONAL e manter somente o turno/UF do piloto. Nunca publicar o piloto como base
nacional. Em `plan`, amostras não comprovam todos os campos/linhas ou seções.
`input_eligible` indica aceitação preliminar das fontes; `national_load_allowed`
exige também projeção positiva que caiba no orçamento e na reserva livre.
O código de saída 0 de `plan` permite prosseguir ao piloto, não certifica a carga.

## Política explícita

```json
"storage": {
  "max_work_disk_bytes": 8589934592,
  "min_free_disk_bytes": 16106127360,
  "work_directory": ".work",
  "cleanup_policy": "owned",
  "retain_checkpoints": false,
  "retain_failed_diagnostics": true,
  "detailed_report_bytes": 8388608,
  "projected_peak_bytes": 0
}
```

8 GiB é o limite adicional da execução, incluindo a release final. 15 GiB é a
reserva livre. Não aumentar automaticamente. `projected_peak_bytes` é uma projeção
fundamentada no piloto, incluindo DBs simultâneos, journals, temporários e relatórios;
0 significa ainda não estimado e impede carga oficial com exigência NATIONAL.
Projeção maior que orçamento ou reserva disponível falha antes da criação dos DBs.
O envelope sem filtros de `plan` serve para dimensionar amplificação; não é uma
medição nem previsão calibrada. Distribuições e comprimentos podem variar por UF.

Flags de importação: `--max-work-disk-bytes`, `--min-free-disk-bytes`,
`--projected-peak-bytes`, `--work-directory`, `--cleanup-policy owned|retain`,
`--[no-]retain-checkpoints`, `--[no-]retain-failed-diagnostics`,
`--detailed-report-bytes`, `--source` repetível e `--inventory-cache`.
`work_directory` deve ser um único nome relativo dentro da saída. Entrada e saída
não podem se sobrepor; áreas com symlink/junction/reparse point são recusadas.

O guard mede arquivos visíveis, incluindo desconhecidos na área, a cada 100 ms e
em limites de SQL/lotes. Reserva crescimento antes dos lotes e uma margem de até
64 MiB. Usa também a perda de espaço livre do volume como estimativa conservadora
para temporários não enumeráveis: outras atividades do sistema podem inflar ou mascarar parte desse
delta, que não oferece atribuição exata. Os relatórios separam pico visível, pico contabilizado e espaço livre mínimo.
Isso **não é quota rígida do SO**, limite absoluto nem atribuição exata de toda
atividade do volume. Falta de margem interrompe o processamento; SQLite em curso
é interrompido pelo progress handler. Para isolamento rígido, use quotas do SO.

`TEMP`, `TMP` e `SQLITE_TMPDIR` são direcionados somente no processo para `tmp/` e
restaurados no fim. Execuções do motor no mesmo processo serializam essa alteração.
Não há alteração global da máquina. Na medição Windows foram observados temporários
SQLite `etilqs_*` nessa área. Arquivos abertos e já removidos podem não ser visíveis;
o delta de espaço livre ajuda a cobri-los. Bytes comprimidos efetivamente lidos pelo
SO não são medidos; o relatório informa bytes CSV descompactados até EOF, excluindo
sondagens de cabeçalho/PDF/índice, e distingue reutilização de checkpoints.

## Fluxo e amplificação

1. Inventariar e conferir hashes/referências; persistir o catálogo local de diagnóstico.
2. Ler cada CSV primário em fluxo uma vez, com índice de UF/turno.
3. Ler uma unidade BWEB; para cada UF/turno realmente contido, combinar com o recorte
   primário, projetar, reconciliar e incorporar em uma única base final de staging.
4. Remover a partição incorporada e o checkpoint BWEB redundante, salvo retenção explícita.
5. Conferir estrutura, matemática, referências, agregações e cobertura; recuperar
   páginas livres incrementalmente, evitando a cópia integral de `VACUUM`.
6. Gerar manifestos/relatórios, revalidar, mover a release e trocar `current.json`
   atomicamente no mesmo volume. A última operação é a atualização do ponteiro.

No perfil público, os registros intermediários retêm chaves, votos, contexto e
sentinelas necessários, com menos JSON técnico por linha. O contexto continua
derivado dos campos originais antes dessa redução. Perfil analyst mantém os campos
presidenciais selecionados. O código compara candidatos/eleições entre partições;
não escolhe metadados conflitantes silenciosamente.

O modo atual recusa BWEBs em **unidades separadas com UF/turno sobreposto**. Não
escolhe um arquivo arbitrariamente. Contextos múltiplos dentro de uma unidade
continuam sendo reconhecidos; não são somados. Para expandir a organização de
fontes, implementar agrupamento multifonte por partição antes de promovê-las.

## Propriedade, limpeza e recuperação

```text
national-2026/
  current.json
  releases/<release-id>/election.sqlite
                        manifest.json
                        validation.json
                        divergences-summary.json
                        divergences.jsonl
  .runs/<run-id>.json
  .work/<run-id>/staging/
                 checkpoints/
                 tmp/
```

O registro contém UUID, estado, chave de interpretação, arquivos e identidades
locais, arquivos removidos, bytes lógicos recuperados e métricas. Arquivos regulares
são criados exclusivamente. Limpeza verifica caminho canônico e identidade, sem
seguir links; `unlink` remove apenas caminhos reconhecidos, `rmdir` somente pastas
vazias. Arquivos desconhecidos/substituídos são contados e preservados. Não existe
limpeza recursiva genérica ou comando que apague originais.

Com `cleanup_policy: owned`, sucesso preserva release ativa/relatórios/registro e
elimina intermediários próprios. Falha/Ctrl+C preserva ponteiro anterior e elimina
SQLite incompleto próprio; diagnósticos essenciais e detalhe limitado são mantidos
conforme `retain_failed_diagnostics`. Falha ao trocar o ponteiro tenta retornar a
nova release sem referência ao staging de diagnóstico. `retain` conserva os arquivos
próprios para investigação, sempre contabilizados no orçamento.

`retain_checkpoints: true` permite retomada de unidades completas após falha.
O motor confere registro de propriedade, hash do DB e marcador transacional com
configuração/regras/versões. Parciais, DBs alterados e unidades de interpretação
antiga não são adotados. Versão nova invalida checkpoints M2 sem apagá-los.
`--no-resume` reprocessa unidades; uma release completa idêntica e íntegra continua
idempotente. Unidades reutilizadas de outra execução são somente lidas e nunca
limpas pela nova. Retenção pode aumentar bastante o consumo: não a habilite em
carga nacional sem recalcular a projeção e inventariar os artefatos retidos.

Após queda abrupta do processo/SO, a rotina `finally` pode não rodar: o lock e os
arquivos permanecem. Confirme que não há escritor ativo antes de remover **somente**
`.import.lock`. Inspecione `.runs` e checkpoints; propriedade incerta exige revisão
manual. Não excluir áreas antigas automaticamente. Tentativas normais removem os
DBs e staging vazios próprios; diagnósticos de falhas ficam limitados por execução,
podendo acumular conforme retenção. Inventarie antes da próxima carga; a ferramenta
não usa falha como autorização para limpar artefatos anteriores.

As métricas de `validation.json` são o retrato anterior à promoção/limpeza. O registro
`.runs/<run-id>.json` traz o estado ao final; os bytes do próprio registro mudam ao
gravá-lo e os tamanhos são lógicos, não blocos físicos alocados. `file_high_water_bytes`
não é uma soma simultânea: são máximos por arquivo. Comparações entre execuções
devem usar a definição de cada métrica e registrar atividades externas.

## Reconciliação, cobertura e confiança

`divergences-summary.json` contém contagens exatas por UF/turno e código para as
partições concluídas; `complete: false` identifica interrupção. Sem fonte BWEB,
agregar ocorrências em `bweb_source_absent`. Com fonte: `bweb_section_absent`,
`bweb_votable_absent`, `vote_difference`, `local_difference`, `ambiguous_bu`,
`ambiguous_bu_row`, `bu_mathematics`. A direção inversa usa `section_source_absent`,
`section_section_absent`, `section_votable_absent`. Uma ocorrência é um evento
de comparação, não necessariamente uma seção distinta. Sucessos ficam nos contadores
de reconciliação e em `comparison` do banco.

Detalhe sob demanda: ampliar `detailed_report_bytes` dentro do orçamento. O resumo
mantém o total mesmo com `detail.truncated: true` e `omitted_due_to_limit > 0`.
Ausência de fonte é sempre agregada. Registros inválidos/não suportados abortam;
não existe descarte silencioso ou quarentena permissiva. `quarantined_records: 0`
em importação concluída significa essa política estrita, não correção de registros.

NATIONAL exige presença dos 56 pares. `ALL` continua permitindo investigação
parcial. Presença territorial não comprova todas as seções. `territory_totals`
informa municípios, zonas, categorias e totais disponíveis com contagem de
indisponibilidade. Agregados incluem ZZ explicitamente; consultas em
[data_queries.sql](data_queries.sql). Campos sem linha não viram zero.

`inventory_cache` aceita catálogo do mesmo diretório com fingerprint de tamanho,
mtime, dispositivo e identidade. A opção é explícita; divergência recalcula os
hashes. Índice ZIP/referência atual são sempre reavaliados. Cache local pode ser
adulterado e fingerprint não prova imutabilidade dos bytes contra um agente hostil:
`hash_calculation` e `source_hashes.evidence` o distinguem de hash corrente, e seu uso
impede `public_readiness` pronto. Sem cache, calcular hashes atuais continua padrão.

Ausência de checksum oficial do CSV nacional permite análise local legítima com
limite declarado. SHA-256/SHA-512 são comparações de bytes, não assinaturas;
`trusted` é confiança atribuída pelo operador, nunca autenticação automática.
Não há relaxamento automático da política de prontidão pública, deploy ou conexão
com dados reais no Flutter.
