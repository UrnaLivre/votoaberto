import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/features/elections/data/embedded_election_repository.dart';
import 'package:votoaberto/features/elections/data/mock_election_repository.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/elections/domain/election_repository.dart';
import 'package:votoaberto/features/elections/domain/geography.dart';
import 'package:votoaberto/features/explorer/presentation/explorer_controller.dart';

class FixtureBundle extends CachingAssetBundle {
  FixtureBundle({String root = 'assets/data/synthetic'}) {
    for (final file in Directory(
      root,
    ).listSync(recursive: true).whereType<File>()) {
      if (file.path.endsWith('.json')) {
        files[file.path.replaceAll('\\', '/')] = file.readAsBytesSync();
      }
    }
  }
  final files = <String, Uint8List>{};
  final calls = <String>[];
  void changeManifest(void Function(Map<String, dynamic>) mutate) {
    final value = jsonDecode(
      utf8.decode(files['assets/data/synthetic/manifest.json']!),
    ) as Map<String, dynamic>;
    mutate(value);
    files['assets/data/synthetic/manifest.json'] = Uint8List.fromList(
      utf8.encode(jsonEncode(value)),
    );
  }

  @override
  Future<ByteData> load(String key) async {
    calls.add(key);
    final bytes = files[key];
    if (bytes == null) throw StateError('Missing fixture asset: $key');
    return ByteData.sublistView(bytes);
  }
}

class PendingMunicipalRepository implements MunicipalElectionRepository {
  final requests = <String, Completer<List<MunicipalitySummary>>>{};
  @override
  Future<ElectionDataset> load(Election election) =>
      MockElectionRepository().load(election);
  @override
  Future<List<MunicipalitySummary>> loadMunicipalities(
    Election election,
    String territory,
  ) => (requests[territory] = Completer<List<MunicipalitySummary>>()).future;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  EmbeddedElectionRepository repository(
    FixtureBundle bundle, {
    int capacity = 3,
    String nature = 'synthetic',
  }) => EmbeddedElectionRepository(
    bundle: bundle,
    assetRoot: 'assets/data/synthetic',
    expectedNature: nature,
    cacheCapacity: capacity,
  );

  test('manifest, lazy per-UF assets, exact national/domestic/ZZ totals and textual codes', () async {
    final bundle = FixtureBundle();
    final repo = repository(bundle);
    final data = await repo.load(Election.presidential2026);
    expect(bundle.calls.any((key) => key.contains('municipalities/')), isFalse);
    expect(data.states.length, 27);
    expect(data.national.rounds[ElectionRound.first]!.totals.counted, 5600);
    expect(data.domestic!.rounds[ElectionRound.first]!.totals.counted, 5400);
    expect(data.overseas!.rounds[ElectionRound.first]!.totals.counted, 200);
    expect(data.overseas!.rounds[ElectionRound.second]!.totals.counted, 100);
    final cities = await repo.loadMunicipalities(
      Election.presidential2026,
      'SC',
    );
    expect(cities.first.municipality.code, '00001');
    expect(cities.first.municipality.name, 'São FICTÍCIO');
    expect(cities.first.rounds[ElectionRound.first]!.candidates.length, 3);
    expect(cities.first.rounds[ElectionRound.second]!.candidates.length, 2);
    expect(
      cities.first.rounds[ElectionRound.second]!.candidates.any(
        (c) => c.candidate.number == '33',
      ),
      isFalse,
    );
    await repo.loadMunicipalities(Election.presidential2026, 'SC');
    expect(
      bundle.calls
          .where((key) => key.endsWith('municipalities/SC.json'))
          .length,
      1,
    );
  });

  test('bounded LRU and cross-UF cache reuse', () async {
    final bundle = FixtureBundle();
    final repo = repository(bundle, capacity: 2);
    for (final code in ['AC', 'AL', 'AC', 'SP']) {
      await repo.loadMunicipalities(Election.presidential2026, code);
    }
    expect(repo.cachedTerritories, ['AC', 'SP']);
    expect(
      bundle.calls
          .where((key) => key.endsWith('municipalities/AC.json'))
          .length,
      1,
    );
  });

  for (final failure in ['schema', 'nature', 'version', 'missing']) {
    test('reject $failure with no fictional fallback', () async {
      final bundle = FixtureBundle();
      if (failure == 'schema') {
        bundle.changeManifest((m) => m['schema_version'] = 99);
      }
      if (failure == 'nature') {
        bundle.changeManifest((m) => m['data_nature'] = 'official-derived');
      }
      if (failure == 'version') {
        bundle.changeManifest((m) => m['validation'] = 'pending');
      }
      if (failure == 'missing') {
        bundle.files.remove('assets/data/synthetic/national.json');
      }
      final c = ExplorerController(
        repository(bundle),
        election: Election.presidential2026,
      );
      addTearDown(c.dispose);
      await c.load();
      expect(c.status, LoadStatus.error);
      expect(c.dataset, isNull);
    });
  }

  test(
    'corrupt municipality file fails hash verification; retry remains possible',
    () async {
      final bundle = FixtureBundle();
      final saved =
          bundle.files['assets/data/synthetic/municipalities/SC.json']!;
      bundle.files['assets/data/synthetic/municipalities/SC.json'] =
          Uint8List.fromList([1, 2, 3]);
      final repo = repository(bundle);
      await expectLater(
        repo.loadMunicipalities(Election.presidential2026, 'SC'),
        throwsA(isA<FormatException>()),
      );
      bundle.files['assets/data/synthetic/municipalities/SC.json'] = saved;
      expect(
        await repo.loadMunicipalities(Election.presidential2026, 'SC'),
        hasLength(2),
      );
    },
  );

  test('zero denominators are unavailable instead of zero percent', () {
    expect(
      CandidateResult(const Candidate('A', 'A'), 0).shareOfValid(0),
      isNull,
    );
    expect(
      VoteTotals(eligible: 0, valid: 0, blank: 0, invalid: 0).turnoutRate,
      isNull,
    );
  });

  test('partial and absent counts are not zero or complete participation', () {
    final t = VoteTotals(
      eligible: null,
      valid: 90,
      blank: null,
      invalid: 10,
      counted: 100,
      turnoutValue: null,
      abstentionValue: null,
      deriveParticipation: false,
      sections: 2,
      availableSections: const {'eligible': 0, 'turnout': 0, 'abstention': 0},
    );
    expect(t.eligible, isNull);
    expect(t.blank, isNull);
    expect(t.turnoutRate, isNull);
  });

  test(
    'late UF response cannot replace current municipality selection',
    () async {
      final repo = PendingMunicipalRepository();
      final c = ExplorerController(repo);
      addTearDown(c.dispose);
      await c.load();
      c.navigate(BrazilianState.ac, ResultMode.first, municipality: '00001');
      await Future<void>.delayed(Duration.zero);
      c.navigate(BrazilianState.sc, ResultMode.second, municipality: '00002');
      await Future<void>.delayed(Duration.zero);
      final sc = MunicipalitySummary(
        municipality: Municipality(
          code: '00002',
          name: 'SC FICTÍCIO',
          state: BrazilianState.sc,
        ),
        rounds: c.dataset!.states.first.rounds,
      );
      repo.requests['SC']!.complete([sc]);
      await Future<void>.delayed(Duration.zero);
      repo.requests['AC']!.completeError(StateError('old failure'));
      await Future<void>.delayed(Duration.zero);
      expect(c.municipality?.municipality.name, 'SC FICTÍCIO');
      expect(c.municipalStatus, LoadStatus.ready);
      expect(c.mode, ResultMode.second);
    },
  );
}
