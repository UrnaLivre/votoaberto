# VotoAberto Auditor

CLI local para o motor compartilhado em `pipelines/tse_importer`. Python 3.11+;
não depende do Flutter. Instalar na raiz: `python -m pip install '.[dev]'`.

Comandos: `votoaberto-auditor inventory|inspect|verify|plan|import|validate|report`.
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

Na versão 0.2.1, manifesto/relatório separam integridade física, referencial e
matemática de cobertura, hashes, reconciliação e prontidão pública. ALL permite
investigações parciais. `--require-territory NATIONAL --require-round 1
--require-round 2` exige presença dos 56 pares UF/ZZ × turno; não comprova
exaustividade das seções. `trusted` é declaração do operador sobre a referência.

[Critérios e caminhos da integração oficial](../../docs/DATA_ENGINE_OPERATIONS.md).

0.3.1 acrescenta preflight (`plan`), processamento sequencial por UF/turno e
política de disco padrão de 8 GiB adicionais com reserva livre de 15 GiB.
Temporários têm propriedade registrada; os anteriores nunca são apagados
automaticamente. [Importação nacional e recuperação](../../docs/NATIONAL_IMPORT.md).
