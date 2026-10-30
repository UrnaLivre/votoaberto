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
  static const presidential2026 = Election(
    id: 'presidential-2026',
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
    this.publicReadiness = 'not_applicable',
    this.sourceRelease,
  });
  final String source;
  final String version;
  final bool synthetic;
  final String transformations;
  final Uri? sourceUri;
  final DateTime? collectedAt;
  final String? sha256;
  final String publicReadiness;
  final String? sourceRelease;
}

class Candidate {
  const Candidate(this.id, this.name, {this.number, this.sourceCandidateId});
  final String id;
  final String name;
  final String? number;
  final String? sourceCandidateId;
  String get comparisonKey => number == null ? id : '$number:$name';
}

class CandidateResult {
  CandidateResult(this.candidate, this.votes) {
    if (votes < 0) throw ArgumentError.value(votes, 'votes');
  }
  final Candidate candidate;
  final int votes;
  double? shareOfValid(int validVotes) =>
      validVotes == 0 ? null : ratio(votes, validVotes);
}

double ratio(num numerator, num denominator) =>
    denominator == 0 ? 0 : numerator / denominator;

class VoteTotals {
  VoteTotals({
    required this.eligible,
    required this.valid,
    required this.blank,
    required this.invalid,
    int? counted,
    int? turnoutValue,
    int? abstentionValue,
    bool deriveParticipation = true,
    this.sections = 1,
    this.availableSections = const {},
  }) {
    if (counted == null && (blank == null || invalid == null)) {
      throw ArgumentError('Total contabilizado indisponível');
    }
    this.counted = counted ?? valid + (blank ?? 0) + (invalid ?? 0);
    turnout = deriveParticipation ? this.counted : turnoutValue;
    abstention = deriveParticipation && eligible != null && turnout != null
        ? eligible! - turnout!
        : abstentionValue;
    if ([
          eligible,
          valid,
          blank,
          invalid,
          this.counted,
          turnout,
          abstention,
        ].whereType<int>().any((v) => v < 0) ||
        (eligible != null &&
            turnout != null &&
            complete('eligible') &&
            complete('turnout') &&
            turnout! > eligible!)) {
      throw ArgumentError('Totais de votação inconsistentes');
    }
  }
  final int? eligible;
  final int valid;
  final int? blank;
  final int? invalid;
  late final int counted;
  late final int? turnout;
  late final int? abstention;
  final int sections;
  final Map<String, int> availableSections;
  bool complete(String metric) =>
      availableSections.isEmpty || availableSections[metric] == sections;
  double? get turnoutRate =>
      eligible == null ||
          eligible == 0 ||
          turnout == null ||
          !complete('eligible') ||
          !complete('turnout')
      ? null
      : ratio(turnout!, eligible!);
  double? get abstentionRate =>
      eligible == null ||
          eligible == 0 ||
          abstention == null ||
          !complete('eligible') ||
          !complete('abstention')
      ? null
      : ratio(abstention!, eligible!);
}

class RoundResult {
  RoundResult({
    required this.round,
    required this.totals,
    required List<CandidateResult> candidates,
    this.electionId,
    this.unreportedCandidates = const [],
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
  final String? electionId;
  final List<Candidate> unreportedCandidates;
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

  /// Scope is explicit on ElectionDataset; real national totals include ZZ.
  final Map<ElectionRound, RoundResult> rounds;
}

class ElectionDataset {
  ElectionDataset({
    required this.election,
    required this.provenance,
    required List<StateSummary> states,
    required this.national,
    this.domestic,
    this.overseas,
  }) : states = List.unmodifiable(states);
  final Election election;
  final DataProvenance provenance;
  final List<StateSummary> states;
  final NationalSummary national;
  final NationalSummary? domestic;
  final NationalSummary? overseas;

  Map<ElectionRound, RoundResult>? results(BrazilianState? state) {
    if (state == null) return national.rounds;
    for (final summary in states) {
      if (summary.state == state) return summary.rounds;
    }
    return null;
  }
}

class MunicipalitySummary {
  MunicipalitySummary({
    required this.municipality,
    required Map<ElectionRound, RoundResult> rounds,
  }) : rounds = Map.unmodifiable(rounds);
  final Municipality municipality;
  final Map<ElectionRound, RoundResult> rounds;
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
