import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/features/elections/data/mock_election_repository.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/elections/domain/election_repository.dart';
import 'package:votoaberto/features/elections/domain/geography.dart';
import 'package:votoaberto/core/formatters.dart';

void main() {
  late ElectionDataset data;
  setUp(
    () async =>
        data = await MockElectionRepository().load(Election.demonstration),
  );

  test('27 unique UFs, with DF and without ZZ', () {
    expect(BrazilianState.values.length, 27);
    expect(BrazilianState.values.map((s) => s.ibgeCode).toSet().length, 27);
    expect(BrazilianState.fromCode('df'), BrazilianState.df);
    expect(BrazilianState.fromCode('ZZ'), isNull);
    expect(
      data.states.map((s) => s.state).toSet(),
      BrazilianState.values.toSet(),
    );
  });

  test('every UF and both rounds reconcile exactly', () {
    for (final state in data.states) {
      expect(state.rounds.length, 2);
      for (final result in state.rounds.values) {
        final t = result.totals;
        expect(result.candidates.fold(0, (sum, c) => sum + c.votes), t.valid);
        expect(t.valid + t.blank + t.invalid, t.turnout);
        expect(t.abstention + t.turnout, t.eligible);
        expect(t.turnout, lessThanOrEqualTo(t.eligible));
        expect(t.turnoutRate + t.abstentionRate, closeTo(1, 1e-12));
        expect(
          result.candidates.fold(
            0.0,
            (sum, c) => sum + c.shareOfValid(t.valid),
          ),
          closeTo(1, 1e-12),
        );
        expect(
          result.candidates.length,
          result.round == ElectionRound.first ? 4 : 2,
        );
      }
    }
  });

  test('national totals and each candidate equal the sum of states', () {
    for (final round in ElectionRound.values) {
      final national = data.national.rounds[round]!;
      for (final read in <int Function(VoteTotals)>[
        (t) => t.eligible,
        (t) => t.turnout,
        (t) => t.abstention,
        (t) => t.valid,
        (t) => t.blank,
        (t) => t.invalid,
      ]) {
        expect(
          read(national.totals),
          data.states.fold(0, (sum, s) => sum + read(s.rounds[round]!.totals)),
        );
      }
      for (final c in national.candidates) {
        expect(
          c.votes,
          data.states.fold(
            0,
            (sum, s) =>
                sum +
                s.rounds[round]!.candidates
                    .firstWhere((item) => item.candidate.id == c.candidate.id)
                    .votes,
          ),
        );
      }
    }
  });

  test(
    'repository contract is deterministic and rejects unsupported election',
    () async {
      final ElectionRepository repository = MockElectionRepository();
      final next = await repository.load(Election.demonstration);
      expect(
        next.national.rounds[ElectionRound.second]!.totals.valid,
        data.national.rounds[ElectionRound.second]!.totals.valid,
      );
      expect(next.provenance.synthetic, isTrue);
      expect(() => next.states.clear(), throwsUnsupportedError);
      await expectLater(
        repository.load(
          const Election(id: 'official', year: 2026, office: Office.president),
        ),
        throwsUnsupportedError,
      );
    },
  );

  test('denominators and absolute/relative differences are explicit', () {
    expect(ratio(25, 100), .25);
    expect(ratio(0, 0), 0);
    expect(
      CandidateResult(const Candidate('A', 'A'), 20).shareOfValid(80),
      .25,
    );
    expect(const VoteChange(100, 125).absolute, 25);
    expect(const VoteChange(100, 125).relative, .25);
    expect(const VoteChange(100, 80).relative, -.2);
    expect(const VoteChange(0, 10).relative, isNull);
    expect(
      () => VoteTotals(eligible: 10, valid: 9, blank: 2, invalid: 0),
      throwsArgumentError,
    );
    expect(
      () => RoundResult(
        round: ElectionRound.first,
        totals: VoteTotals(eligible: 10, valid: 9, blank: 0, invalid: 0),
        candidates: [],
      ),
      throwsArgumentError,
    );
  });

  test(
    'electoral keys preserve zeros and additional source discriminators',
    () {
      final key = ElectoralLocationKey(
        electionId: '0001',
        round: 1,
        territoryCode: 'ZZ',
        municipalityCode: '00123',
        zoneCode: '0007',
        sectionCode: '0001',
        additional: {'event': '02'},
      );
      expect(key.electionId, '0001');
      expect(key.municipalityCode, '00123');
      expect(key.zoneCode, '0007');
      expect(key.sectionCode, '0001');
      expect(key.additional['event'], '02');
      expect(const ElectoralSection('0001').code, '0001');
    },
  );

  test('Brazilian formatting and accent-insensitive searches', () {
    expect(count(1234567), '1.234.567');
    expect(percent(.745), '74,5%');
    expect(normalizeSearch(' SÃO PAULO '), 'sao paulo');
    expect(normalizeSearch('Espírito Santo'), 'espirito santo');
  });
}
