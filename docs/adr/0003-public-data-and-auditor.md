# ADR 0003 — Uma cadeia de dados, dois produtos e perfis de exportação

- **Estado:** aceito; implementação inicial M2, com expansões pendentes.
- **Data:** 2026-10-29.
- **Produtos:** VotoAberto (consulta pública) e VotoAberto Auditor (análise local).
- **Decisão anterior relacionada:** [ADR 0002](0002-state-data-navigation.md).

## Contexto

O M1 entrega uma aplicação Flutter com dados inteiramente sintéticos. Os arquivos oficiais do TSE podem ocupar vários gigabytes, conter dados de diversos cargos, formatos e informações técnicas sem relevância para o cidadão que deseja consultar a eleição presidencial de 2026. Não é necessário, nem desejável, transferir todos os ZIPs ou BUs completos a cada instalação do VotoAberto.

Há duas demandas distintas: consulta rápida e simples a resultados, e reprodução aprofundada da importação e conferência das fontes originais.

## Decisão

1. **VotoAberto público:** Windows, Web e Android. Lê somente **conjuntos derivados compactos e versionados** com informações necessárias à consulta: eleição/turno, abrangência (UF ou ZZ, município, zona e seção), candidatos e votos, totais adequadamente definidos e metadados mínimos de proveniência/cobertura. Primeiro recorte: **presidente da República, 2026, primeiro e segundo turnos**, incluindo exterior quando presente nas fontes.
2. **Boletins de urna:** podem e devem ser considerados **fontes de conferência e extração** pelo pipeline, mas **não serão armazenados integralmente na base pública**. Publicar números extraídos de BUs somente com fonte, regra de associação e status de validação explícitos. Preservar referências que permitam consultar os originais, quando disponíveis.
3. **VotoAberto Auditor:** ferramenta de analista para Windows e Linux, inicialmente **CLI em Python**, capaz de trabalhar com os arquivos oficiais completos disponibilizados localmente, analisar metadados e produzir/conferir bases; interface gráfica é evolução opcional. Não declarar que ela prova a integridade de todo o processo eleitoral.
4. **Um único motor de importação:** componentes reutilizáveis de descoberta, leitura, filtros, normalização, validação e exportação, configurados por **cargo, turno, área e perfil de saída**. **Padrão: presidente, turnos 1 e 2, perfil público compacto.** Suporte a outros cargos será habilitado somente após inspeção de schemas e testes específicos, sem presumir que todo cargo existe em ambos os turnos.
5. **Independência do armazenamento:** o pipeline produz um artefato versionado e documentado, inicialmente **SQLite** para consumo local/teste de contrato, com manifesto e relatórios; analíticos podem usar DuckDB/Parquet internamente. API/backend e distribuição remota serão definidos após aferir tamanho/latência. Flutter deve continuar desacoplado do formato físico mediante o contrato `ElectionRepository`.
6. **Sem dados brutos no Git ou nos clientes comuns:** ZIPs integrais são obtidos do TSE ou apontados como arquivos locais; podem ser mantidos em arquivo histórico do operador. Arquivos temporários podem ser descartados **somente após** verificações e publicação bem-sucedida; o pipeline **nunca exclui automaticamente os originais fornecidos pelo usuário**.
7. **Versões transacionais:** um conjunto novo é preparado em staging, conferido e publicado como versão imutável apenas após validação. Uma falha não pode substituir a última versão íntegra, criar duplicações ou misturar turnos/estados de versões distintas.
8. **Reproduzibilidade e integridade:** hashes calculados de arquivos e hashes de referência oficiais, quando disponíveis, devem ter algoritmo e origem explícitos. SHA-256/SHA-512 **não são assinaturas digitais** nem certificação de regularidade. Atribuir termos/licença específicos a cada fonte, conforme publicados.

## Contrato de exportação: princípios

A forma física de saída será escolhida/ajustada após inspeção dos datasets TSE. O contrato lógico deve conter:

