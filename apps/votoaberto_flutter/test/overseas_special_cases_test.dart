import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:votoaberto/app/votoaberto_app.dart';
import 'package:votoaberto/features/elections/data/embedded_election_repository.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/elections/domain/election_repository.dart';
import 'package:votoaberto/features/elections/domain/geography.dart';
import 'package:votoaberto/features/explorer/presentation/explorer_controller.dart';
import 'package:votoaberto/features/explorer/presentation/explorer_page.dart';
import 'package:votoaberto/features/explorer/presentation/overseas_special_case.dart';
import 'package:votoaberto/features/explorer/presentation/overseas_special_cases_dialog.dart';
import 'package:votoaberto/features/explorer/presentation/result_charts.dart';
import 'package:votoaberto/features/explorer/presentation/round_summary.dart';
import 'package:votoaberto/features/map/domain/brazil_geometry.dart';
import 'package:votoaberto/features/map/domain/geographic_catalog.dart';
import 'embedded_repository_test.dart' show FixtureBundle;
import 'geographic_explorer_test.dart' show fixtureWorld, tap;
import 'geographic_explorer_test.dart' as geo;

/// Code aliases exercise the real UI paths with small, explicitly fictional votes.
class SpecialFixtureRepository implements MunicipalElectionRepository {
  SpecialFixtureRepository(this.base, this.dataset, this.localities);
  final EmbeddedElectionRepository base;
  final ElectionDataset dataset;
  List<MunicipalitySummary> localities;
  Completer<List<MunicipalitySummary>>? pending;
  bool fail = false;
  @override
  Future<ElectionDataset> load(Election election) async => dataset;
  @override
  Future<List<MunicipalitySummary>> loadMunicipalities(
    Election election,
    String territory,
  ) async {
    if (territory != 'ZZ') return base.loadMunicipalities(election, territory);
    if (pending != null) return pending!.future;
    if (fail) throw StateError('Falha fictícia');
    return localities;
  }
}

Future<SpecialFixtureRepository> fixtureRepository() async {
  final base = EmbeddedElectionRepository(
    bundle: FixtureBundle(),
    assetRoot: 'assets/data/synthetic',
    expectedNature: 'synthetic',
  );
  final data = await base.load(Election.presidential2026);
  final zz = await base.loadMunicipalities(Election.presidential2026, 'ZZ');
  final cases = [
    for (var i = 0; i < 2; i++)
      MunicipalitySummary(
        municipality: Municipality(
          code: i == 0 ? '29432' : '30686',
          name: 'LOCALIDADE FICTÍCIA ${i + 1}',
          state: null,
          territoryCode: 'ZZ',
        ),
        rounds: zz[i].rounds,
      ),
  ];
  return SpecialFixtureRepository(base, data, cases);
}

GeographicCatalog specialGeography(SpecialFixtureRepository repo) =>
    GeographicCatalog(
      locations: const {},
      sourceDatasetId: repo.dataset.provenance.version,
      foreign: const {
        '29432': ForeignLocality(
          '29432',
          null,
          null,
          'conflicting_section_countries',
        ),
        '30686': ForeignLocality(
          '30686',
          null,
          null,
          'no_verified_section_join',
        ),
      },
    );

ExplorerController controller(WidgetTester tester) =>
    tester.widget<ExplorerPage>(find.byType(ExplorerPage)).controller;
GoRouter router(WidgetTester tester) =>
    GoRouter.of(tester.element(find.byKey(const ValueKey('map-title'))));
Finder get dialog => find.byType(OverseasSpecialCasesDialog);

Future<SpecialFixtureRepository> openSpecialApp(
  WidgetTester tester, {
  String location = '/mundo?modo=1',
  Size size = const Size(1366, 768),
  SpecialFixtureRepository? repository,
  bool settle = true,
}) async {
  final repo = repository ?? (await tester.runAsync(fixtureRepository))!;
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    VotoAbertoApp(
      repository: repo,
      election: Election.presidential2026,
      initialLocation: location,
      geographicLoader: () async => specialGeography(repo),
      worldLoader: () async => fixtureWorld(),
      geometryLoader: () async => BrazilGeometry.decode(
        File('assets/geo/br_states.geojson').readAsStringSync(),
      ),
    ),
  );
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));
  }
  return repo;
}

