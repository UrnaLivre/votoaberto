import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:votoaberto/app/strings.dart';
import 'package:votoaberto/main.dart' as app;
import 'package:votoaberto/features/map/presentation/brazil_map.dart';
import 'package:votoaberto/features/map/presentation/world_map.dart';
import 'package:go_router/go_router.dart';
import 'package:votoaberto/features/explorer/presentation/round_summary.dart';

class NoHttp extends HttpOverrides {
  int attempts = 0;
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    attempts++;
    throw StateError('HTTP bloqueado no smoke offline da aplicação');
  }
}

Future<void> captureDialog(WidgetTester tester, String name) async {
  const output = String.fromEnvironment('QA_SCREENSHOTS');
  if (output.isEmpty) return;
  final boundary = tester.renderObject<RenderRepaintBoundary>(
    find
        .ancestor(
          of: find.byKey(const ValueKey('special-cases-surface')),
          matching: find.byType(RepaintBoundary),
        )
        .first,
  );
  final picture = await boundary.toImage(pixelRatio: 1);
  final bytes = await picture.toByteData(format: ui.ImageByteFormat.png);
  await Directory(output).create(recursive: true);
  await File('$output/$name.png').writeAsBytes(bytes!.buffer.asUint8List());
  picture.dispose();
}

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  const enabled = bool.fromEnvironment('RUN_REAL_EMBEDDED');
  testWidgets('native real assets without any application HTTP request', (
    tester,
  ) async {
    final previous = HttpOverrides.current;
    final offline = NoHttp();
    HttpOverrides.global = offline;
    addTearDown(() => HttpOverrides.global = previous);
    final metrics = <String, Object>{};
    final clock = Stopwatch()..start();
    app.main();
    await tester.pumpAndSettle();
    metrics['first_national_frame_ms'] = clock.elapsedMicroseconds / 1000;
    expect(find.text(AppStrings.demo), findsNothing);
    expect(find.text('119.306.034'), findsOneWidget);
    final round2 = find.byKey(const ValueKey('mode-second'));
    await tester.ensureVisible(round2);
    clock.reset();
    await tester.tap(round2);
    await tester.pumpAndSettle();
    metrics['round_change_ms'] = clock.elapsedMicroseconds / 1000;
    expect(find.text('124.082.273'), findsOneWidget);

    final stateSearch = find.byKey(const ValueKey('state-search'));
    await tester.ensureVisible(stateSearch);
    await tester.enterText(stateSearch, 'SP');
    await tester.pumpAndSettle();
    clock.reset();
    await tester.tap(find.byKey(const ValueKey('select-SP')));
    await tester.pumpAndSettle();
    metrics['state_selection_ms'] = clock.elapsedMicroseconds / 1000;

    final citySearch = find.byKey(const ValueKey('municipality-search'));
    await tester.ensureVisible(citySearch);
    clock.reset();
    await tester.enterText(citySearch, 'sao paulo');
    await tester.pumpAndSettle();
    metrics['municipal_search_ms'] = clock.elapsedMicroseconds / 1000;
    final saoPaulo = find.byKey(const ValueKey('municipality-71072'));
    await tester.ensureVisible(saoPaulo);
    clock.reset();
    await tester.tap(saoPaulo);
    await tester.pumpAndSettle();
    metrics['municipal_selection_ms'] = clock.elapsedMicroseconds / 1000;
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'SÃO PAULO',
    );
    expect(find.byKey(const ValueKey('municipal-marker')), findsOneWidget);
    final mapState = tester.state(find.byType(BrazilMap));

    final secondSearch = find.byKey(const ValueKey('municipality-search'));
    await tester.ensureVisible(secondSearch);
    await tester.enterText(secondSearch, 'adamantina');
    await tester.pumpAndSettle();
    await tester.ensureVisible(
      find.byKey(const ValueKey('municipality-61018')),
    );
    await tester.tap(find.byKey(const ValueKey('municipality-61018')));
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'ADAMANTINA',
    );
    expect(tester.state(find.byType(BrazilMap)), same(mapState));
    expect(find.byKey(const ValueKey('municipal-marker')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('map-reset')));
    await tester.pumpAndSettle();
    expect(find.text('124.082.273'), findsOneWidget);
    expect(find.byKey(const ValueKey('municipal-marker')), findsNothing);
    expect(find.byKey(const ValueKey('map-reset')), findsNothing);
    final router = GoRouter.of(
      tester.element(find.byKey(const ValueKey('map-title'))),
    );
    expect(router.routeInformationProvider.value.uri.toString(), '/?modo=2');
    clock.reset();
    router.go('/mundo?turno=2&visao=summary');
    await tester.pumpAndSettle();
    metrics['world_selection_ms'] = clock.elapsedMicroseconds / 1000;
    expect(find.text('371.651'), findsOneWidget);
    expect(tester.widget<WorldMap>(find.byType(WorldMap)).active.length, 100);
    expect(find.textContaining('Cobertura por país parcial'), findsNothing);
    expect(find.text('Sem país confirmado (2)'), findsNothing);
    final worldRoute = router.routeInformationProvider.value.uri;
    await tester.ensureVisible(
      find.byKey(const ValueKey('special-cases-open')),
    );
    await tester.tap(find.byKey(const ValueKey('special-cases-open')));
    await tester.pumpAndSettle();
    expect(find.text('Localidade eleitoral TSE 29432'), findsOneWidget);
    await captureDialog(tester, 'bruxelas-light-desktop');
    expect(
      tester
          .widget<RoundSummary>(
            find.byKey(const ValueKey('special-result-29432-first')),
          )
          .result
          .totals
          .counted,
      5091,
    );
    expect(
      tester
          .widget<RoundSummary>(
            find.byKey(const ValueKey('special-result-29432-second')),
          )
          .result
          .totals
          .counted,
      5326,
    );
    await tester.tap(find.byKey(const ValueKey('special-tab-30686')));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<RoundSummary>(
            find.byKey(const ValueKey('special-result-30686-first')),
          )
          .result
          .totals
          .counted,
      2,
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
    await captureDialog(tester, 'tripoli-light-desktop');
    await tester.tap(find.byKey(const ValueKey('special-cases-close')));
    await tester.pumpAndSettle();
    expect(router.routeInformationProvider.value.uri, worldRoute);
    await tester.tap(find.byKey(const ValueKey('theme-toggle')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('special-cases-open')));
    await tester.pumpAndSettle();
    await captureDialog(tester, 'bruxelas-dark-desktop');
    await tester.tap(find.byKey(const ValueKey('special-tab-30686')));
    await tester.pumpAndSettle();
    await captureDialog(tester, 'tripoli-dark-desktop');
    await tester.tap(find.byKey(const ValueKey('special-cases-close')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('theme-toggle')));
    await tester.pumpAndSettle();
    for (final mode in ['1', '2', 'comparacao']) {
      router.go('/mundo/NP/localidade/29173?modo=$mode');
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
        'KATMANDU',
      );
      expect(tester.widget<WorldMap>(find.byType(WorldMap)).selected, 'NP');
      if (mode == 'comparacao') {
        expect(find.text('Entre um turno e outro'), findsOneWidget);
      }
    }
    clock.reset();
    router.go('/mundo/US?turno=2&visao=summary');
    await tester.pumpAndSettle();
    metrics['country_selection_ms'] = clock.elapsedMicroseconds / 1000;
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'Estados Unidos',
    );
    expect(find.text('85.741'), findsOneWidget);
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('turnout-rate'))).data,
      'Indisponível',
    );
    router.go('/mundo/US/localidade/29416?turno=2&visao=comparison');
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'BOSTON',
    );
    expect(find.text('Entre um turno e outro'), findsOneWidget);
    expect(
      router.routeInformationProvider.value.uri.toString(),
      '/mundo/US/localidade/29416?modo=comparacao',
    );
    await tester.tap(find.byKey(const ValueKey('world-map-reset')));
    await tester.pumpAndSettle();
    expect(
      router.routeInformationProvider.value.uri.toString(),
      '/mundo?modo=comparacao',
    );
    expect(find.byKey(const ValueKey('world-map-reset')), findsNothing);
    expect(find.text('Entre um turno e outro'), findsOneWidget);
    expect(find.byKey(const ValueKey('breadcrumb-brasil')), findsNothing);
    router.go('/mundo/localidade/29432?turno=1');
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'BRUXELAS',
    );
    expect(tester.widget<WorldMap>(find.byType(WorldMap)).selected, isNull);
    expect(find.textContaining('ZZ'), findsNothing);
    router.go('/?turno=2&visao=summary');
    await tester.pumpAndSettle();
    expect(find.text('124.082.273'), findsOneWidget);
    expect(offline.attempts, 0);
    metrics['application_http_attempts'] = offline.attempts;
    binding.reportData = metrics;
    debugPrint('VOTOABERTO_NATIVE_QA ${jsonEncode(metrics)}');
  }, skip: !enabled);
}
