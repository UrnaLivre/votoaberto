import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../../core/formatters.dart';
import '../../elections/domain/election.dart';

const _candidateColors = [
  Color(0xff5377ba),
  Color(0xff9a639b),
  Color(0xffb47736),
  Color(0xff5c8584),
];

class DistributionChart extends StatelessWidget {
  const DistributionChart({
    super.key,
    required this.result,
    this.synthetic = true,
  });
  final RoundResult result;
  final bool synthetic;
  @override
  Widget build(BuildContext context) => Column(
    children: [
      for (var i = 0; i < result.candidates.length; i++)
        _candidate(context, result.candidates[i], i),
    ],
  );

  Widget _candidate(BuildContext context, CandidateResult candidate, int i) {
    final share = candidate.shareOfValid(result.totals.valid);
    final colorIndex =
        (int.tryParse(candidate.candidate.number ?? '') ?? i) %
        _candidateColors.length;
    return Semantics(
      label:
          '${candidate.candidate.name}, ${count(candidate.votes)} votos${synthetic ? ' fictícios' : ''}, '
          '${percent(share)} dos válidos',
      child: ExcludeSemantics(
        child: Padding(
          padding: const EdgeInsets.only(bottom: 18),
          child: Column(
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: _candidateColors[colorIndex],
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${candidate.candidate.number == null ? '' : '${candidate.candidate.number} · '}${candidate.candidate.name}',
                    ),
                  ),
                  Text(
                    percent(share),
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(
                  value: share ?? 0,
                  minHeight: 7,
                  color: _candidateColors[colorIndex],
                  backgroundColor: Theme.of(
                    context,
                  ).colorScheme.surfaceContainerHighest,
                  stopIndicatorRadius: 0,
                ),
              ),
              const SizedBox(height: 5),
              Align(
                alignment: Alignment.centerRight,
                child: Text(
                  '${count(candidate.votes)} votos',
                  style: Theme.of(context).textTheme.labelSmall,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ComparisonChart extends StatelessWidget {
  const ComparisonChart({
    super.key,
    required this.first,
    required this.second,
    this.synthetic = true,
  });
  final RoundResult first;
  final RoundResult second;
  final bool synthetic;

  @override
  Widget build(BuildContext context) {
    int? complete(VoteTotals totals, String key, int? value) =>
        totals.complete(key) ? value : null;
    final metrics = <(String, int?, int?)>[
      (
        'Eleitores aptos',
        complete(first.totals, 'eligible', first.totals.eligible),
        complete(second.totals, 'eligible', second.totals.eligible),
      ),
      (
        'Comparecimento',
        complete(first.totals, 'turnout', first.totals.turnout),
        complete(second.totals, 'turnout', second.totals.turnout),
      ),
      (
        'Abstenção',
        complete(first.totals, 'abstention', first.totals.abstention),
        complete(second.totals, 'abstention', second.totals.abstention),
      ),
      ('Votos válidos', first.totals.valid, second.totals.valid),
      (
        'Votos brancos',
        complete(first.totals, 'blank', first.totals.blank),
        complete(second.totals, 'blank', second.totals.blank),
      ),
      (
        'Votos nulos',
        complete(first.totals, 'null', first.totals.invalid),
        complete(second.totals, 'null', second.totals.invalid),
      ),
    ];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '1º → 2º turno · contagem de votos/eleitores',
          style: TextStyle(fontSize: 12),
        ),
        const SizedBox(height: 16),
        for (final metric in metrics)
          _pair(context, metric.$1, metric.$2, metric.$3),
        const Divider(),
        Text(
          'Votação por candidato',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 16),
        for (final candidate in first.candidates) ...[
          if (second.candidates.any(
            (c) =>
                c.candidate.comparisonKey == candidate.candidate.comparisonKey,
          )) ...[
            _pair(
              context,
              candidate.candidate.name,
              candidate.votes,
              second.candidates
                  .firstWhere(
                    (c) =>
                        c.candidate.comparisonKey ==
                        candidate.candidate.comparisonKey,
                  )
                  .votes,
            ),
            Padding(
              padding: const EdgeInsets.only(bottom: 18),
              child: Text(
                'Dos válidos: ${percent(candidate.shareOfValid(first.totals.valid))} → '
                '${percent(second.candidates.firstWhere((c) => c.candidate.comparisonKey == candidate.candidate.comparisonKey).shareOfValid(second.totals.valid))}',
                style: Theme.of(context).textTheme.labelMedium,
              ),
            ),
          ] else
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Text(
                '${candidate.candidate.name}: ${count(candidate.votes)} votos no 1º turno '
                '(${percent(candidate.shareOfValid(first.totals.valid))} dos válidos). '
                '${second.unreportedCandidates.any((c) => c.comparisonKey == candidate.candidate.comparisonKey) ? 'Sem registro neste recorte do 2º turno.' : 'Não disputa o 2º turno.'}',
              ),
            ),
        ],
        for (final candidate in second.candidates.where(
          (c) => !first.candidates.any(
            (a) => a.candidate.comparisonKey == c.candidate.comparisonKey,
          ),
        ))
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Text(
              '${candidate.candidate.name}: ${count(candidate.votes)} votos no 2º turno. '
              '${first.unreportedCandidates.any((c) => c.comparisonKey == candidate.candidate.comparisonKey) ? 'Sem registro no recorte do 1º turno.' : 'Não disputa o 1º turno.'}',
            ),
          ),
      ],
    );
  }

  Widget _pair(BuildContext context, String label, int? a, int? b) {
    if (a == null || b == null) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 16),
        child: Text(
          '$label: ${count(a)} → ${count(b)}. Comparação indisponível.',
        ),
      );
    }
    final change = VoteChange(a, b);
    final maxValue = math.max(a, b);
    final colors = Theme.of(context).colorScheme;
    return Semantics(
      label:
          '$label: primeiro turno ${count(a)}, segundo turno ${count(b)}. '
          'Variação ${signedCount(change.absolute)}, ${signedPercent(change.relative)}.${synthetic ? ' Dados fictícios.' : ''}',
      child: ExcludeSemantics(
        child: Padding(
          padding: const EdgeInsets.only(bottom: 18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 7),
              _bar(context, '1º', a, maxValue, colors.primary),
              const SizedBox(height: 5),
              _bar(context, '2º', b, maxValue, colors.tertiary),
              const SizedBox(height: 7),
              Text(
                '${signedCount(change.absolute)} · ${signedPercent(change.relative)}',
                style: Theme.of(context).textTheme.labelMedium,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _bar(
    BuildContext context,
    String label,
    int value,
    int maximum,
    Color color,
  ) => Row(
    children: [
      Text(label, style: Theme.of(context).textTheme.labelSmall),
      const SizedBox(width: 8),
      Expanded(
        child: ClipRRect(
          borderRadius: BorderRadius.circular(2),
          child: LinearProgressIndicator(
            value: ratio(value, maximum),
            color: color,
            minHeight: 6,
            stopIndicatorRadius: 0,
            backgroundColor: Theme.of(
              context,
            ).colorScheme.surfaceContainerHighest,
          ),
        ),
      ),
      const SizedBox(width: 10),
      SizedBox(
        width: 90,
        child: Text(
          count(value),
          textAlign: TextAlign.right,
          style: Theme.of(context).textTheme.labelMedium,
        ),
      ),
    ],
  );
}
