import 'geography.dart';

enum Office { president }

enum ElectionRound { first, second }

class Election {
  const Election({required this.id, required this.year, required this.office});
  final String id;
  final int year;
  final Office office;
  static const demonstration = Election(
    id: 'demo-presidential-2026',
    year: 2026,
    office: Office.president,
  );
}

class DataProvenance {
  const DataProvenance({
    required this.source,
    required this.version,
    required this.synthetic,
    required this.transformations,
    this.sourceUri,
    this.collectedAt,
    this.sha256,
  });
  final String source;
  final String version;
  final bool synthetic;
  final String transformations;
  final Uri? sourceUri;
  final DateTime? collectedAt;
  final String? sha256;
}

class Candidate {
  const Candidate(this.id, this.name);
  final String id;
  final String name;
}

class CandidateResult {
  CandidateResult(this.candidate, this.votes) {
    if (votes < 0) throw ArgumentError.value(votes, 'votes');
  }
  final Candidate candidate;
  final int votes;
  double shareOfValid(int validVotes) => ratio(votes, validVotes);
}

double ratio(num numerator, num denominator) =>
    denominator == 0 ? 0 : numerator / denominator;

class VoteTotals {
  VoteTotals({
    required this.eligible,
    required this.valid,
    required this.blank,
    required this.invalid,
  }) {
    if ([eligible, valid, blank, invalid].any((v) => v < 0) ||
        turnout > eligible) {
      throw ArgumentError('Totais de votação inconsistentes');
    }
  }
  final int eligible;
  final int valid;
  final int blank;
  final int invalid;
  int get turnout => valid + blank + invalid;
  int get abstention => eligible - turnout;
  double get turnoutRate => ratio(turnout, eligible);
  double get abstentionRate => ratio(abstention, eligible);
}

class RoundResult {
  RoundResult({
    required this.round,
    required this.totals,
    required List<CandidateResult> candidates,
  }) : candidates = List.unmodifiable(candidates) {
    if (candidates.fold(0, (sum, c) => sum + c.votes) != totals.valid ||
        candidates.map((c) => c.candidate.id).toSet().length !=
            candidates.length) {
      throw ArgumentError(
        'Votos válidos devem corresponder aos candidatos únicos',
      );
    }
  }
  final ElectionRound round;
  final VoteTotals totals;
  final List<CandidateResult> candidates;
}

class StateSummary {
  StateSummary({
    required this.state,
    required Map<ElectionRound, RoundResult> rounds,
  }) : rounds = Map.unmodifiable(rounds);
  final BrazilianState state;
  final Map<ElectionRound, RoundResult> rounds;
}

class NationalSummary {
  NationalSummary(Map<ElectionRound, RoundResult> rounds)
    : rounds = Map.unmodifiable(rounds);

  /// Covers the 27 domestic UFs only; no synthetic overseas electorate.
  final Map<ElectionRound, RoundResult> rounds;
}

class ElectionDataset {
  ElectionDataset({
    required this.election,
    required this.provenance,
    required List<StateSummary> states,
    required this.national,
  }) : states = List.unmodifiable(states);
  final Election election;
  final DataProvenance provenance;
  final List<StateSummary> states;
  final NationalSummary national;

  Map<ElectionRound, RoundResult>? results(BrazilianState? state) {
    if (state == null) return national.rounds;
    for (final summary in states) {
      if (summary.state == state) return summary.rounds;
    }
    return null;
  }
}

class VoteChange {
  const VoteChange(this.first, this.second);
  final int first;
  final int second;
  int get absolute => second - first;

  /// Undefined for a zero first-round baseline, rather than infinity or 0%.
  double? get relative => first == 0 ? null : absolute / first;
}

class BallotReportReference {
  const BallotReportReference({
    required this.location,
    required this.source,
    required this.provenance,
    this.recordId,
  });
  final ElectoralLocationKey location;
  final Uri source;
  final String? recordId;
  final DataProvenance provenance;
}
