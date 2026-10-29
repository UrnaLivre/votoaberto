# VotoAberto Auditor

CLI local para o motor compartilhado em `pipelines/tse_importer`. Python 3.11+;
não depende do Flutter. Instalar na raiz: `python -m pip install '.[dev]'`.

Comandos: `votoaberto-auditor inventory|inspect|verify|import|validate|report`.
Cada um oferece `--help`; não há perguntas interativas nem downloads automáticos.

```powershell
votoaberto-auditor inspect --input "D:\TSE"
votoaberto-auditor import --input "D:\TSE" --output data/processed/sc --territory SC
votoaberto-auditor validate --dataset data/processed/sc
```

Presidente e ambos os turnos são padrão. `--synthetic` identifica fixtures;
`--profile analyst` mantém registros presidenciais das fontes para análise.

[Instalação, configuração, formatos, estados, segurança e retomada](../../docs/DATA_ARCHITECTURE.md).
[Inspeção e importação real de SC](../../docs/TSE_2026_FORMAT_INVESTIGATION.md).
