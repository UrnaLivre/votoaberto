import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:votoaberto/app/strings.dart';
import 'package:votoaberto/main.dart' as app;

class NoHttp extends HttpOverrides {
  int attempts = 0;
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    attempts++;
    throw StateError('HTTP bloqueado no smoke offline da aplicação');
  }
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
    final round2 = find.byKey(const ValueKey('round-2'));
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
    expect(offline.attempts, 0);
    metrics['application_http_attempts'] = offline.attempts;
    binding.reportData = metrics;
    debugPrint('VOTOABERTO_NATIVE_QA ${jsonEncode(metrics)}');
  }, skip: !enabled);
}
