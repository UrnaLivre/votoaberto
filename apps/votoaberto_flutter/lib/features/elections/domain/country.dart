import 'election.dart';

class CountrySummary {
  const CountrySummary(this.iso, this.name, this.localities, this.rounds);
  final String iso;
  final String name;
  final List<MunicipalitySummary> localities;
  final Map<ElectionRound, RoundResult> rounds;
}

/// Add only published fields; retain their section coverage and candidate set.
Map<ElectionRound, RoundResult> aggregateLocalities(
  Iterable<MunicipalitySummary> localities,
) {
  final result = <ElectionRound, RoundResult>{};
  for (final round in ElectionRound.values) {
    final rows = localities
        .map((loc) => loc.rounds[round])
        .whereType<RoundResult>()
        .toList();
    if (rows.isEmpty) continue;
    int? sum(int? Function(VoteTotals) metric) {
      final values = rows
          .map((r) => metric(r.totals))
          .whereType<int>()
          .toList();
      return values.isEmpty ? null : values.fold<int>(0, (a, b) => a + b);
    }

    final candidates = <String, CandidateResult>{};
    final catalog = <String, Candidate>{};
    for (final row in rows) {
      for (final c in row.unreportedCandidates) {
        catalog[c.id] = c;
      }
      for (final c in row.candidates) {
        catalog[c.candidate.id] = c.candidate;
        candidates[c.candidate.id] = CandidateResult(
          c.candidate,
          (candidates[c.candidate.id]?.votes ?? 0) + c.votes,
        );
      }
    }
    final available = <String, int>{};
    for (final key in [
      'counted',
      'valid',
      'blank',
      'null',
      'eligible',
      'turnout',
      'abstention',
    ]) {
      available[key] = rows.fold(
        0,
        (sum, r) =>
            sum +
            (r.totals.availableSections.isEmpty
                ? r.totals.sections
                : r.totals.availableSections[key] ?? 0),
      );
    }
    result[round] = RoundResult(
      round: round,
      electionId: rows.first.electionId,
      totals: VoteTotals(
        eligible: sum((t) => t.eligible),
        valid: sum((t) => t.valid)!,
        blank: sum((t) => t.blank),
        invalid: sum((t) => t.invalid),
        counted: sum((t) => t.counted),
        turnoutValue: sum((t) => t.turnout),
        abstentionValue: sum((t) => t.abstention),
        deriveParticipation: false,
        sections: rows.fold(0, (sum, r) => sum + r.totals.sections),
        availableSections: Map.unmodifiable(available),
      ),
      candidates: candidates.values.toList()
        ..sort((a, b) => a.candidate.id.compareTo(b.candidate.id)),
      unreportedCandidates: catalog.values
          .where((c) => !candidates.containsKey(c.id))
          .toList(),
    );
  }
  return Map.unmodifiable(result);
}