- Identificação da eleição, cargo, turno, abrangência, município/UF/ZZ, zona e seção quando aplicáveis; preservar códigos oficiais como **strings**, incluindo zeros à esquerda.
- Identificadores de candidato, votos nominais, votos brancos e nulos e demais totais **somente quando suportados pela fonte e com semântica documentada**.
- Linhagem da extração: recurso oficial, nome/hash do ZIP, identificador de registro, regras de transformação e status de correspondência BU × votação por seção.
- Controle de integridade referencial, completude/duplicidade, diferenças entre fontes e versão dos esquemas.
- Manifesto legível por máquina com versão do dataset, versão do esquema, filtros selecionados, arquivos produzidos e seus hashes; relatório de validação explicando limitações.

Não inventar campo oficial, chave 1:1 entre BU e equipamento, vínculo entre turnos da mesma urna, dados de eleitores individuais ou polígonos de zonas.

## Consequências

**Vantagens:** app público leve, importação reproduzível, canal aberto para pesquisadores, adição de cargos sem reescrever a pipeline e fronteiras de responsabilidade mais claras.

**Custos:** manutenção de contrato de exportação e versionamento, testes de migração e necessidade de arquivo histórico de fontes para reauditorias. Uma base pública resumida **não substitui** os arquivos originais; suas alegações precisam sempre mencionar os limites de conferência.

## Implementação por marcos

- **M2.1:** CLI, inventário e inspeção segura dos ZIPs, relatórios e proveniência; fixtures sintéticos; schema real ainda sob investigação.
- **M2.2:** filtros por cargo/turno, parsers por formato confirmado, SQLite compacto e manifestos versionados, testes de reconciliação e retomada segura.
- **M2.3:** testar com fontes oficiais locais e reconciliar totais; estudar distribuição/API e integração Flutter.
- **Futuro:** funcionalidades avançadas do Auditor sobre dados integrais, exportação alternativa para outros cargos, download automático e atualização baseada em manifestos assinados.

Esta decisão **não** autoriza substituir a base fictícia no Flutter por dados reais sem verificação e indicação inequívoca da fonte.

## Aplicação na implementação M2

As oito decisões acima e o contrato lógico provêm da main (`84e38c9`) e
continuam vinculantes. A branch M2 partiu de `37c066b`, anterior a esses registros;
o merge preserva o ADR da main e acrescenta evidências, sem substituir decisões.

O motor Python em `pipelines/tse_importer` é consumido pela CLI fina. Foram
confirmados BWEB/VOTACAO_SECAO 2026 e importado SC/presidente nos dois turnos.
PUBLIC não copia BUs completos; ANALYST mantém o recorte presidencial normalizado
e contexto selecionado, não todos os cargos. SQLite também serve como staging e
checkpoint transacional por membro; hashes de fonte/configuração/código/schema
inviabilizam retomada incompatível. DuckDB/Parquet não se mostraram necessários
na medição atual; continuam alternativas futuras.

Releases são locais e imutáveis, com current.json atômico após validação; isso
não faz deploy nem certifica prontidão pública. Chaves eleitorais são textuais;
contextos BWEB ambíguos não são somados nem identificam automaticamente equipamento
físico. Seções agregadas não são expandidas artificialmente; ausência não vira zero.
Somente presidente/2026 e situações confirmadas estão habilitados. O Flutter
e o contrato ElectionRepository permanecem intactos.

Detalhes: [operação](../DATA_ENGINE_OPERATIONS.md) e
[investigação](../TSE_2026_FORMAT_INVESTIGATION.md).

## Evolução M4

As decisões acima permanecem: SQLite é a base do motor e o cliente não recebe BUs
integrais. O [ADR 0004](0004-embedded-municipal-data.md) define o derivado JSON
municipal e o adaptador de assets, sem API ou SQLite no Flutter. O mock M1 fica
em modo separado. A prévia real local conserva a avaliação M3.1; não representa
autorização de distribuição pública.