Future<void> openDialog(WidgetTester tester) =>
    tap(tester, find.byKey(const ValueKey('special-cases-open')));

void main() {
  for (final dark in [false, true]) {
    testWidgets(
      'dialog text contrast follows the existing ${dark ? 'dark' : 'light'} theme',
      (tester) async {
        final semantics = tester.ensureSemantics();
        await openSpecialApp(tester);
        if (dark) {
          controller(tester).toggleTheme();
          await tester.pumpAndSettle();
        }
        await openDialog(tester);
        await expectLater(tester, meetsGuideline(textContrastGuideline));
        semantics.dispose();
      },
    );
  }

  testWidgets(
    'large text, long candidate labels and large vote counts stay scrollable',
    (tester) async {
      final repo = (await tester.runAsync(fixtureRepository))!;
      final old = repo.localities[0];
      final long = RoundResult(
        round: ElectionRound.first,
        totals: VoteTotals(
          eligible: 9999999999999,
          valid: 1234567890123,
          blank: 0,
          invalid: 0,
        ),
        candidates: [
          CandidateResult(
            Candidate(
              'long-fictional',
              List.filled(14, 'NOME FICTÍCIO LONGO').join(' '),
            ),
            1234567890123,
          ),
        ],
      );
      repo.localities[0] = MunicipalitySummary(
        municipality: old.municipality,
        rounds: {...old.rounds, ElectionRound.first: long},
      );
      await openSpecialApp(
        tester,
        repository: repo,
        size: const Size(390, 844),
      );
      tester.platformDispatcher.textScaleFactorTestValue = 2;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await tester.pumpAndSettle();
      await openDialog(tester);
      await tester.drag(
        find.byKey(const PageStorageKey('special-scroll-29432')),
        const Offset(0, -1800),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      await tap(tester, find.byKey(const ValueKey('special-cases-close')));
    },
  );

  testWidgets(
    'demonstration without case codes never creates special entries',
    (tester) async {
      await geo.openGeo(tester);
      expect(find.byKey(const ValueKey('special-cases-open')), findsNothing);
      expect(find.text('Localidade eleitoral TSE 29432'), findsNothing);
      expect(find.text('Localidade eleitoral TSE 30686'), findsNothing);
    },
  );

  testWidgets(
    'ZZ loading and failure offer existing recovery without invented case results',
    (tester) async {
      final repo = (await tester.runAsync(fixtureRepository))!;
      repo.pending = Completer<List<MunicipalitySummary>>();
      await openSpecialApp(tester, repository: repo, settle: false);
      expect(controller(tester).municipalStatus, LoadStatus.loading);
      expect(find.byKey(const ValueKey('special-cases-open')), findsNothing);
      repo.fail = true;
      repo.pending!.completeError(StateError('Falha fictícia de leitura'));
      repo.pending = null;
      await tester.pumpAndSettle();
      expect(
        find.text('Não foi possível abrir as localidades eleitorais.'),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('special-cases-open')), findsNothing);
      repo.fail = false;
      await tap(tester, find.text('Tentar novamente'));
      expect(find.text('Casos especiais (2)'), findsOneWidget);
    },
  );

  testWidgets(
    'dialog handles loading, failure, absent locality and closing before late completion',
    (tester) async {
      final repo = await openSpecialApp(tester);
      await openDialog(tester);
      final c = controller(tester);
      c.municipalStatus = LoadStatus.error;
      c.notifyListeners();
      await tester.pumpAndSettle();
      expect(
        find.text('Não foi possível carregar os resultados desta localidade.'),
        findsOneWidget,
      );
      expect(
        find.descendant(of: dialog, matching: find.byType(RoundSummary)),
        findsNothing,
      );
      c.municipalStatus = LoadStatus.ready;
      c.municipalities = [repo.localities[1]];
      c.notifyListeners();
      await tester.pumpAndSettle();
      expect(
        find.text(
          'Localidade ausente ou indisponível neste conjunto consultado.',
        ),
        findsOneWidget,
      );
      repo.pending = Completer<List<MunicipalitySummary>>();
      c.navigate(null, c.mode, overseas: false);
      c.navigate(null, c.mode, overseas: true);
      await tester.pump();
      expect(find.text('Carregando resultados locais…'), findsWidgets);
      await tester.tap(find.byKey(const ValueKey('special-cases-close')));
      await tester.pump();
      repo.pending!.complete(repo.localities);
      repo.pending = null;
      await tester.pumpAndSettle();
      expect(dialog, findsNothing);
      expect(tester.takeException(), isNull);
      expect(controller(tester).municipalities, repo.localities);
    },
  );

  testWidgets(
    'unavailable metrics and partial valid denominator keep existing labels and suppress shares',
    (tester) async {
      final repo = (await tester.runAsync(fixtureRepository))!;
      final old = repo.localities[1];
      final source = old.rounds[ElectionRound.first]!;
      final t = source.totals;
      final unavailable = RoundResult(
        round: source.round,
        candidates: source.candidates,
        totals: VoteTotals(
          eligible: null,
          valid: t.valid,
          blank: null,
          invalid: null,
          counted: t.counted,
          deriveParticipation: false,
          sections: t.sections,
          availableSections: {
            'valid': 0,
            'blank': 0,
            'null': 0,
            'turnout': 0,
            'eligible': 0,
            'abstention': 0,
          },
        ),
        unreportedCandidates: [
          const Candidate(
            'fixture-unreported',
            'SEM REGISTRO FICTÍCIO',
            number: '98',
          ),
        ],
      );
      repo.localities[1] = MunicipalitySummary(
        municipality: old.municipality,
        rounds: {ElectionRound.first: unavailable},
      );
      await openSpecialApp(tester, repository: repo);
      await openDialog(tester);
      await tap(tester, find.byKey(const ValueKey('special-tab-30686')));
      expect(
        tester
            .widget<RoundSummary>(
              find.byKey(const ValueKey('special-result-30686-first')),
            )
            .result,
        same(unavailable),
      );
      expect(
        find.descendant(of: dialog, matching: find.text('Indisponível')),
        findsWidgets,
      );
      final chart = find.descendant(
        of: dialog,
        matching: find.byType(DistributionChart),
      );
      expect(
        find.descendant(of: chart, matching: find.text('—')),
        findsNWidgets(source.candidates.length),
      );
      expect(
        find.textContaining('SEM REGISTRO FICTÍCIO: sem registro de votos'),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('special-result-30686-second')),
        findsNothing,
      );
    },
  );

  testWidgets(
    'reduced motion, accessible chart labels and explicit close semantics',
    (tester) async {
      tester.platformDispatcher.accessibilityFeaturesTestValue =
          FakeAccessibilityFeatures(disableAnimations: true);
      addTearDown(
        tester.platformDispatcher.clearAccessibilityFeaturesTestValue,
      );
      final semantics = tester.ensureSemantics();
      await openSpecialApp(tester);
      await openDialog(tester);
      final tabController = tester.widget<DefaultTabController>(
        find.descendant(
          of: dialog,
          matching: find.byType(DefaultTabController),
        ),
      );
      expect(tabController.animationDuration, Duration.zero);
      expect(find.byTooltip('Fechar casos especiais'), findsOneWidget);
      final first = tester
          .widget<RoundSummary>(
            find.byKey(const ValueKey('special-result-29432-first')),
          )
          .result
          .candidates
          .first;
      expect(
        find.descendant(
          of: dialog,
          matching: find.byWidgetPredicate(
            (w) =>
                w is Semantics &&
                (w.properties.label ?? '').contains(first.candidate.name),
          ),
        ),
        findsWidgets,
      );
      await tester.tap(find.byKey(const ValueKey('special-tab-30686')));
      await tester.pump();
      expect(find.text('Localidade eleitoral TSE 30686'), findsOneWidget);
      semantics.dispose();
    },
  );

  testWidgets(
    'world action sits below Brazil, hides old coverage/list and stays independent of mode',
    (tester) async {
      await openSpecialApp(tester);
      final c = controller(tester);
      expect(c.specialCases, OverseasSpecialCase.values);
      expect(c.unmappedLocalities, hasLength(2));
      expect(find.textContaining('Cobertura por país parcial'), findsNothing);
      expect(find.text('Sem país confirmado (2)'), findsNothing);
      expect(find.textContaining('Outras localidades'), findsNothing);
      expect(
        tester.getTopLeft(find.byKey(const ValueKey('special-cases-open'))).dy,
        greaterThanOrEqualTo(
          tester
              .getBottomLeft(find.byKey(const ValueKey('geographic-back')))
              .dy,
        ),
      );
      for (final mode in ['2', 'comparacao', '1']) {
        router(tester).go('/mundo?modo=$mode');
        await tester.pumpAndSettle();
        expect(find.text('Casos especiais (2)'), findsOneWidget);
      }
      router(tester).go('/?modo=1');
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('special-cases-open')), findsNothing);
    },
  );

  testWidgets(
    'two tabs use repository rounds without changing votes, route, mode or main scroll',
    (tester) async {
      final repo = await openSpecialApp(
        tester,
        location: '/mundo?modo=comparacao',
      );
      final c = controller(tester);
      final beforeRoute = router(tester).routeInformationProvider.value.uri;
      final beforeTotals = c.dataset!.national.rounds;
      final beforeExterior = c.dataset!.overseas!.rounds;
      await openDialog(tester);
      final panelScroll = tester
          .state<ScrollableState>(
            find
                .descendant(
                  of: find.byKey(const ValueKey('panel-scroll')),
                  matching: find.byType(Scrollable),
                )
                .first,
          )
          .position
          .pixels;
      expect(
        find.descendant(of: dialog, matching: find.byType(Tab)),
        findsNWidgets(2),
      );
      expect(
        find.descendant(
          of: dialog,
          matching: find.byType(SegmentedButton<ResultMode>),
        ),
        findsNothing,
      );
      expect(
        find.descendant(of: dialog, matching: find.byType(ComparisonChart)),
        findsNothing,
      );
      expect(find.text('Localidade eleitoral TSE 29432'), findsOneWidget);
      expect(find.textContaining('Bélgica e em Luxemburgo'), findsOneWidget);
      final summary = tester.widget<RoundSummary>(
        find.byKey(const ValueKey('special-result-29432-first')),
      );
      expect(
        summary.result,
        same(repo.localities[0].rounds[ElectionRound.first]),
      );
      expect(
        tester
            .widget<RoundSummary>(
              find.byKey(const ValueKey('special-result-29432-second')),
            )
            .result,
        same(repo.localities[0].rounds[ElectionRound.second]),
      );
      expect(find.text('Resultados — 1º turno'), findsOneWidget);
      expect(find.text('Resultados — 2º turno'), findsOneWidget);
      expect(find.text('DEMONSTRAÇÃO · resultados fictícios'), findsOneWidget);
      expect(
        tester
            .widget<DistributionChart>(
              find
                  .descendant(
                    of: dialog,
                    matching: find.byType(DistributionChart),
                  )
                  .first,
            )
            .result
            .candidates,
        summary.result.candidates,
      );
      await tap(tester, find.byKey(const ValueKey('special-tab-30686')));
      expect(find.text('Localidade eleitoral TSE 30686'), findsOneWidget);
      expect(
        find.textContaining('administrativamente à Líbia'),
        findsOneWidget,
      );
      expect(find.textContaining('Túnis, na Tunísia'), findsOneWidget);
      expect(
        tester
            .widget<RoundSummary>(
              find.byKey(const ValueKey('special-result-30686-first')),
            )
            .result,
        same(repo.localities[1].rounds[ElectionRound.first]),
      );
      expect(
        find.byKey(const ValueKey('special-result-30686-second')),
        findsNothing,
      );
      expect(
        find.text(
          'Não há registro de resultados desta localidade para o 2º turno na base consultada.',
        ),
        findsOneWidget,
      );
      expect(c.mode, ResultMode.comparison);
      expect(c.municipalityCode, isNull);
      expect(router(tester).routeInformationProvider.value.uri, beforeRoute);
      expect(c.dataset!.national.rounds, same(beforeTotals));
      expect(c.dataset!.overseas!.rounds, same(beforeExterior));
      expect(c.unmappedLocalities, hasLength(2));
      expect(c.countries, isEmpty);
      await tap(tester, find.byKey(const ValueKey('special-cases-close')));
      expect(dialog, findsNothing);
      expect(router(tester).routeInformationProvider.value.uri, beforeRoute);
      expect(
        tester
            .state<ScrollableState>(
              find
                  .descendant(
                    of: find.byKey(const ValueKey('panel-scroll')),
                    matching: find.byType(Scrollable),
                  )
                  .first,
            )
            .position
            .pixels,
        panelScroll,
      );
      expect(FocusManager.instance.primaryFocus?.debugLabel, 'Casos especiais');
    },
  );

  testWidgets(
    'keyboard tab traversal, arrows and Escape leave map navigation untouched',
    (tester) async {
      await openSpecialApp(tester);
      await openDialog(tester);
      final close = find.byKey(const ValueKey('special-cases-close'));
      Focus.of(
        tester.element(
          find.descendant(of: close, matching: find.byType(Icon)).first,
        ),
      ).requestFocus();
      await tester.pump();
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.pumpAndSettle();
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowRight);
      await tester.pumpAndSettle();
      expect(find.text('Localidade eleitoral TSE 30686'), findsOneWidget);
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowLeft);
      await tester.pumpAndSettle();
      expect(find.text('Localidade eleitoral TSE 29432'), findsOneWidget);
      await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
      await tester.pump();
      expect(
        FocusManager.instance.primaryFocus?.context
            ?.findAncestorWidgetOfExactType<Dialog>(),
        isNotNull,
      );
      await tester.sendKeyEvent(LogicalKeyboardKey.escape);
      await tester.pumpAndSettle();
      expect(dialog, findsNothing);
      expect(controller(tester).abroad, isTrue);
      expect(FocusManager.instance.primaryFocus?.debugLabel, 'Casos especiais');
    },
  );

  for (final code in ['29432', '30686']) {
    testWidgets('previous deep link remains available: $code', (tester) async {
      final repo = await openSpecialApp(
        tester,
        location: '/mundo/localidade/$code?modo=1',
      );
      expect(
        controller(tester).municipality!.rounds,
        repo.localities
            .firstWhere((loc) => loc.municipality.code == code)
            .rounds,
      );
      expect(dialog, findsNothing);
      expect(find.byKey(const ValueKey('special-cases-open')), findsNothing);
    });
  }

  testWidgets(
    'future residual remains visible and accessible outside known cases',
    (tester) async {
      final repo = (await tester.runAsync(fixtureRepository))!;
      repo.localities = [
        ...repo.localities,
        MunicipalitySummary(
          municipality: Municipality(
            code: '99999',
            name: 'PENDÊNCIA FICTÍCIA',
            state: null,
            territoryCode: 'ZZ',
          ),
          rounds: const {},
        ),
      ];
      await openSpecialApp(tester, repository: repo);
      expect(find.text('Casos especiais (2)'), findsOneWidget);
      expect(controller(tester).unmappedLocalities, hasLength(3));
      final extra = find.text('Outras localidades sem país confirmado (1)');
      await tap(tester, extra);
      await tap(tester, find.widgetWithText(ListTile, 'PENDÊNCIA FICTÍCIA'));
      expect(
        router(tester).routeInformationProvider.value.uri.path,
        '/mundo/localidade/99999',
      );
    },
  );

  for (final dark in [false, true]) {
    for (final size in const [
      Size(1366, 768),
      Size(1920, 1080),
      Size(390, 844),
      Size(768, 1024),
      Size(280, 640),
    ]) {
      testWidgets('responsive modal, both tabs, dark=$dark at $size', (
        tester,
      ) async {
        await openSpecialApp(tester, size: size);
        if (dark) {
          controller(tester).toggleTheme();
          await tester.pumpAndSettle();
        }
        await openDialog(tester);
        for (final code in ['29432', '30686']) {
          await tap(tester, find.byKey(ValueKey('special-tab-$code')));
          expect(find.text('Localidade eleitoral TSE $code'), findsOneWidget);
          expect(tester.takeException(), isNull);
          final scroll = find.byKey(PageStorageKey('special-scroll-$code'));
          await tester.drag(scroll, const Offset(0, -1200));
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
        }
        expect(
          tester
              .getSize(find.byKey(const ValueKey('special-cases-surface')))
              .width,
          lessThanOrEqualTo(760),
        );
        await tap(tester, find.byKey(const ValueKey('special-cases-close')));
      });
    }
  }
}
