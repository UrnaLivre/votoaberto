# Arquitetura de dados — VotoAberto e VotoAberto Auditor

> **Planejamento técnico (M2).** M1 tem apenas mock sintético. Nenhum ZIP oficial foi importado ou validado neste repositório.

## Visão geral

```text
       Fontes oficiais TSE (download externo ou ZIP local)
                            |
                      SHA-256 próprio
           + hash de referência oficial, se disponível
                            |
                    Inventário de fontes
                            |
                   VotoAberto Data Engine
     descoberta -> parsers -> filtros -> normalização
                -> reconciliação -> exportação
                    /                       \
          Perfil PUBLIC                    Perfil ANALYST
     SQLite compacto +                  Relatórios, consultas
     manifesto + relatório              e derivados completos
          |                               |
  Adaptador/API futuro            VotoAberto Auditor CLI
          |                       (Windows e Linux)
  VotoAberto Flutter
  (Windows/Web/Android)
```

**Motor único, dois perfis:** o processamento não é parte obrigatória do cliente Flutter. Windows/Web/Android não precisam baixar nem descompactar os ZIPs completos. O Auditor roda localmente e pode consumir arquivos originais do TSE para reprocessar e investigar.

## A fronteira entre os produtos

| | VotoAberto público | VotoAberto Auditor |
| --- | --- | --- |
| Usuário | cidadão, jornalista, pesquisador | analista, pesquisador, desenvolvedor |
| Plataforma pretendida | Windows/Web/Android | Windows/Linux (CLI primeiro) |
| Fonte operacional | base derivada compacta | arquivos oficiais completos fornecidos localmente |
| Escopo inicial | presidente 2026, 1º/2º turnos | importação por cargos/turnos configuráveis, na medida em que formatos forem implementados |
| Boletim de urna completo | **não** armazenado na base pública | pode ser aberto, analisado e cruzado com outros registros |
| Resultado detalhado por seção | sim, com procedência e limites | sim, inclusive campos adicionais conforme fonte |
| Objetivo | navegação, comparação, acesso fácil | inspeção de formatos, reconciliação, análises reproduzíveis |

### Campos lógicos do perfil público

A lista exata depende de inspeção dos arquivos reais.

- Contexto: eleição, ano, cargo, turno, UF/ZZ, município, zona, seção e quaisquer discriminadores exigidos pela fonte.
- Votos presidenciais por candidato, identificadores/número do candidato e totais da seção, **conforme o que as fontes permitirem calcular**.
- Votos brancos/nulos, aptos, comparecimento e abstenção quando a origem e o significado forem claros; sem substituir ausência de dado por zero.
- Origem, versão de fonte, hashes, registro de transformação, status de completude e de comparação com BU quando disponível.
- Tabelas/agregações para Brasil, UF e município, sempre compatíveis com os registros base; exterior tratado como abrangência própria e não como 28ª UF.

**Exclusão deliberada:** não armazenar integralmente o conteúdo original dos BUs, logs técnicos, demais cargos e arquivos brutos no banco público. Registros derivados de BU podem ser usados para confrontar a votação por seção e anotar o resultado da conferência sem copiar o documento inteiro.

### Campos e recursos do perfil analista

- Referência ou acesso local aos ZIPs originais e aos registros neles contidos; originais são imutáveis.
- Catálogo dos arquivos, estrutura interna, schemas por recurso, metadados, eventuais registros técnicos, erros de parsing e reconciliações.
- Consultas ad hoc e exportação para formatos analíticos, sem afirmar que qualquer campo indisponível nos dados pode ser inferido.
- Seleção por cargo/turno/abrangência, com validações específicas por origem. O uso de dados completos pode exigir espaço e processamento substanciais.

## Configuração prevista

Exemplo **ilustrativo**, não afirma que o comando ou o perfil já foram implementados:

```json
{
  "election_year": 2026,
  "offices": ["president"],
  "rounds": [1, 2],
  "territories": ["ALL"],
  "profile": "public",
  "input_dir": "data/raw",
  "output_dir": "data/processed"
}
```

**Padrão:** somente `president`, turnos `1,2`, `public`; `governor`, `senator` etc. só podem ser ativados após mapeamento e testes. Não aceitar configurações silenciosamente ignoradas.

## Etapas da importação

