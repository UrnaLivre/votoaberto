import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/explorer/presentation/result_charts.dart';

const firstCandidate = Candidate(
  'first:11',
  'José FICTÍCIO',
  number: '11',
  sourceCandidateId: '000123',
);
const secondCandidate = Candidate(
  'second:11',
  'JOSE FICTICIO',
  number: '11',
  sourceCandidateId: '000123',
);

RoundResult result(
  ElectionRound round,
  Candidate candidate,
  int votes, {
  int? blank = 5,
  int? invalid = 5,
  Map<String, int> available = const {},
  List<Candidate> unreported = const [],
}) => RoundResult(
  round: round,
  totals: VoteTotals(
    eligible: 200,
    valid: votes,
    blank: blank,
    invalid: invalid,
    counted: votes + 10,
    turnoutValue: votes + 10,
    abstentionValue: 190 - votes,
    deriveParticipation: false,
    sections: 2,
    availableSections: available,
  ),
  candidates: [CandidateResult(candidate, votes)],
  unreportedCandidates: unreported,
);

Future<void> showComparison(
  WidgetTester tester,
  RoundResult first,
  RoundResult second,
) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: SingleChildScrollView(
          child: ComparisonChart(
            first: first,
            second: second,
            synthetic: false,
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  test(
    'comparison uses scoped number, not spelling or election-specific ID',
    () {
      expect(firstCandidate.comparisonKey, secondCandidate.comparisonKey);
      expect(firstCandidate.sameCandidateAs(secondCandidate), isTrue);
      const withoutSourceId = Candidate(
        'second:11',
        'Outra grafia',
        number: '11',
      );
      expect(firstCandidate.sameCandidateAs(withoutSourceId), isTrue);
      expect(withoutSourceId.sameCandidateAs(firstCandidate), isTrue);
    },
  );

  test(
    'conflicting official IDs or different numbers never establish equivalence',
    () {
      const conflicting = Candidate(
        'second:11',
        'José FICTÍCIO',
        number: '11',
        sourceCandidateId: '000456',
      );
      expect(firstCandidate.sameCandidateAs(conflicting), isFalse);
      expect(
        firstCandidate.sameCandidateAs(
          const Candidate('second:22', 'José FICTÍCIO', number: '22'),
        ),
        isFalse,
      );
    },
  );

  test('mock candidates without numbers retain their stable internal ID', () {
    const first = Candidate('demo-a', 'Grafia A');
    expect(
      first.sameCandidateAs(const Candidate('demo-a', 'Grafia B')),
      isTrue,
    );
    expect(
      first.sameCandidateAs(const Candidate('demo-b', 'Grafia A')),
      isFalse,
    );
  });

  testWidgets(
    'changed spelling remains a participating candidate in both rounds',
    (tester) async {
      await showComparison(
        tester,
        result(ElectionRound.first, firstCandidate, 90),
        result(ElectionRound.second, secondCandidate, 100),
      );
      expect(find.text('José FICTÍCIO'), findsOneWidget);
      expect(find.text('Dos válidos: 100,0% → 100,0%'), findsOneWidget);
      expect(find.textContaining('Não disputa'), findsNothing);
    },
  );

  testWidgets(
    'conflicting source IDs show unconfirmed identity, not nonparticipation',
    (tester) async {
      const conflicting = Candidate(
        'second:11',
        'Outra grafia',
        number: '11',
        sourceCandidateId: '000456',
      );
      await showComparison(
        tester,
        result(ElectionRound.first, firstCandidate, 90),
        result(ElectionRound.second, conflicting, 100),
      );
      expect(
        find.textContaining(
          'Correspondência de identidade entre turnos não confirmada.',
        ),
        findsNWidgets(2),
      );
      expect(find.textContaining('Não disputa'), findsNothing);
      expect(find.textContaining('Dos válidos:'), findsNothing);
    },
  );

  testWidgets(
    'unreported participant with changed spelling is not marked absent',
    (tester) async {
      await showComparison(
        tester,
        result(ElectionRound.first, firstCandidate, 90),
        result(
          ElectionRound.second,
          const Candidate('second:22', 'Outro FICTÍCIO', number: '22'),
          100,
          unreported: [secondCandidate],
        ),
      );
      expect(
        find.textContaining('Sem registro neste recorte do 2º turno.'),
        findsOneWidget,
      );
      expect(find.textContaining('Não disputa o 2º turno.'), findsNothing);
    },
  );

  testWidgets(
    'partial sums including explicit zero differ from wholly absent categories',
    (tester) async {
      const availability = {
        'eligible': 2,
        'turnout': 2,
        'abstention': 2,
        'valid': 2,
        'blank': 1,
        'null': 0,
      };
      await showComparison(
        tester,
        result(
          ElectionRound.first,
          firstCandidate,
          90,
          blank: 5,
          invalid: null,
          available: availability,
        ),
        result(
          ElectionRound.second,
          secondCandidate,
          100,
          blank: 0,
          invalid: null,
          available: availability,
        ),
      );
      expect(
        find.text(
          'Votos brancos: 5 · registros parciais → 0 · registros parciais. Comparação de totais completos indisponível.',
        ),
        findsOneWidget,
      );
      expect(
        find.text(
          'Votos nulos: Indisponível → Indisponível. Comparação indisponível.',
        ),
        findsOneWidget,
      );
      expect(find.textContaining('Votos brancos: Indisponível'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
}
