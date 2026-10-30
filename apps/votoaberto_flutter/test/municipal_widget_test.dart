import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/app/strings.dart';
import 'package:votoaberto/app/votoaberto_app.dart';
import 'package:votoaberto/features/elections/data/embedded_election_repository.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/map/domain/brazil_geometry.dart';

import 'embedded_repository_test.dart' show FixtureBundle;

Future<void> openMunicipal(
  WidgetTester tester, {
  String location = '/',
  bool officialPresentation = false,
  Size size = const Size(1366, 900),
}) async {
  final bundle = FixtureBundle();
  if (officialPresentation) {
    bundle.changeManifest((m) => m['data_nature'] = 'official-derived');
  }
  final repo = EmbeddedElectionRepository(
    bundle: bundle,
    assetRoot: 'assets/data/synthetic',
    expectedNature: officialPresentation ? 'official-derived' : 'synthetic',
  );
  await tester.runAsync(() async {
    await repo.load(Election.presidential2026);
    await repo.loadMunicipalities(Election.presidential2026, 'SC');
    await repo.loadMunicipalities(Election.presidential2026, 'ZZ');
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
      geometryLoader: () async => BrazilGeometry.decode(
        File('assets/geo/br_states.geojson').readAsStringSync(),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

void main() {
  for (final query in ['turno=3', 'visao=unknown']) {
    testWidgets('invalid deep-link filter is explicit: $query', (tester) async {
      await openMunicipal(tester, location: '/uf/SC?$query');
      expect(find.text('Este endereço não está disponível.'), findsOneWidget);
      expect(find.byKey(const ValueKey('turnout-rate')), findsNothing);
    });
  }
  testWidgets(
    'Brazil to UF to municipality, accent search, rounds, comparison and breadcrumbs',
    (tester) async {
      await openMunicipal(tester);
      await tester.enterText(find.byKey(const ValueKey('state-search')), 'SC');
      await tester.pumpAndSettle();
      await tapVisible(tester, find.byKey(const ValueKey('select-SC')));
      await tester.ensureVisible(
        find.byKey(const ValueKey('municipality-search')),
      );
      await tester.enterText(
        find.byKey(const ValueKey('municipality-search')),
        'sao ficticio',
      );
      await tester.pumpAndSettle();
      await tester.testTextInput.receiveAction(TextInputAction.search);
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
        'São FICTÍCIO',
      );
      await tapVisible(tester, find.byKey(const ValueKey('round-2')));
      await tapVisible(tester, find.byKey(const ValueKey('view-comparison')));
      expect(find.textContaining('Não disputa o 2º turno.'), findsOneWidget);
      await tapVisible(tester, find.byKey(const ValueKey('back-uf')));
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
        'Santa Catarina',
      );
      await tapVisible(tester, find.byKey(const ValueKey('back-brasil')));
      expect(find.text('EXPLORAÇÃO NACIONAL'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'invalid city is explicit and never another city or a zero result',
    (tester) async {
      await openMunicipal(tester, location: '/uf/SC/municipio/99999?turno=2');
      expect(
        find.text('Município ou turno não disponível neste conjunto.'),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('turnout-rate')), findsNothing);
    },
  );

  testWidgets('overseas locality absent in round two stays unavailable', (
    tester,
  ) async {
    await openMunicipal(tester, location: '/uf/ZZ/municipio/00002?turno=2');
    expect(find.text('VISÃO MUNICIPAL · ZZ'), findsOneWidget);
    expect(
      find.text('Município ou turno não disponível neste conjunto.'),
      findsOneWidget,
    );
    await tapVisible(tester, find.byKey(const ValueKey('round-1')));
    expect(find.byKey(const ValueKey('turnout-rate')), findsOneWidget);
  });

  testWidgets(
    'official presentation has local-preview provenance and no fictional banner',
    (tester) async {
      // Synthetic numbers exercise the presentation branch only; no real assets in CI.
      await openMunicipal(tester, officialPresentation: true);
      expect(find.text(AppStrings.demo), findsNothing);
      expect(find.textContaining('PRÉVIA LOCAL'), findsOneWidget);
      expect(
        find.textContaining('Brasil inclui os votos no exterior'),
        findsOneWidget,
      );
      await tapVisible(tester, find.byKey(const ValueKey('select-ZZ')));
      expect(find.text('VOTAÇÃO NO EXTERIOR · ZZ'), findsOneWidget);
      await tester.tap(find.byTooltip(AppStrings.methodology));
      await tester.pumpAndSettle();
      expect(
        find.textContaining('Prontidão pública: not_ready'),
        findsOneWidget,
      );
    },
  );

  for (final size in const [Size(390, 844), Size(768, 1024), Size(1366, 768)]) {
    testWidgets('municipal results and comparison without overflow at $size', (
      tester,
    ) async {
      await openMunicipal(
        tester,
        size: size,
        location: '/uf/SC/municipio/00001?turno=2&visao=comparison',
      );
      expect(find.text('VISÃO MUNICIPAL · SC'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.ensureVisible(find.text('Entre um turno e outro'));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'municipal search has accessible label, keyboard submission and empty feedback',
    (tester) async {
      final semantics = tester.ensureSemantics();
      try {
        await openMunicipal(tester, location: '/uf/SC');
        final finder = find.byKey(const ValueKey('municipality-search'));
        await tester.ensureVisible(finder);
        expect(
          tester.widget<TextField>(finder).decoration!.labelText,
          'Buscar município',
        );
        await tester.enterText(finder, 'nenhum');
        await tester.pumpAndSettle();
        expect(find.text('Nenhuma localidade encontrada.'), findsOneWidget);
        await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
      } finally {
        semantics.dispose();
      }
    },
  );
}
