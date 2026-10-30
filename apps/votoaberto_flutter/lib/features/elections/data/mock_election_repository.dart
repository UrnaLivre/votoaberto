import '../domain/election.dart';
import '../domain/election_repository.dart';
import '../domain/geography.dart';

class MockElectionRepository implements ElectionRepository {
  static const provenance = DataProvenance(
    source: 'Gerador sintético VotoAberto (sem dados eleitorais do TSE)',
    version: 'mock-v1',
    synthetic: true,
    transformations:
        'Fórmulas inteiras determinísticas por índice alfabético de UF. '
        'Brasil = soma das 27 UFs; exterior não incluído.',
  );
  static const candidates = [
    Candidate('A', 'Candidato A'),
    Candidate('B', 'Candidato B'),
    Candidate('C', 'Candidato C'),
    Candidate('D', 'Candidato D'),
  ];

  @override
  Future<ElectionDataset> load(Election election) async {
    if (election.id != Election.demonstration.id) {
      throw UnsupportedError('Somente a eleição demonstrativa está disponível');
    }
    final states = [for (final state in BrazilianState.values) _state(state)];
    return ElectionDataset(
      election: election,
      provenance: provenance,
      states: states,
      national: NationalSummary({
        for (final round in ElectionRound.values)
          round: _aggregate(states, round),
      }),
    );
  }

  StateSummary _state(BrazilianState state) {
    final i = state.index;
    final eligible = 400000 + (i + 1) * 173521;
    return StateSummary(
      state: state,
      rounds: {
        for (final round in ElectionRound.values)
          round: _round(i, eligible, round),
      },
    );
  }

  RoundResult _round(int i, int eligible, ElectionRound round) {
    final second = round == ElectionRound.second;
    final turnout =
        eligible * (74 + i % 10 + (second ? (i % 5) - 2 : 0)) ~/ 100;
    final blank = turnout * (second ? 2 : 3) ~/ 100;
    final invalid = turnout * (3 + i % 3) ~/ 100;
    final valid = turnout - blank - invalid;
    final a = valid * (second ? 45 + i % 17 : 30 + i % 12) ~/ 100;
    final b = second ? valid - a : valid * (27 + i % 10) ~/ 100;
    final c = second ? 0 : valid * 18 ~/ 100;
    final votes = second ? [a, b] : [a, b, c, valid - a - b - c];
    return RoundResult(
      round: round,
      totals: VoteTotals(
        eligible: eligible,
        valid: valid,
        blank: blank,
        invalid: invalid,
      ),
      candidates: [
        for (var j = 0; j < votes.length; j++)
          CandidateResult(candidates[j], votes[j]),
      ],
    );
  }

  RoundResult _aggregate(List<StateSummary> states, ElectionRound round) {
    final results = states.map((s) => s.rounds[round]!).toList();
    int sum(int Function(VoteTotals) read) =>
        results.fold(0, (total, r) => total + read(r.totals));
    return RoundResult(
      round: round,
      totals: VoteTotals(
        eligible: sum((t) => t.eligible!),
        valid: sum((t) => t.valid),
        blank: sum((t) => t.blank!),
        invalid: sum((t) => t.invalid!),
      ),
      candidates: [
        for (final candidate in results.first.candidates)
          CandidateResult(
            candidate.candidate,
            results.fold(
              0,
              (total, result) =>
                  total +
                  result.candidates
                      .firstWhere(
                        (c) => c.candidate.id == candidate.candidate.id,
                      )
                      .votes,
            ),
          ),
      ],
    );
  }
}
