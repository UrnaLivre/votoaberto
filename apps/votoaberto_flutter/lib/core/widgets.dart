import 'package:flutter/material.dart';

import '../app/strings.dart';
import '../features/elections/domain/election.dart';

class SourceBanner extends StatelessWidget {
  const SourceBanner({super.key, required this.synthetic});
  final bool synthetic;
  @override
  Widget build(BuildContext context) => synthetic
      ? const DemoBanner()
      : Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: Theme.of(context).colorScheme.secondaryContainer,
          child: Text(
            'PRÉVIA LOCAL · Dados derivados do TSE · Verificação de origem limitada',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.labelMedium,
          ),
        );
}

class DemoBanner extends StatelessWidget {
  const DemoBanner({super.key});
  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Semantics(
      container: true,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        color: colors.tertiaryContainer,
        child: Text(
          AppStrings.demo,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: colors.onTertiaryContainer,
            fontWeight: FontWeight.w700,
            letterSpacing: 1,
          ),
        ),
      ),
    );
  }
}

class StatusMessage extends StatelessWidget {
  const StatusMessage({
    super.key,
    required this.message,
    this.onRetry,
    this.loading = false,
  });
  final String message;
  final VoidCallback? onRetry;
  final bool loading;
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (loading)
            const CircularProgressIndicator()
          else
            Icon(
              onRetry == null ? Icons.inbox_outlined : Icons.cloud_off_outlined,
              size: 36,
            ),
          const SizedBox(height: 16),
          Text(message, textAlign: TextAlign.center),
          if (onRetry != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: FilledButton(
                onPressed: onRetry,
                child: const Text('Tentar novamente'),
              ),
            ),
        ],
      ),
    ),
  );
}

Future<void> showMethodology(
  BuildContext context, {
  DataProvenance? provenance,
}) => showDialog<void>(
  context: context,
  builder: (context) => AlertDialog(
    title: const Text(AppStrings.methodology),
    content: SizedBox(
      width: 580,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              provenance == null || provenance.synthetic
                  ? AppStrings.demo
                  : 'Dados derivados do TSE · Prévia local de validação',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            SelectableText(
              provenance == null || provenance.version == 'mock-v1'
                  ? AppStrings.methodologyBody
                  : '${provenance.synthetic ? 'Fonte: fixture sintético para testes, sem resultados reais.' : 'Fonte: dados abertos do TSE · processamento independente pelo VotoAberto.'}\n\n'
                        '${provenance.transformations}\n\n'
                        'Versão: ${provenance.version}. Release de origem: ${provenance.sourceRelease}.\n'
                        'Prontidão pública: ${provenance.publicReadiness}. Esta instalação é uma prévia local, sem publicação pública aprovada.\n\n'
                        'Percentuais dos candidatos dividem pelos votos válidos. Comparecimento e abstenção dividem pelos aptos quando completos. '
                        'Totais parciais são identificados; valores indisponíveis não são zero. '
                        'As listas de candidatos e os aptos podem mudar entre turnos. ${AppStrings.interpretation}\n\n'
                        'SHA-256 compara bytes; não é assinatura nem certificação. VotoAberto é independente do TSE. '
                        'Malha de UFs: IBGE, Malhas Geográficas v3, simplificada; sem localização de equipamentos.',
            ),
            const SizedBox(height: 16),
            const SelectableText(AppStrings.geographicMethodology),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => showLicensePage(
          context: context,
          applicationName: AppStrings.title,
          applicationVersion: '0.5.0',
        ),
        child: const Text('Licenças de software'),
      ),
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Entendi'),
      ),
    ],
  ),
);
