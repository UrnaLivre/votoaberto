# Fontes, licenciamento e proveniência dos dados

## Fontes primárias

- [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/)
- [Resultados eleitorais (categoria)](https://dadosabertos.tse.jus.br/dataset/?groups=resultados)

Os conjuntos de **votação por seção**, **boletins de urna** e, se necessário, arquivos técnicos de totalização serão investigados separadamente. O recorte inicial é **presidente da República em 2026, ambos os turnos**, inclusive votação no exterior quando aplicável.

**Status M2:** primeira importação local de SC/presidente nos dois turnos executada,
com resultados e limites em [TSE_2026_FORMAT_INVESTIGATION](TSE_2026_FORMAT_INVESTIGATION.md).
Os originais e derivados reais não são versionados. M4 acrescenta prévia Flutter
local por JSONs derivados da base M3.1; a demonstração fictícia permanece separada.
Não há publicação remota. `public_readiness: not_ready` é preservado e apresentado
na metodologia.

## Regras para o pipeline de ingestão

1. Registrar cada recurso baixado: URL exata, título do conjunto, órgão, data da coleta, data/versão de publicação quando informada, tamanho em bytes e SHA-256 do arquivo efetivamente recebido.
2. Registrar separadamente hashes/metadados eventualmente publicados pelo próprio TSE e o algoritmo/formato empregado. **Hash igual confirma correspondência de bytes sob as premissas da fonte de comparação; não demonstra sozinho autenticidade eleitoral ou ausência de fraude.**
3. Manter os originais **imutáveis** fora do controle de versão; transformar em derivados com schemas, logs, parâmetros e versões reproduzíveis.
4. No **perfil público inicial**, importar somente **presidente de 2026, turnos 1 e 2**; no **perfil analista**, permitir filtros configuráveis por cargo/turno conforme parsers efetivamente suportados. Boletins completos não são copiados para o banco público; referências e valores presidenciais extraídos podem ser preservados com linhagem explícita.
5. Reconciliar somas por turno e âmbito com os totais oficiais correspondentes, documentando faltas, duplicações, registros anulados/substituídos e exceções que o dataset revelar.
6. Documentar chaves compostas e a relação entre seção, boletim, urna/equipamento e eventuais contingências. Não assumir correspondência 1:1 sem confirmação documental.
7. Manter relatório de cobertura e divergências com estados explícitos: `verificado`, `pendente`, `sem dado`, `divergente`, `não aplicável` (com definições).
8. Para toda transformação estatística, registrar filtros, denominadores e metodologia.
9. Não excluir automaticamente os ZIPs originais fornecidos pelo operador; limpar apenas temporários gerados pelo importador, após conferência e publicação válida dos derivados.
10. Exportar dados públicos de forma versionada e imutável, com manifesto dos hashes e relatório de cobertura; nunca promover uma importação incompleta ou falha como validada.

Aplicação no M2: promoção local de uma investigação parcial não é publicação pública
nem afirmação de completude. O manifesto v2 separa integridade física, matemática,
referencial, cobertura, hashes, reconciliação e prontidão. Confiança `trusted` é
atribuída pelo operador à referência; não autenticação automática da origem.
ALL seleciona o disponível; cobertura exigida usa contrato explícito. Estados e
limites no [guia operacional](DATA_ENGINE_OPERATIONS.md).

## Perfis de saída e separação de produtos

A arquitetura aprovada separa **VotoAberto público** (derivados presidenciais compactos, sem BUs integrais) de **VotoAberto Auditor** (processamento e investigação local de fontes completas). Um mesmo motor de importação configura cargo, turno e perfil. Consulte [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md) e [ADR 0003](adr/0003-public-data-and-auditor.md). A base pública é um derivado verificável; **não substitui as fontes originais**.

## Dados de demonstração

- **Exclusivamente sintéticos**, em arquivos pequenos de teste.
- Visualmente rotulados como **FICTÍCIOS** em toda tela, gráfico, exportação e captura criada pelo aplicativo.
- Sem mistura de valores demonstrativos com resultados reais.
- Casos de teste com inconsistências artificiais são permitidos, mas precisam ser rotulados como casos de teste.

## Licenças e atribuição

O código-fonte é disponibilizado sob a licença [MIT](../LICENSE), quando aplicável. **Isso não relicencia dados do TSE, cartografia, logos ou outros materiais de terceiros.**

Antes de redistribuir cada conjunto de dados, verificar os termos informados pelo **recurso específico** no portal oficial. Incluir, conforme exigido, atribuição do TSE, nome do conjunto, URL da origem, data de acesso, licença e eventuais alterações executadas. A cartografia deverá ter atribuição e licença verificadas separadamente.

## Limitações de interpretação

- Padrões incomuns e discrepâncias estatísticas são **hipóteses de investigação**, não evidência conclusiva de fraude.
- Tampouco a simples coincidência de totais é prova completa da integridade do processo.
- Dados oficiais publicados e registros internos de equipamentos são objetos distintos; a aplicação só pode mostrar o que a documentação efetivamente suporta.
- Não atribuir a eleitores individuais resultados ou comportamentos inferidos de agregados por seção.

## Organização local recomendada

```text
data/raw/          # ZIPs originais (não versionar)
data/processed/    # Parquet/SQLite/CSV derivados (não versionar)
data/cache/        # temporários (não versionar)
data/samples/      # pequenos fixtures sintéticos, versionáveis
```

Este repositório **não** pretende servir como espelho dos gigabytes de arquivos oficiais. A reprodutibilidade virá dos scripts, manifestos, documentação e links às fontes.

## Prévia municipal M4

Builds reais usam apenas JSONs agregados conferidos contra o SQLite existente,
com hashes, atribuição e limitações herdadas. Hashes da mini-base verificam o
pacote selecionado; não autenticam a origem do TSE.
`source_hashes_reused_from_local_cache` e `operator_trusted_hashes_incomplete`
continuam bloqueando prontidão pública. M4 não baixa/reimporta fontes nem muda
artificialmente confiança. Fixtures são fictícios e empacotados separadamente.
Assets reais ausentes ou incompatíveis impedem build real, sem fallback mock.
A licença MIT não é aplicada aos dados por essa conversão.
[Operação e atualização](EMBEDDED_DATA_MVP.md).
