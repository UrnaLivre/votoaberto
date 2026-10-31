# VotoAberto Flutter — M4

Build e operação Web em produção: [WEB_DEPLOYMENT.md](../../docs/WEB_DEPLOYMENT.md).
O comando de publicação exige dados reais aprovados; fixtures são exclusivas do CI.

Consulta por Brasil/UF/município e exterior nos dois turnos. Modos explícitos:
`demo` (mock M1), `fixture` (JSON fictício do CI), `real` (JSON gerado localmente).
A prévia real preserva `public_readiness: not_ready`; dados reais ficam fora do Git.
[Operação, contrato, builds e limites offline](../../docs/EMBEDDED_DATA_MVP.md).
[Evidências M4](../../docs/M4_COMPLETION_REPORT.md).

```powershell
flutter pub get
flutter run -d windows
flutter run -d chrome
flutter test
```

Execução comum acima usa demo M1. Na raiz, para compilar com fixture ou dados reais:

```powershell
python apps/votoaberto_flutter/tool/embedded_build.py web --mode fixture
python apps/votoaberto_flutter/tool/embedded_build.py windows --mode real --source data/processed/embedded-presidential-2026
```

O wrapper valida schema/hashes/somas e seleciona exclusivamente os assets do modo.
Pastas municipais são declaradas explicitamente. Assets reais ausentes impedem
build real, sem fallback fictício. `--flutter` aceita caminho do SDK quando necessário.
Windows/Android consultam assets sem servidor; Web não garante offline após reiniciar
o navegador. Não há API de resultados, ZIPs ou SQLite no cliente. Cartografia:
[IBGE, origem e condições](../../docs/CARTOGRAPHY.md).
