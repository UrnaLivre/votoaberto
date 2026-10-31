import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:votoaberto/app/votoaberto_app.dart';
import 'package:votoaberto/features/elections/data/embedded_election_repository.dart';
import 'package:votoaberto/features/elections/domain/country.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/elections/domain/geography.dart';
import 'package:votoaberto/features/explorer/presentation/explorer_controller.dart';
import 'package:votoaberto/features/map/domain/brazil_geometry.dart';
import 'package:votoaberto/features/map/domain/geographic_catalog.dart';
import 'package:votoaberto/features/map/domain/world_geometry.dart';
import 'package:votoaberto/features/map/presentation/brazil_map.dart';
import 'package:votoaberto/features/map/presentation/world_map.dart';
import 'embedded_repository_test.dart'
    show FixtureBundle, PendingMunicipalRepository;
import 'country_evidence_test.dart' show registerCatalog, registerFixture;

GeographicCatalog fixtureGeography({bool partial = false}) => GeographicCatalog(
  sourceDatasetId:
      jsonDecode(
            File('assets/data/synthetic/manifest.json').readAsStringSync(),
          )['dataset_id']
          as String,
  locations: {
    'SC/00001': const MunicipalLocation(
      'SC',
      '00001',
      '9990001',
      -27,
      -50,
      'representative',
    ),
  },
  foreign: {
    '00001': const ForeignLocality(
      '00001',
      'US',
      'País fictício A',
      'verified_section_join',
    ),
    if (!partial)
      '00002': const ForeignLocality(
        '00002',
        'PT',
        'País fictício B',
        'verified_section_join',
      ),
  },
);

WorldGeometry fixtureWorld() => WorldGeometry.decode(
  jsonEncode({
    'type': 'FeatureCollection',
    'features': [
      for (final (iso, x) in [('US', -100), ('PT', -10), ('BR', -50)])
        {
          'type': 'Feature',
          'properties': {
            'iso': iso,
            'name':
                'País fictício ${iso == 'US'
                    ? 'A'
                    : iso == 'PT'
                    ? 'B'
                    : 'C'}',
          },
          'geometry': {
            'type': 'Polygon',
            'coordinates': [
              [
                [x, 20],
                [x + 8, 20],
                [x + 8, 28],
                [x, 28],
                [x, 20],
              ],
            ],
          },
        },
      {
        'type': 'Feature',
        'properties': {'iso': 'FJ', 'name': 'Ilhas fictícias'},
        'geometry': {
          'type': 'MultiPolygon',
          'coordinates': [
            [
              [
                [179, -18],
                [-179, -18],
                [-179, -16],
                [179, -16],
                [179, -18],
              ],
            ],
            [
              [
                [175, -20],
                [176, -20],
                [176, -19],
                [175, -19],
                [175, -20],
              ],
            ],
          ],
        },
      },
    ],
  }),
);

