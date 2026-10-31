import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:url_launcher_platform_interface/link.dart';
import 'package:votoaberto/core/institutional_link.dart';
import 'package:votoaberto/app/votoaberto_app.dart';
import 'package:votoaberto/features/elections/data/mock_election_repository.dart';
import 'package:votoaberto/features/map/domain/brazil_geometry.dart';

void main() {
  testWidgets(
    'native application keeps its existing layout without the footer',
    (tester) async {
      await tester.pumpWidget(
        VotoAbertoApp(
          repository: MockElectionRepository(),
          geometryLoader: () async => BrazilGeometry.decode(
            File('assets/geo/br_states.geojson').readAsStringSync(),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(InstitutionalLink), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'institutional link has semantics, exact URL and keyboard action',
    (tester) async {
      final opened = <String>[];
      final semantics = tester.ensureSemantics();
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            bottomNavigationBar: InstitutionalLink(openUrl: opened.add),
          ),
        ),
      );
      final link = tester.widget<InstitutionalLink>(
        find.byType(InstitutionalLink),
      );
      expect(link.uri, Uri.parse('https://urnalivre.com.br/'));
      expect(link.target, LinkTarget.blank);
      expect(
        tester
            .getSemantics(
              find.bySemanticsLabel(
                'Uma iniciativa Urna Livre (abre em nova aba)',
              ),
            )
            .flagsCollection
            .isLink,
        isTrue,
      );
      semantics.dispose();
      await tester.sendKeyEvent(LogicalKeyboardKey.tab);
      await tester.sendKeyEvent(LogicalKeyboardKey.enter);
      await tester.tap(find.byKey(const ValueKey('institutional-link')));
      expect(opened, everyElement('https://urnalivre.com.br/'));
      expect(opened.length, 2);
    },
  );

  for (final size in [const Size(320, 568), const Size(844, 390)]) {
    testWidgets('footer fits $size with enlarged text and safe inset', (
      tester,
    ) async {
      tester.view.physicalSize = size;
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(
        MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: const TextScaler.linear(2),
              padding: const EdgeInsets.only(bottom: 24),
            ),
            child: child!,
          ),
          home: const Scaffold(
            body: Center(child: Text('Resultados')),
            bottomNavigationBar: InstitutionalLink(),
          ),
        ),
      );
      expect(tester.takeException(), isNull);
      expect(find.text('Resultados'), findsOneWidget);
      final link = tester.getRect(
        find.byKey(const ValueKey('institutional-link')),
      );
      expect(link.bottom, lessThanOrEqualTo(size.height - 24));
      expect(link.left, greaterThanOrEqualTo(0));
      expect(link.right, lessThanOrEqualTo(size.width));
    });
  }
}
