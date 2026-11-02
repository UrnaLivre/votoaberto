import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/app/theme.dart';
import 'package:votoaberto/features/elections/domain/geography.dart';
import 'package:votoaberto/features/map/domain/brazil_geometry.dart';
import 'package:votoaberto/features/map/presentation/brazil_map.dart';

void main() {
  final source = File('assets/geo/br_states.geojson').readAsStringSync();
  final geometry = BrazilGeometry.decode(source);
  test('real geometry loads 27 UFs and all label anchors hit their own UF', () {
    expect(geometry.states.length, 27);
    for (final state in geometry.states) {
      expect(
        geometry.hitTest(state.label),
        state.state,
        reason: state.state.code,
      );
      final view = geometry.viewFor(state.state);
      expect(view.contains(state.bounds.topLeft), isTrue);
      expect(view.contains(state.bounds.bottomRight), isTrue);
    }
    expect(geometry.hitTest(BrazilGeometry.project(0, 0)), isNull);
  });

  test('DF inside GO, small coastal states and complex northern borders', () {
    for (final sample in <(double, double, BrazilianState)>[
      (-47.88, -15.79, BrazilianState.df),
      (-49.26, -16.68, BrazilianState.go),
      (-37.07, -10.91, BrazilianState.se),
      (-35.73, -9.64, BrazilianState.al),
      (-60.02, -3.10, BrazilianState.am),
      (-51.07, .03, BrazilianState.ap),
      (-34.88, -8.05, BrazilianState.pe),
    ]) {
      expect(
        geometry.hitTest(BrazilGeometry.project(sample.$1, sample.$2)),
        sample.$3,
      );
    }
  });

  test('Polygon holes and every MultiPolygon component are preserved', () {
    final json = jsonDecode(source) as Map<String, dynamic>;
    final features = json['features'] as List<dynamic>;
    final first = features.first as Map<String, dynamic>;
    first['geometry'] = {
      'type': 'MultiPolygon',
      'coordinates': [
        [
          [
            [0, 0],
            [4, 0],
            [4, 4],
            [0, 4],
            [0, 0],
          ],
          [
            [1, 1],
            [3, 1],
            [3, 3],
            [1, 3],
            [1, 1],
          ],
        ],
        [
          [
            [10, 0],
            [11, 0],
            [11, 1],
            [10, 1],
            [10, 0],
          ],
        ],
      ],
    };
    final changed = BrazilGeometry.decode(jsonEncode(json));
    expect(changed.hitTest(BrazilGeometry.project(.5, .5)), BrazilianState.ro);
    expect(changed.hitTest(BrazilGeometry.project(2, 2)), isNull);
    expect(
      changed.hitTest(BrazilGeometry.project(10.5, .5)),
      BrazilianState.ro,
    );
  });

  test('uniform viewport is invertible at desktop and mobile sizes', () {
    for (final size in const [Size(900, 650), Size(280, 350)]) {
      final viewport = MapViewport(geometry.viewFor(null), size);
      for (final state in geometry.states) {
        expect(
          (viewport.toWorld(viewport.toScreen(state.label)) - state.label)
              .distance,
          lessThan(1e-10),
        );
      }
    }
  });

  testWidgets(
    'rapid selections replace an animation and reset reaches national bounds',
    (tester) async {
      Widget map(BrazilianState? selected) => MaterialApp(
        theme: AppTheme.build(Brightness.light),
        home: SizedBox(
          width: 800,
          height: 600,
          child: BrazilMap(
            geometry: geometry,
            selected: selected,
            onSelect: (_) {},
            onReset: () {},
          ),
        ),
      );
      await tester.pumpWidget(map(null));
      await tester.pumpWidget(map(BrazilianState.am));
      await tester.pump(const Duration(milliseconds: 140));
      await tester.pumpWidget(map(BrazilianState.df));
      await tester.pumpAndSettle();
      BrazilMapPainter painter() =>
          tester
                  .widget<CustomPaint>(
                    find.byKey(const ValueKey('brazil-map-paint')),
                  )
                  .painter!
              as BrazilMapPainter;
      expect(painter().viewport.world, geometry.viewFor(BrazilianState.df));
      await tester.pumpWidget(map(null));
      await tester.pumpAndSettle();
      expect(painter().viewport.world, geometry.viewFor(null));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('all 27 UF anchors can be selected with a pointer', (
    tester,
  ) async {
    BrazilianState? selected;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: BrazilMap(
            geometry: geometry,
            selected: null,
            onSelect: (state) => selected = state,
            onReset: () {},
          ),
        ),
      ),
    );
    final paint = find.byKey(const ValueKey('brazil-map-paint'));
    final painter =
        tester.widget<CustomPaint>(paint).painter! as BrazilMapPainter;
    final origin = tester.getTopLeft(paint);
    for (final state in geometry.states) {
      await tester.tapAt(origin + painter.viewport.toScreen(state.label));
      expect(selected, state.state, reason: state.state.code);
    }
  });

  testWidgets(
    'reduced motion fits immediately without a pending camera animation',
    (tester) async {
      Widget map(BrazilianState? state) => MaterialApp(
        home: MediaQuery(
          data: const MediaQueryData(disableAnimations: true),
          child: BrazilMap(
            geometry: geometry,
            selected: state,
            onSelect: (_) {},
            onReset: () {},
          ),
        ),
      );
      await tester.pumpWidget(map(null));
      await tester.pumpWidget(map(BrazilianState.df));
      final painter =
          tester
                  .widget<CustomPaint>(
                    find.byKey(const ValueKey('brazil-map-paint')),
                  )
                  .painter!
              as BrazilMapPainter;
      expect(painter.viewport.world, geometry.viewFor(BrazilianState.df));
    },
  );
}