Future<void> openGeo(
  WidgetTester tester, {
  String location = '/mundo',
  Size size = const Size(1366, 900),
  bool partial = false,
  GeographicCatalog? geography,
}) async {
  final repo = EmbeddedElectionRepository(
    bundle: FixtureBundle(),
    assetRoot: 'assets/data/synthetic',
    expectedNature: 'synthetic',
  );
  await tester.runAsync(() async {
    await repo.load(Election.presidential2026);
    for (final uf in ['SC', 'ZZ']) {
      await repo.loadMunicipalities(Election.presidential2026, uf);
    }
  });
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    VotoAbertoApp(
      repository: repo,
      election: Election.presidential2026,
      initialLocation: location,
      geographicLoader: () async =>
          geography ?? fixtureGeography(partial: partial),
      worldLoader: () async => fixtureWorld(),
      geometryLoader: () async => BrazilGeometry.decode(
        File('assets/geo/br_states.geojson').readAsStringSync(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> tap(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

GoRouter router(WidgetTester tester) =>
    GoRouter.of(tester.element(find.byKey(const ValueKey('map-title'))));
String? title(WidgetTester tester) =>
    tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data;

void main() {
  testWidgets(
    'reviewed register activates countries and retains all three modes and deep links',
    (tester) async {
      await openGeo(
        tester,
        geography: registerCatalog(),
        location: '/mundo/PT?modo=1',
      );
      expect(title(tester), 'País fictício B');
      expect(tester.widget<WorldMap>(find.byType(WorldMap)).active, {
        'US',
        'PT',
      });
      expect(find.textContaining('Sem país confirmado'), findsNothing);
      router(tester).go('/mundo/US/localidade/00001?modo=2');
      await tester.pumpAndSettle();
      expect(title(tester), 'São FICTÍCIO');
      expect(tester.widget<WorldMap>(find.byType(WorldMap)).active, {'US'});
      router(tester).go('/mundo/US/localidade/00001?modo=comparacao');
      await tester.pumpAndSettle();
      expect(find.text('Entre um turno e outro'), findsOneWidget);
      await tap(tester, find.byKey(const ValueKey('geographic-back')));
      expect(title(tester), 'País fictício A');
      expect(
        router(tester).routeInformationProvider.value.uri.queryParameters,
        {'modo': 'comparacao'},
      );
    },
  );

  testWidgets(
    'register with missing or additional turn stays residual instead of duplicating votes',
    (tester) async {
      final data = registerFixture();
      final row = (data['localities'] as List)[0];
      row['verified_rounds'] = [1];
      (row['evidence'] as List).removeLast();
      await openGeo(
        tester,
        geography: registerCatalog(data),
        location: '/mundo/localidade/00001?modo=2',
      );
      expect(title(tester), 'São FICTÍCIO');
      expect(
        find.text('Outras localidades sem país confirmado (1)'),
        findsOneWidget,
      );
      expect(tester.widget<WorldMap>(find.byType(WorldMap)).selected, isNull);
      expect(tester.widget<WorldMap>(find.byType(WorldMap)).active, isEmpty);
    },
  );

  testWidgets(
    'legacy insights redirects to summary while retaining municipal deep link and round',
    (tester) async {
      await openGeo(
        tester,
        location: '/uf/SC/municipio/00001?turno=2&visao=insights',
      );
      expect(find.text('Explorar os Dados'), findsNothing);
      expect(find.byKey(const ValueKey('view-insights')), findsNothing);
      expect(title(tester), 'São FICTÍCIO');
      final uri = router(tester).routeInformationProvider.value.uri;
      expect(uri.path, '/uf/SC/municipio/00001');
      expect(uri.queryParameters, {'modo': '2'});
    },
  );

  testWidgets(
    'municipal marker zooms UF, persists map and omits unknown point',
    (tester) async {
      await openGeo(tester, location: '/uf/SC/municipio/00001');
      expect(find.byKey(const ValueKey('municipal-marker')), findsOneWidget);
      final map = tester.state(find.byType(BrazilMap));
      final painter =
          tester
                  .widget<CustomPaint>(
                    find.byKey(const ValueKey('brazil-map-paint')),
                  )
                  .painter!
              as BrazilMapPainter;
      expect(
        painter.viewport.world,
        painter.geometry.viewFor(BrazilianState.sc),
      );
      router(tester).go('/uf/SC/municipio/00002');
      await tester.pumpAndSettle();
      expect(tester.state(find.byType(BrazilMap)), same(map));
      expect(find.byKey(const ValueKey('municipal-marker')), findsNothing);
      expect(find.textContaining('Localização não confirmada'), findsOneWidget);
      expect(title(tester), 'Vila FICTÍCIA');
      await tap(tester, find.byKey(const ValueKey('back-uf')));
      expect(title(tester), 'Santa Catarina');
    },
  );

  testWidgets(
    'world highlights only observed countries for the selected round and preserves exterior total',
    (tester) async {
      await openGeo(tester);
      expect(title(tester), 'Mundo');
      WorldMap map() => tester.widget<WorldMap>(find.byType(WorldMap));
      expect(map().active, {'US', 'PT'});
      expect(map().active.contains('BR'), isFalse);
      expect(find.text('200'), findsOneWidget);
      await tap(tester, find.byKey(const ValueKey('mode-second')));
      expect(map().active, {'US'});
      expect(find.text('100'), findsOneWidget);
      expect(find.textContaining('ZZ'), findsNothing);
    },
  );

  testWidgets(
    'country pointer changes camera and panel; inactive country cannot be selected',
    (tester) async {
      await openGeo(tester);
      final f = find.byKey(const ValueKey('world-map-paint'));
      var painter = tester.widget<CustomPaint>(f).painter! as WorldMapPainter;
      final us = painter.geometry.countries.firstWhere((c) => c.iso == 'US');
      final br = painter.geometry.countries.firstWhere((c) => c.iso == 'BR');
      await tester.tapAt(
        tester.getTopLeft(f) + painter.viewport.toScreen(br.anchor),
      );
      await tester.pumpAndSettle();
      expect(title(tester), 'Mundo');
      await tester.tapAt(
        tester.getTopLeft(f) + painter.viewport.toScreen(us.anchor),
      );
      await tester.pumpAndSettle();
      expect(title(tester), 'País fictício A');
      painter = tester.widget<CustomPaint>(f).painter! as WorldMapPainter;
      expect(painter.viewport.world, painter.geometry.viewFor('US'));
      expect(
        router(tester).routeInformationProvider.value.uri.path,
        '/mundo/US',
      );
      await tap(tester, find.byKey(const ValueKey('show-municipalities')));
      await tap(tester, find.byKey(const ValueKey('municipality-00001')));
      expect(title(tester), 'São FICTÍCIO');
      expect(
        router(tester).routeInformationProvider.value.uri.path,
        '/mundo/US/localidade/00001',
      );
      await tap(tester, find.byKey(const ValueKey('geographic-back')));
      expect(title(tester), 'País fictício A');
      await tap(tester, find.byKey(const ValueKey('geographic-back')));
      expect(title(tester), 'Mundo');
      await tap(tester, find.byKey(const ValueKey('geographic-back')));
      expect(title(tester), 'Brasil');
    },
  );

  testWidgets(
    'legacy overseas links retain locality, round, view and public names',
    (tester) async {
      await openGeo(
        tester,
        location: '/uf/ZZ/municipio/00001?turno=2&visao=comparison',
      );
      expect(
        router(tester).routeInformationProvider.value.uri.path,
        '/mundo/localidade/00001',
      );
      expect(find.text('Entre um turno e outro'), findsOneWidget);
      expect(find.textContaining('ZZ'), findsNothing);
      expect(tester.widget<WorldMap>(find.byType(WorldMap)).selected, 'US');
      await tap(tester, find.byKey(const ValueKey('geographic-back')));
      expect(
        router(tester).routeInformationProvider.value.uri.path,
        '/mundo/US',
      );
    },
  );

  testWidgets(
    'foreign country/locality mismatch and absent round never fabricate votes',
    (tester) async {
      await openGeo(tester, location: '/mundo/US/localidade/00002?turno=2');
      expect(
        find.text(
          'Localidade eleitoral ou turno não disponível neste conjunto.',
        ),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('turnout-rate')), findsNothing);
      router(tester).go('/mundo/PT?turno=2');
      await tester.pumpAndSettle();
      expect(
        find.text(
          'Sem votação registrada para este país no turno selecionado.',
        ),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('turnout-rate')), findsNothing);
    },
  );

  testWidgets(
    'partial country view labels gaps, suppresses percentages and retains unmapped access',
    (tester) async {
      await openGeo(tester, partial: true, location: '/mundo/US');
      expect(find.textContaining('Agregação parcial'), findsOneWidget);
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('turnout-rate'))).data,
        'Indisponível',
      );
      router(tester).go('/mundo/localidade/00002');
      await tester.pumpAndSettle();
      expect(title(tester), 'Vila FICTÍCIA');
      expect(
        find.text('Outras localidades sem país confirmado (1)'),
        findsOneWidget,
      );
    },
  );

  for (final size in const [Size(390, 844), Size(768, 1024), Size(1366, 768)]) {
    testWidgets('world responsive layout and keyboard selection at $size', (
      tester,
    ) async {
      await openGeo(tester, size: size);
      final focus = find.ancestor(
        of: find.byType(WorldMap),
        matching: find.byType(Focus),
      );
      // Focus the map's own Focus widget using its descendant semantics.
      final node = Focus.of(
        tester.element(find.byKey(const ValueKey('world-map-paint'))),
      );
      node.requestFocus();
      await tester.pump();
      await tester.sendKeyEvent(LogicalKeyboardKey.enter);
      await tester.pumpAndSettle();
      expect(title(tester), 'País fictício A');
      expect(focus, findsWidgets);
      await tester.sendKeyEvent(LogicalKeyboardKey.escape);
      await tester.pumpAndSettle();
      expect(title(tester), 'Mundo');
      expect(tester.takeException(), isNull);
    });
  }

  test('antimeridian, multipart islands and inactive hit testing', () {
    final g = fixtureWorld();
    final view = g.viewFor('FJ');
    expect(view.width, lessThan(15));
    expect(g.hitTest(const Offset(179.5, 17), {'FJ'}), 'FJ');
    expect(g.hitTest(const Offset(-179.5, 17), {'FJ'}), 'FJ');
    expect(g.hitTest(const Offset(175.5, 19.5), {'FJ'}), 'FJ');
    expect(g.hitTest(const Offset(179.5, 17), {}), isNull);
  });

  test(
    'late exterior load cannot replace domestic selection or mix UF and country',
    () async {
      final repo = PendingMunicipalRepository();
      final c = ExplorerController(repo);
      addTearDown(c.dispose);
      await c.load();
      c.navigate(
        BrazilianState.sc,
        ResultMode.first,
        overseas: true,
        country: 'US',
      );
      await Future<void>.delayed(Duration.zero);
      expect(c.selected, isNull);
      c.navigate(BrazilianState.sc, ResultMode.comparison);
      await Future<void>.delayed(Duration.zero);
      repo.requests['ZZ']!.complete([]);
      repo.requests['SC']!.complete([]);
      await Future<void>.delayed(Duration.zero);
      expect(c.abroad, isFalse);
      expect(c.countryCode, isNull);
      expect(c.territoryCode, 'SC');
      expect(c.countries, isEmpty);
    },
  );

  test(
    'country aggregation retains missing fields, candidates and per-turn membership',
    () async {
      final repo = EmbeddedElectionRepository(
        bundle: FixtureBundle(),
        assetRoot: 'assets/data/synthetic',
        expectedNature: 'synthetic',
      );
      final locals = await repo.loadMunicipalities(
        Election.presidential2026,
        'ZZ',
      );
      final sum = aggregateLocalities(locals);
      final dataset = await repo.load(Election.presidential2026);
      for (final round in ElectionRound.values) {
        expect(
          sum[round]!.totals.counted,
          dataset.overseas!.rounds[round]!.totals.counted,
        );
        expect(
          sum[round]!.totals.availableSections,
          dataset.overseas!.rounds[round]!.totals.availableSections,
        );
        expect(
          sum[round]!.candidates.map((c) => c.votes),
          dataset.overseas!.rounds[round]!.candidates.map((c) => c.votes),
        );
      }
    },
  );
}