1. **Descobrir:** listar ZIPs e arquivos suportados, coletar nome, tamanho, última alteração, hash de conteúdo e referência oficial, quando fornecida e verificável.
2. **Inspecionar:** sem extrair em massa, listar os membros dos ZIPs e amostrar seus esquemas com limites de tempo/memória/bytes. Tratar extensões desconhecidas explicitamente, sem inventar parsers.
3. **Selecionar:** aplicar filtros por eleição/cargo/turno/território/arquivo com base em campos confirmados. Evitar assumir que o nome do ZIP é identificação suficiente.
4. **Interpretar:** streaming quando viável; decodificação, formatos, campos e exceções documentados. Não extrair entradas com path traversal; limitar tamanhos para evitar ZIP bombs.
5. **Normalizar:** preservar chaves oficiais como texto; guardar campo de origem e evento/versão quando necessário. Evitar coerção de identificadores e junções prematuras.
6. **Conferir:** somas e integridade, conflitos e duplicidades, cruzamento entre votação por seção e BU quando realmente possível. Separar ausência de evidência de divergência confirmada.
7. **Publicar:** construir em staging, gerar SQLite público com índices, manifesto de arquivo/esquema/filtros/hashes e relatório legível. Promover versão somente após validação; falhas deixam a versão anterior intacta.
8. **Limpar:** apagar arquivos temporários criados pelo processo, não excluir automaticamente ZIPs originais ou artefatos de proveniência necessários.

O importador deve ser **idempotente**, com retomada/checkpoint por fonte/partição quando a implementação assim permitir. Mudanças nas fontes ou filtros devem invalidar/recriar derivados afetados, não misturar resultados antigos.

## Interface de dados e versionamento

Começar com **SQLite como formato de entrega pública** para testar tamanho, índices e consultas locais. DuckDB/Parquet são opções de processamento e exportação analítica; não introduzir dependência deles sem necessidade. O backend/API da aplicação e uma eventual distribuição por arquivo serão definidos após medições.

O manifesto do dataset deve conter, no mínimo:

- Identificador e release da base, versão do esquema e versão do importador.
- Eleição/cargo/turnos/abrangências de fato incluídos.
- Relação de fontes e hashes calculados, hashes oficiais de referência com algoritmo/proveniência quando houver.
- SHA-256 dos artefatos derivados publicados, contagem de registros por nível, indicadores de cobertura e estado da validação.
- Metadados de atribuição/licença e explicação de limitações, sem afirmar atestação pelo TSE.

Manter distinção entre `synthetic`, `official-derived` e `unverified` e não promover bases incompletas a `validated`. Nenhum hash isolado equivale a assinatura digital.

## Organização pretendida

```text
apps/
  votoaberto_flutter/              # M1, não alterar por causa do importador
  votoaberto_auditor/              # CLI fina Windows/Linux, futura UX analítica
pipelines/
  tse_importer/                    # motor de ingestão, filtros, validadores e exportadores
    ...                           # estrutura interna decidida pelo Codex, testada
backend/                          # futura API
docs/
  DATA_ARCHITECTURE.md
  DATA_POLICY.md
  adr/0003-public-data-and-auditor.md
data/
  raw/                            # fora do Git; originais fornecidos pelo operador
  processed/                      # fora do Git; SQLite/Parquet/manifestos gerados
  samples/                        # fixtures pequenas e explicitamente sintéticas
```

A biblioteca de importação deve ser **independente da CLI** e o Auditor não deve duplicar lógica de parsing; ambos podem compartilhar modelos, validadores, filtros e exportadores.

## Critérios de aceitação do M2 inicial

- Não requer acesso às fontes reais para executar testes sintéticos.
- Com entrada local, inventaria e calcula hashes de ZIPs reais sem descompactar 4 GB de uma vez.
- Há limitação explícita para formatos ainda desconhecidos e geração de relatório de descoberta reprodutível.
- Configuração padrão seleciona somente presidente, ambos os turnos e perfil público.
- Testes de streaming/extrator seguro, codificação, identificadores com zeros e cálculos/reconciliação.
- Saída de exemplo SQLite + manifesto + relatório produzidos **somente** com fixtures sintéticas até que parsers oficiais estejam validados.
- Nenhum resultado sintético pode ser apresentado como oficial. O Flutter não deve ser alimentado por uma base real não conferida.
- Código e documentação preservam [nossa política de duas branches](WORKFLOW.md) e não adicionam dados brutos ao Git.

## Princípios de auditoria e interpretação

Os registros publicados pelo TSE, ainda que íntegros e matematicamente consistentes, têm limites informacionais. Um padrão anômalo pode demandar investigação, mas não prova fraude; uma conciliação de totais tampouco prova que todas as etapas de votação transcorreram corretamente. O sistema deve expor separadamente **observações**, **métodos**, **fontes** e **inferências**.
