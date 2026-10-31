import 'package:flutter/material.dart';
import '../../../core/formatters.dart';
import '../../elections/domain/election.dart';
import 'result_charts.dart';

/// Shared presentation of an existing round. No aggregation or missing-value substitution.
class RoundSummary extends StatelessWidget {
  const RoundSummary({
    super.key,
    required this.result,
    required this.synthetic,
    this.percentages = true,
    this.afterCounted,
  });
  final RoundResult result;
  final bool synthetic;
  final bool percentages;
  final Widget? afterCounted;

  @override
  Widget build(BuildContext context) {
    final t = result.totals;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Participação em números',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 20),
        Text(
          percent(percentages ? t.turnoutRate : null),
          key: const ValueKey('turnout-rate'),
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.w700,
          ),
        ),
        Text(
          'de comparecimento · ${_available(t, 'turnout', t.turnout)} eleitores',
        ),
        const SizedBox(height: 22),
        _metric(
          context,
          'Eleitores aptos',
          _available(t, 'eligible', t.eligible),
        ),
        _metric(
          context,
          'Abstenção',
          '${_available(t, 'abstention', t.abstention)} · ${percent(percentages ? t.abstentionRate : null)}',
        ),
        _metric(context, 'Votos contabilizados', count(t.counted)),
        ?afterCounted,
        _metric(context, 'Votos válidos', count(t.valid)),
        _metric(
          context,
          'Votos brancos',
          '${count(t.blank)}${t.blank != null && !t.complete('blank') ? ' · registros parciais' : ''}',
        ),
        _metric(
          context,
          'Votos nulos',
          '${count(t.invalid)}${t.invalid != null && !t.complete('null') ? ' · registros parciais' : ''}',
        ),
        const Divider(),
        Text(
          'Distribuição dos votos válidos',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 4),
        Text(
          synthetic
              ? 'Candidatos fictícios · % dos votos válidos'
              : percentages
              ? 'Candidatos · % dos votos válidos'
              : 'Candidatos · contagens associadas; percentuais indisponíveis',
          style: const TextStyle(fontSize: 12),
        ),
        const SizedBox(height: 20),
        DistributionChart(
          result: result,
          synthetic: synthetic,
          percentages: percentages,
        ),
        for (final candidate in result.unreportedCandidates)
          Text(
            '${candidate.number} · ${candidate.name}: sem registro de votos neste recorte.',
          ),
      ],
    );
  }

  Widget _metric(BuildContext context, String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: Wrap(
      alignment: WrapAlignment.spaceBetween,
      spacing: 16,
      runSpacing: 4,
      children: [
        Text(label),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
      ],
    ),
  );

  String _available(VoteTotals totals, String key, int? value) =>
      '${count(value)}${value != null && !totals.complete(key) ? ' · parcial' : ''}';
}
