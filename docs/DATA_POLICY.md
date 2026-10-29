# Fontes, licenciamento e proveniência dos dados

## Fontes primárias previstas

- [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/)
- [Resultados eleitorais (categoria)](https://dadosabertos.tse.jus.br/dataset/?groups=resultados)

Os conjuntos de **votação por seção**, **boletins de urna** e, se necessário, arquivos técnicos de totalização serão investigados separadamente. O recorte inicial é **presidente da República em 2026, ambos os turnos**, inclusive votação no exterior quando aplicável.

**Status:** o projeto ainda não importou, validou nem publicou um banco de resultados. Não há nesta árvore dados eleitorais oficiais processados.

## Regras para o pipeline de ingestão

1. Registrar cada recurso baixado: URL exata, título do conjunto, órgão, data da coleta, data/versão de publicação quando informada, tamanho em bytes e SHA-256 do arquivo efetivamente recebido.
2. Registrar separadamente hashes/metadados eventualmente publicados pelo próprio TSE e o algoritmo/formato empregado. **Hash igual confirma correspondência de bytes sob as premissas da fonte de comparação; não demonstra sozinho autenticidade eleitoral ou ausência de fraude.**
3. Manter os originais **imutáveis** fora do controle de versão; transformar em derivados com schemas, logs, parâmetros e versões reproduzíveis.
4. Importar apenas o cargo presidencial no banco de consulta, preservando a capacidade de voltar aos arquivos originais.
5. Reconciliar somas por turno e âmbito com os totais oficiais correspondentes, documentando faltas, duplicações, registros anulados/substituídos e exceções que o dataset revelar.
6. Documentar chaves compostas e a relação entre seção, boletim, urna/equipamento e eventuais contingências. Não assumir correspondência 1:1 sem confirmação documental.
7. Manter relatório de cobertura e divergências com estados explícitos: `verificado`, `pendente`, `sem dado`, `divergente`, `não aplicável` (com definições).
8. Para toda transformação estatística, registrar filtros, denominadores e metodologia.

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
