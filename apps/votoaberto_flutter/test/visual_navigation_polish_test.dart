import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/app/theme.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/elections/domain/geography.dart';
import 'package:votoaberto/features/explorer/presentation/explorer_page.dart';
import 'package:votoaberto/features/explorer/presentation/result_charts.dart';
import 'package:votoaberto/features/explorer/presentation/result_mode.dart';
import 'package:votoaberto/features/map/domain/brazil_geometry.dart';
import 'package:votoaberto/features/map/domain/world_geometry.dart';
import 'package:votoaberto/features/map/presentation/brazil_map.dart';
import 'package:votoaberto/features/map/presentation/map_controls.dart';
import 'package:votoaberto/features/map/presentation/world_map.dart';

import 'geographic_explorer_test.dart'
    show openGeo, router, title, tap, fixtureWorld;

ResultMode selectedMode(WidgetTester tester) => tester
    .widget<SegmentedButton<ResultMode>>(
      find.byKey(const ValueKey('result-mode')),
    )
    .selected
    .single;

void main() {
  for (final (query, expected) in [
    ('turno=1&visao=summary', ResultMode.first),
    ('turno=2&visao=summary', ResultMode.second),
    ('turno=1&visao=comparison', ResultMode.comparison),
    ('turno=2&visao=comparison', ResultMode.comparison),
    ('turno=1&visao=insights', ResultMode.first),
    ('turno=2&visao=insights', ResultMode.second),
    ('modo=1', ResultMode.first),
    ('modo=2', ResultMode.second),
    ('modo=comparacao', ResultMode.comparison),
  ]) {
    testWidgets('legacy and canonical URL preserve locality: $query', (
      tester,
    ) async {
      await openGeo(tester, location: '/mundo/US/localidade/00001?$query');
      final uri = router(tester).routeInformationProvider.value.uri;
      expect(uri.path, '/mundo/US/localidade/00001');
      expect(uri.queryParameters, {'modo': expected.queryValue});
      expect(selectedMode(tester), expected);
      expect(title(tester), 'São FICTÍCIO');
      // A second parse is stable and cannot start a redirect cycle.
      router(tester).go(uri.toString());
      await tester.pumpAndSettle();
      expect(router(tester).routeInformationProvider.value.uri, uri);
    });
  }

  test('invalid modes are rejected; canonical mode takes precedence', () {
    for (final query in [
      'modo=3',
      'modo=comparison',
      'turno=3',
      'visao=other',
    ]) {
      expect(ResultMode.fromQuery(Uri(query: query).queryParameters), isNull);
    }
    expect(
      ResultMode.fromQuery({'modo': 'comparacao', 'turno': '2'}),
      ResultMode.comparison,
    );
    expect(ResultMode.values, hasLength(3));
  });

  testWidgets('exactly three result choices work at every geographic scope', (
    tester,
  ) async {
    await openGeo(tester);
    for (final path in [
      '/',
      '/uf/SC',
      '/uf/SC/municipio/00001',
      '/mundo',
      '/mundo/US',
      '/mundo/US/localidade/00001',
    ]) {
      for (final mode in ResultMode.values) {
        router(tester).go('$path?modo=${mode.queryValue}');
        await tester.pumpAndSettle();
        final control = tester.widget<SegmentedButton<ResultMode>>(
          find.byKey(const ValueKey('result-mode')),
        );
        expect(control.segments.map((s) => s.value), ResultMode.values);
        expect(control.selected, {mode});
        expect(find.byType(ChoiceChip), findsNothing);
        expect(find.text('Resumo'), findsNothing);
        expect(find.text('Comparar'), findsNothing);
        if (mode == ResultMode.comparison) {
          final chart = tester.widget<ComparisonChart>(
            find.byType(ComparisonChart),
          );
          expect(chart.first.round, ElectionRound.first);
          expect(chart.second.round, ElectionRound.second);
          expect(find.byType(DistributionChart), findsNothing);
        } else {
          expect(
            tester
                .widget<DistributionChart>(find.byType(DistributionChart))
                .result
                .round,
            mode.round,
          );
          expect(find.byType(ComparisonChart), findsNothing);
        }
        expect(tester.takeException(), isNull);
      }
    }
  });

  testWidgets(
    'comparison uses both rounds regardless of previous choice; absent round stays absent',
    (tester) async {
      await openGeo(tester);
      for (final before in [ResultMode.first, ResultMode.second]) {
        router(tester).go('/mundo?modo=${before.queryValue}');
        await tester.pumpAndSettle();
        await tap(tester, find.byKey(const ValueKey('mode-comparison')));
        expect(tester.widget<WorldMap>(find.byType(WorldMap)).active, {
          'US',
          'PT',
        });
        expect(find.byType(ComparisonChart), findsOneWidget);
        expect(
          router(tester).routeInformationProvider.value.uri.queryParameters,
          {'modo': 'comparacao'},
        );
      }
      router(tester).go('/mundo/PT/localidade/00002?modo=comparacao');
      await tester.pumpAndSettle();
      expect(find.text('A comparação requer os dois turnos.'), findsOneWidget);
      expect(find.byType(ComparisonChart), findsNothing);
      expect(find.byType(DistributionChart), findsNothing);
    },
  );

  testWidgets(
    'map reset clears UF, municipality, country and locality at their own roots, in all modes',
    (tester) async {
      await openGeo(tester);
      for (final path in [
        '/uf/SC',
        '/uf/SC/municipio/00001',
        '/mundo/US',
        '/mundo/US/localidade/00001',
      ]) {
        for (final mode in ResultMode.values) {
          final world = path.startsWith('/mundo');
          router(tester).go('$path?modo=${mode.queryValue}');
          await tester.pumpAndSettle();
          final mapState = tester.state(
            find.byType(world ? WorldMap : BrazilMap),
          );
          final key = world ? 'world-map-reset' : 'map-reset';
          await tap(tester, find.byKey(ValueKey(key)));
          expect(
            router(tester).routeInformationProvider.value.uri.toString(),
            '${world ? '/mundo' : '/'}?modo=${mode.queryValue}',
          );
          expect(title(tester), world ? 'Mundo' : 'Brasil');
          expect(selectedMode(tester), mode);
          expect(
            tester.state(find.byType(world ? WorldMap : BrazilMap)),
            same(mapState),
          );
          expect(find.byKey(ValueKey(key)), findsNothing);
          expect(find.byKey(const ValueKey('municipal-marker')), findsNothing);
          final c = tester
              .widget<ExplorerPage>(find.byType(ExplorerPage))
              .controller;
          expect(c.selected, isNull);
          expect(c.countryCode, isNull);
          expect(c.municipalityCode, isNull);
          expect(
            c.results,
            world ? c.dataset!.overseas!.rounds : c.dataset!.national.rounds,
          );
          if (world) {
            final painter =
                tester
                        .widget<CustomPaint>(
                          find.byKey(const ValueKey('world-map-paint')),
                        )
                        .painter!
                    as WorldMapPainter;
            expect(painter.viewport.world, WorldGeometry.bounds);
          } else {
            final painter =
                tester
                        .widget<CustomPaint>(
                          find.byKey(const ValueKey('brazil-map-paint')),
                        )
                        .painter!
                    as BrazilMapPainter;
            expect(painter.viewport.world, painter.geometry.viewFor(null));
          }
          // The retained map can zoom again after clearing selection.
          router(tester).go('$path?modo=${mode.queryValue}');
          await tester.pumpAndSettle();
          expect(find.byKey(ValueKey(key)), findsOneWidget);
        }
      }
    },
  );

  testWidgets(
    'Brazil and World have independent clickable breadcrumbs and coherent switching actions',
    (tester) async {
      await openGeo(
        tester,
        location: '/mundo/US/localidade/00001?modo=comparacao',
      );
      expect(find.byKey(const ValueKey('breadcrumb-brasil')), findsNothing);
      expect(find.byKey(const ValueKey('breadcrumb-mundo')), findsOneWidget);
      expect(find.byKey(const ValueKey('breadcrumb-country')), findsOneWidget);
      expect(find.byKey(const ValueKey('breadcrumb-locality')), findsOneWidget);
      expect(find.text('Voltar ao Brasil'), findsNothing);
      await tap(tester, find.byKey(const ValueKey('breadcrumb-country')));
      expect(title(tester), 'País fictício A');
      await tap(tester, find.byKey(const ValueKey('breadcrumb-mundo')));
      expect(title(tester), 'Mundo');
      await tap(tester, find.text('Consultar votação no Brasil'));
      expect(title(tester), 'Brasil');
      expect(selectedMode(tester), ResultMode.comparison);
      expect(find.byKey(const ValueKey('breadcrumb-mundo')), findsNothing);
      await tap(tester, find.text('Consultar votação no exterior'));
      expect(title(tester), 'Mundo');
      expect(selectedMode(tester), ResultMode.comparison);
      router(tester).go('/uf/SC/municipio/00001?modo=2');
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('breadcrumb-locality')), findsOneWidget);
      await tap(tester, find.byKey(const ValueKey('breadcrumb-uf')));
      expect(title(tester), 'Santa Catarina');
      await tap(tester, find.byKey(const ValueKey('breadcrumb-brasil')));
      expect(title(tester), 'Brasil');
      expect(selectedMode(tester), ResultMode.second);
    },
  );

  testWidgets(
    'platform history restores routes, result mode and camera without contradictory state',
    (tester) async {
      await openGeo(tester, location: '/uf/SC/municipio/00001?modo=2');
      final provider = router(tester).routeInformationProvider;
      for (final path in [
        '/mundo/US?modo=comparacao',
        '/mundo?modo=comparacao',
        '/uf/SC/municipio/00001?modo=2',
        '/mundo/US?modo=comparacao',
      ]) {
        await provider.didPushRouteInformation(
          RouteInformation(uri: Uri.parse(path)),
        );
        await tester.pumpAndSettle();
        expect(
          router(tester).routeInformationProvider.value.uri.toString(),
          path,
        );
        final c = tester
            .widget<ExplorerPage>(find.byType(ExplorerPage))
            .controller;
        expect(c.abroad, path.startsWith('/mundo'));
        if (c.abroad) {
          expect(c.selected, isNull);
          expect(
            tester.widget<WorldMap>(find.byType(WorldMap)).selected,
            c.countryCode,
          );
        } else {
          expect(c.countryCode, isNull);
          expect(
            tester.widget<BrazilMap>(find.byType(BrazilMap)).selected,
            c.selected,
          );
        }
      }
    },
  );

  final brazil = BrazilGeometry.decode(
    File('assets/geo/br_states.geojson').readAsStringSync(),
  );
  for (final world in [false, true]) {
    Widget map(bool zoom, {bool reduced = false}) => MaterialApp(
      theme: AppTheme.build(Brightness.light),
      home: MediaQuery(
        data: MediaQueryData(disableAnimations: reduced),
        child: world
            ? WorldMap(
                geometry: fixtureWorld(),
                active: const {'US', 'PT', 'FJ'},
                selected: zoom ? 'FJ' : null,
                onSelect: (_) {},
                onReset: () {},
              )
            : BrazilMap(
                geometry: brazil,
                selected: zoom ? BrazilianState.sc : null,
                onSelect: (_) {},
                onReset: () {},
              ),
      ),
    );
    final buttonKey = ValueKey(world ? 'world-map-reset' : 'map-reset');
    testWidgets(
      'contextual framing fades, excludes hidden actions and zooms again: world=$world',
      (tester) async {
        final semantics = tester.ensureSemantics();
        try {
          await tester.pumpWidget(map(false));
          expect(find.byKey(buttonKey), findsNothing);
          await tester.pumpWidget(map(true));
          await tester.pump(const Duration(milliseconds: 110));
          final transitions = tester.widgetList<FadeTransition>(
            find.descendant(
              of: find.byType(MapResetButton),
              matching: find.byType(FadeTransition),
            ),
          );
          expect(
            transitions.any((t) => t.opacity.value > 0 && t.opacity.value < 1),
            isTrue,
          );
          await tester.pumpAndSettle();
          expect(find.byKey(buttonKey).hitTestable(), findsOneWidget);
          await tester.pumpWidget(map(false));
          await tester.pump(const Duration(milliseconds: 100));
          expect(find.byKey(buttonKey), findsOneWidget); // outgoing fade
          expect(find.byKey(buttonKey).hitTestable(), findsNothing);
          expect(
            tester.semantics.simulatedAccessibilityTraversal().any(
              (n) => n.getSemanticsData().label == 'Ver mapa inteiro',
            ),
            isFalse,
          );
          expect(
            tester
                .widget<ExcludeFocus>(
                  find
                      .descendant(
                        of: find.byType(MapResetButton),
                        matching: find.byType(ExcludeFocus),
                      )
                      .first,
                )
                .excluding,
            isTrue,
          );
          await tester.pumpAndSettle();
          expect(find.byKey(buttonKey), findsNothing);
          await tester.pumpWidget(map(true));
          await tester.pumpAndSettle();
          expect(find.byKey(buttonKey), findsOneWidget);
        } finally {
          semantics.dispose();
        }
      },
    );

    testWidgets(
      'reduced motion makes framing and camera immediate: world=$world',
      (tester) async {
        await tester.pumpWidget(map(false, reduced: true));
        await tester.pumpWidget(map(true, reduced: true));
        expect(
          tester
              .widget<AnimatedSwitcher>(
                find.descendant(
                  of: find.byType(MapResetButton),
                  matching: find.byType(AnimatedSwitcher),
                ),
              )
              .duration,
          Duration.zero,
        );
        if (world) {
          final p =
              tester
                      .widget<CustomPaint>(
                        find.byKey(const ValueKey('world-map-paint')),
                      )
                      .painter!
                  as WorldMapPainter;
          expect(p.viewport.world, p.geometry.viewFor('FJ'));
        } else {
          final p =
              tester
                      .widget<CustomPaint>(
                        find.byKey(const ValueKey('brazil-map-paint')),
                      )
                      .painter!
                  as BrazilMapPainter;
          expect(p.viewport.world, brazil.viewFor(BrazilianState.sc));
        }
        await tester.pumpWidget(map(false, reduced: true));
        await tester.pump();
        expect(find.byKey(buttonKey), findsNothing);
      },
    );
  }

  testWidgets(
    'world caption, unframed surface, hover and keyboard share map typography',
    (tester) async {
      await openGeo(tester);
      final text = tester.widget<Text>(find.text('Selecione um país'));
      final context = tester.element(find.byType(WorldMap));
      expect(text.style, Theme.of(context).textTheme.labelMedium);
      final decoration =
          tester
                  .widget<DecoratedBox>(
                    find
                        .descendant(
                          of: find.byType(WorldMap),
                          matching: find.byType(DecoratedBox),
                        )
                        .first,
                  )
                  .decoration
              as BoxDecoration;
      expect(decoration.color, isNull);
      expect((decoration.border! as Border).top.color, Colors.transparent);
      final f = find.byKey(const ValueKey('world-map-paint'));
      final p = tester.widget<CustomPaint>(f).painter! as WorldMapPainter;
      final us = p.geometry.countries.firstWhere((c) => c.iso == 'US');
      final mouse = await tester.createGesture(
        kind: ui.PointerDeviceKind.mouse,
      );
      await mouse.addPointer(location: Offset.zero);
      await mouse.moveTo(tester.getTopLeft(f) + p.viewport.toScreen(us.anchor));
      await tester.pump();
      expect(find.text('País fictício A'), findsOneWidget);
      expect(
        (tester.widget<CustomPaint>(f).painter! as WorldMapPainter)
            .highlights
            .last
            .iso,
        'US',
      );
      await mouse.removePointer();
      Focus.of(tester.element(f)).requestFocus();
      await tester.pump();
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowRight);
      await tester.pump();
      final focused = tester.widget<CustomPaint>(f).painter! as WorldMapPainter;
      expect(focused.highlights.last.iso, focused.focused);
      expect(focused.active.contains(focused.focused), isTrue);
      final pointer = await tester.createGesture(
        kind: ui.PointerDeviceKind.mouse,
      );
      await pointer.addPointer(location: Offset.zero);
      await pointer.moveTo(
        tester.getTopLeft(f) + p.viewport.toScreen(us.anchor),
      );
      await tester.pump();
      expect(
        (tester.widget<CustomPaint>(f).painter! as WorldMapPainter).focused,
        'US',
      );
      final pt = p.geometry.countries.firstWhere((c) => c.iso == 'PT');
      await pointer.moveTo(
        tester.getTopLeft(f) + p.viewport.toScreen(pt.anchor),
      );
      await tester.pump();
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowLeft);
      await tester.pump();
      expect(
        (tester.widget<CustomPaint>(f).painter! as WorldMapPainter).focused,
        'US',
      );
      await pointer.removePointer();
    },
  );

  testWidgets(
    'rapid world selections and reset retain one camera across the antimeridian',
    (tester) async {
      final geometry = fixtureWorld();
      Widget map(String? iso) => MaterialApp(
        home: WorldMap(
          geometry: geometry,
          active: const {'US', 'PT', 'FJ'},
          selected: iso,
          onSelect: (_) {},
          onReset: () {},
        ),
      );
      WorldMapPainter painter() =>
          tester
                  .widget<CustomPaint>(
                    find.byKey(const ValueKey('world-map-paint')),
                  )
                  .painter!
              as WorldMapPainter;
      await tester.pumpWidget(map(null));
      final state = tester.state(find.byType(WorldMap));
      await tester.pumpWidget(map('US'));
      await tester.pump(const Duration(milliseconds: 90));
      await tester.pumpWidget(map('PT'));
      await tester.pump(const Duration(milliseconds: 90));
      await tester.pumpWidget(map(null));
      await tester.pump(const Duration(milliseconds: 90));
      await tester.pumpWidget(map('FJ'));
      await tester.pumpAndSettle();
      expect(painter().viewport.world, geometry.viewFor('FJ'));
      expect(painter().viewport.world.width, lessThan(15));
      expect(tester.state(find.byType(WorldMap)), same(state));
      await tester.pumpWidget(map(null));
      await tester.pumpAndSettle();
      expect(painter().viewport.world, WorldGeometry.bounds);
      expect(
        WorldGeometry.longitudeWindow(painter().viewport.world),
        WorldGeometry.bounds,
      );
      expect(find.text('Ver mapa inteiro'), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'unavailable country link keeps a global camera without a framing action',
    (tester) async {
      await openGeo(tester, location: '/mundo/AA?modo=2');
      final p =
          tester
                  .widget<CustomPaint>(
                    find.byKey(const ValueKey('world-map-paint')),
                  )
                  .painter!
              as WorldMapPainter;
      expect(p.viewport.world, WorldGeometry.bounds);
      expect(find.text('Ver mapa inteiro'), findsNothing);
      expect(find.byType(DistributionChart), findsNothing);
      expect(find.byType(ComparisonChart), findsNothing);
    },
  );

  for (final brightness in Brightness.values) {
    test('world greens reuse the exact Brazilian tonal fill: $brightness', () {
      final g = fixtureWorld();
      final colors = AppTheme.build(brightness).colorScheme;
      final p = WorldMapPainter(
        geometry: g,
        viewport: MapViewport(WorldGeometry.bounds, const Size(600, 400)),
        colors: colors,
        active: const {'US', 'PT'},
        selected: 'US',
        focused: 'PT',
      );
      expect(p.fillFor(g.countries[0]), colors.primary);
      expect(p.fillFor(g.countries[1]), colors.primaryContainer);
      expect(p.fillFor(g.countries[2]), colors.outlineVariant);
      final base = WorldMapPainter(
        geometry: g,
        viewport: p.viewport,
        colors: colors,
        active: const {'US', 'PT'},
      );
      for (var i = 0; i < 2; i++) {
        expect(
          base.fillFor(g.countries[i]),
          Color.lerp(
            colors.surfaceContainerHighest,
            colors.primaryContainer,
            .3 + i % 4 * .1,
          ),
        );
        expect(base.fillFor(g.countries[i]), isNot(colors.tertiary));
      }
      expect(p.highlights.map((c) => c.iso), ['US', 'PT']);
    });
  }

  test(
    'global camera fits once and preserves aspect at all requested sizes',
    () {
      for (final size in [
        const Size(1366, 768),
        const Size(1920, 1080),
        const Size(390, 844),
        const Size(768, 1024),
      ]) {
        final vp = MapViewport(WorldGeometry.bounds, size);
        final tl = vp.toScreen(WorldGeometry.bounds.topLeft);
        final br = vp.toScreen(WorldGeometry.bounds.bottomRight);
        expect(tl.dx, greaterThanOrEqualTo(-1e-9));
        expect(tl.dy, greaterThanOrEqualTo(-1e-9));
        expect(br.dx, lessThanOrEqualTo(size.width + 1e-9));
        expect(br.dy, lessThanOrEqualTo(size.height + 1e-9));
        expect((br.dx - tl.dx) / (br.dy - tl.dy), closeTo(2, 1e-9));
      }
    },
  );

  testWidgets(
    'rasterized global map has no copies in horizontal letterboxing',
    (tester) async {
      final g = fixtureWorld();
      const size = Size(1600, 300);
      final vp = MapViewport(WorldGeometry.bounds, size);
      final recorder = ui.PictureRecorder();
      WorldMapPainter(
        geometry: g,
        viewport: vp,
        colors: AppTheme.build(Brightness.light).colorScheme,
        active: const {'US'},
      ).paint(Canvas(recorder), size);
      final picture = recorder.endRecording();
      final image = await tester.runAsync(() => picture.toImage(1600, 300));
      final bytes = await tester.runAsync(() => image!.toByteData());
      int alpha(Offset p) =>
          bytes!.getUint8((p.dy.floor() * 1600 + p.dx.floor()) * 4 + 3);
      final anchor = g.countries.first.anchor;
      expect(alpha(vp.toScreen(anchor)), 255);
      expect(alpha(vp.toScreen(anchor + const Offset(360, 0))), 0);
      expect(alpha(vp.toScreen(anchor - const Offset(360, 0))), 0);
      image!.dispose();
      picture.dispose();
    },
  );

  testWidgets(
    'hover outline is rasterized over the later neighbor; small-first hit testing is coherent',
    (tester) async {
      final a = CountryGeometry(
        'AA',
        'A',
        Path()..addRect(const Rect.fromLTRB(-4, -4, 0, 4)),
        const Offset(-2, 0),
      );
      final b = CountryGeometry(
        'BB',
        'B',
        Path()..addRect(const Rect.fromLTRB(0, -4, 4, 4)),
        const Offset(2, 0),
      );
      final g = WorldGeometry([a, b]);
      final colors = AppTheme.build(Brightness.light).colorScheme;
      final p = WorldMapPainter(
        geometry: g,
        viewport: MapViewport(
          const Rect.fromLTRB(-5, -5, 5, 5),
          const Size(200, 200),
        ),
        colors: colors,
        active: const {'AA', 'BB'},
        selected: 'BB',
        focused: 'AA',
      );
      expect(p.highlights.map((c) => c.iso), ['BB', 'AA']);
      final recorder = ui.PictureRecorder();
      p.paint(Canvas(recorder), const Size(200, 200));
      final picture = recorder.endRecording();
      final image = await tester.runAsync(() => picture.toImage(200, 200));
      final data = await tester.runAsync(() => image!.toByteData());
      final offset = (100 * 200 + 100) * 4;
      final pixel = Color.fromARGB(
        data!.getUint8(offset + 3),
        data.getUint8(offset),
        data.getUint8(offset + 1),
        data.getUint8(offset + 2),
      );
      expect(pixel, colors.onSurface);
      final island = CountryGeometry(
        'CC',
        'Ilha',
        Path()..addRect(const Rect.fromLTRB(-2, -1, -1, 1)),
        const Offset(-1.5, 0),
      );
      expect(
        WorldGeometry([a, island]).hitTest(const Offset(-1.5, 0), {'AA', 'CC'}),
        'CC',
      );
      expect(
        WorldGeometry([a, island]).hitTest(const Offset(-1.5, 0), {'AA'}),
        'AA',
      );
      image!.dispose();
      picture.dispose();
    },
  );
}
