# Pipelines — motor compartilhado (M2)

O M1 usa exclusivamente dados demonstrativos e não importa arquivos do TSE.

O M2 implementa `tse_importer/`, biblioteca Python independente da interface Flutter e reutilizada pela CLI do **VotoAberto Auditor**, para descoberta, inspeção, validação, filtros por cargo/turno, normalização e exportação.

**Padrão:** presidente, turnos 1 e 2, perfil de saída `public`. A saída pública conterá informação por seção e candidatos com proveniência, não BUs integrais. O perfil `analyst` atual preserva o recorte presidencial normalizado de fontes completas; análises de todos os cargos continuam futuras.

Não incluir ZIPs, CSVs oficiais volumosos, bancos processados, credenciais ou artefatos temporários no Git.

Decisões e critérios: [arquitetura de dados](../docs/DATA_ARCHITECTURE.md), [ADR 0003](../docs/adr/0003-public-data-and-auditor.md), [política de dados](../docs/DATA_POLICY.md).


Instalação na raiz: `python -m pip install ".[dev]"`.
[CLI e operação](../docs/DATA_ENGINE_OPERATIONS.md) ·
[Investigação real de SC](../docs/TSE_2026_FORMAT_INVESTIGATION.md).
