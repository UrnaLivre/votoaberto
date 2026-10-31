import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/app/strings.dart';
import 'package:votoaberto/app/votoaberto_app.dart';
import 'package:votoaberto/core/formatters.dart';
import 'package:votoaberto/features/elections/data/embedded_election_repository.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/map/domain/brazil_geometry.dart';

class LocalRealBundle extends CachingAssetBundle {
  final reads = <String>[];
  @override
  Future<ByteData> load(String key) async {
    reads.add(key);
    return ByteData.sublistView(await File(key).readAsBytes());
  }
}

void main() {
  const enabled = bool.fromEnvironment('RUN_REAL_EMBEDDED');
  TestWidgetsFlutterBinding.ensureInitialized();
  final metrics = <String, Object>{};
  tearDownAll(() {
    if (enabled) {
      final root = Directory('../../.local')..createSync(recursive: true);
      File(
        '${root.path}/m4-real-flutter-metrics.json',
      ).writeAsStringSync('${jsonEncode(metrics)}\n');
    }
  });
  EmbeddedElectionRepository repo(LocalRealBundle bundle) =>
      EmbeddedElectionRepository(
        bundle: bundle,
        assetRoot: 'assets/data/real',
        expectedNature: 'official-derived',
      );

  test(
    'real assets: M3 reference totals, lazy reads, geography and measured decoding',
    () async {
      final bundle = LocalRealBundle();
      final repository = repo(bundle);
      final clock = Stopwatch()..start();
      final data = await repository.load(Election.presidential2026);
      metrics['initial_dataset_debug_ms'] = clock.elapsedMicroseconds / 1000;
      expect(bundle.reads.where((p) => p.contains('municipalities/')), isEmpty);
      expect(data.provenance.synthetic, isFalse);
      expect(data.provenance.publicReadiness, 'not_ready');
      expect(
        data.national.rounds[ElectionRound.first]!.totals.valid,
        119306034,
      );
      expect(
        data.national.rounds[ElectionRound.second]!.totals.valid,
        124082273,
      );
      expect(
        data.national.rounds[ElectionRound.first]!.candidates,
        hasLength(13),
      );
      expect(
        data.national.rounds[ElectionRound.second]!.candidates,
        hasLength(2),
      );
      expect(
        data.national.rounds[ElectionRound.first]!.candidates
            .firstWhere((c) => c.candidate.number == '13')
            .votes,
        53879538,
      );
      expect(
        data.national.rounds[ElectionRound.second]!.candidates
            .firstWhere((c) => c.candidate.number == '22')
            .votes,
        59826041,
      );
      for (final uf in ['SP', 'AC', 'RS', 'SC', 'ZZ']) {
        clock.reset();
        final cities = await repository.loadMunicipalities(
          Election.presidential2026,
          uf,
        );
        metrics['${uf}_load_debug_ms'] = clock.elapsedMicroseconds / 1000;
        clock.reset();
        final matches = cities
            .where((c) => normalizeSearch(c.municipality.name).contains('sao'))
            .toList();
        metrics['${uf}_search_debug_ms'] = clock.elapsedMicroseconds / 1000;
        metrics['${uf}_search_matches'] = matches.length;
        expect(cities, isNotEmpty);
      }
    },
    skip: !enabled,
  );

  for (final scope in ['BR', 'SP', 'AC', 'RS', 'SC', 'ZZ']) {
    testWidgets('real UI $scope, both rounds and candidate percentages', (
      tester,
    ) async {
      final firstResultsClock = Stopwatch()..start();
      final repository = repo(LocalRealBundle());
      ElectionDataset? data;
      List<MunicipalitySummary> cities = const [];
      await tester.runAsync(() async {
        data = await repository.load(Election.presidential2026);
        if (scope != 'BR') {
          cities = await repository.loadMunicipalities(
            Election.presidential2026,
            scope,
          );
        }
        cities = cities.where((c) => c.rounds.length == 2).toList();
      });
      tester.view.physicalSize = const Size(1366, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final location = scope == 'BR'
          ? '/'
          : '/uf/$scope/municipio/${cities.first.municipality.code}';
      await tester.pumpWidget(
        VotoAbertoApp(
          repository: repository,
          election: Election.presidential2026,
          initialLocation: location,
          geometryLoader: () async => BrazilGeometry.decode(
            File('assets/geo/br_states.geojson').readAsStringSync(),
          ),
        ),
      );
      await tester.pumpAndSettle();
      metrics['${scope}_first_results_widget_debug_ms'] =
          firstResultsClock.elapsedMicroseconds / 1000;
      expect(find.text(AppStrings.demo), findsNothing);
      expect(find.textContaining('PRÉVIA LOCAL'), findsOneWidget);
      if (scope != 'BR') {
        expect(
          tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
          cities.first.municipality.name,
        );
      }
      for (final round in ElectionRound.values) {
        final roundClock = Stopwatch()..start();
        final chip = find.byKey(
          ValueKey(round == ElectionRound.first ? 'mode-first' : 'mode-second'),
        );
        await tester.ensureVisible(chip);
        await tester.tap(chip);
        await tester.pumpAndSettle();
        metrics['${scope}_round_${round.index + 1}_widget_debug_ms'] =
            roundClock.elapsedMicroseconds / 1000;
        final result = scope == 'BR'
            ? data!.national.rounds[round]!
            : cities.first.rounds[round]!;
        expect(
          find.text(
            percent(result.candidates.first.shareOfValid(result.totals.valid)),
          ),
          findsWidgets,
        );
        expect(tester.takeException(), isNull);
      }
      if (cities.length > 1) {
        final searchClock = Stopwatch()..start();
        final search = find.byKey(const ValueKey('municipality-search'));
        await tester.ensureVisible(search);
        await tester.enterText(search, cities[1].municipality.name);
        await tester.pumpAndSettle();
        metrics['${scope}_search_widget_debug_ms'] =
            searchClock.elapsedMicroseconds / 1000;
        final cityClock = Stopwatch()..start();
        await tester.testTextInput.receiveAction(TextInputAction.search);
        await tester.pumpAndSettle();
        metrics['${scope}_city_change_widget_debug_ms'] =
            cityClock.elapsedMicroseconds / 1000;
        expect(
          tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
          cities[1].municipality.name,
        );
      }
    }, skip: !enabled);
  }
}
