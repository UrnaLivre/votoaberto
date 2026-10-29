# Pipelines — motor compartilhado (M2 planejado)

O M1 usa exclusivamente dados demonstrativos e não importa arquivos do TSE.

O próximo marco introduzirá `tse_importer/`, biblioteca Python independente da interface Flutter e reutilizada pela CLI do **VotoAberto Auditor**, para descoberta, inspeção, validação, filtros por cargo/turno, normalização e exportação.

**Padrão:** presidente, turnos 1 e 2, perfil de saída `public`. A saída pública conterá informação por seção e candidatos com proveniência, não BUs integrais. O perfil `analyst` trabalhará com os arquivos completos.

Não incluir ZIPs, CSVs oficiais volumosos, bancos processados, credenciais ou artefatos temporários no Git.

Decisões e critérios: [arquitetura de dados](../docs/DATA_ARCHITECTURE.md), [ADR 0003](../docs/adr/0003-public-data-and-auditor.md), [política de dados](../docs/DATA_POLICY.md).

