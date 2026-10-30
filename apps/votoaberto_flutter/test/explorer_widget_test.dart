import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/app/strings.dart';
import 'package:votoaberto/app/votoaberto_app.dart';
import 'package:votoaberto/features/elections/data/mock_election_repository.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/elections/domain/election_repository.dart';
import 'package:votoaberto/features/map/domain/brazil_geometry.dart';
import 'package:votoaberto/features/map/presentation/brazil_map.dart';

class ErrorRepository implements ElectionRepository {
  @override
  Future<ElectionDataset> load(Election election) async =>
      throw StateError('test');
}

class EmptyRepository implements ElectionRepository {
  @override
  Future<ElectionDataset> load(Election election) async => ElectionDataset(
    election: election,
    provenance: MockElectionRepository.provenance,
    states: [],
    national: NationalSummary({}),
  );
}

class LoadingRepository implements ElectionRepository {
  final result = Completer<ElectionDataset>();
  @override
  Future<ElectionDataset> load(Election election) => result.future;
}

Future<void> open(
  WidgetTester tester, {
  Size size = const Size(1366, 768),
  ElectionRepository? repository,
  String? location,
  bool settle = true,
  Future<BrazilGeometry> Function()? geometryLoader,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    VotoAbertoApp(
      repository: repository ?? MockElectionRepository(),
      initialLocation: location ?? '/',
      geometryLoader:
          geometryLoader ??
          () async => BrazilGeometry.decode(
            File('assets/geo/br_states.geojson').readAsStringSync(),
          ),
    ),
  );
  if (settle) await tester.pumpAndSettle();
}

Future<void> reveal(WidgetTester tester, Finder finder) async {
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('an exact UF abbreviation takes priority over name substrings', (
    tester,
  ) async {
    await open(tester);
    await tester.enterText(find.byKey(const ValueKey('state-search')), 'SP');
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'São Paulo',
    );
  });
  testWidgets('real pending load displays loading and resolves', (
    tester,
  ) async {
    final repo = LoadingRepository();
    await open(tester, repository: repo, settle: false);
    await tester.pump();
    expect(find.text('Carregando dados locais…'), findsOneWidget);
    repo.result.complete(
      await MockElectionRepository().load(Election.demonstration),
    );
    await tester.pumpAndSettle();
    expect(find.text('EXPLORAÇÃO NACIONAL'), findsOneWidget);
  });

  testWidgets('geometry error offers a working retry', (tester) async {
    var calls = 0;
    await open(
      tester,
      geometryLoader: () async {
        if (++calls == 1) throw StateError('asset failure');
        return BrazilGeometry.decode(
          File('assets/geo/br_states.geojson').readAsStringSync(),
        );
      },
    );
    expect(
      find.text('Não foi possível abrir a malha do IBGE.'),
      findsOneWidget,
    );
    await tester.tap(find.text('Tentar novamente'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('brazil-map-paint')), findsOneWidget);
  });

  testWidgets('platform back returns a deep-linked UF to Brazil', (
    tester,
  ) async {
    await open(tester, location: '/uf/SP?turno=2&visao=summary');
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'Brasil',
    );
    expect(
      tester.widget<ChoiceChip>(find.byKey(const ValueKey('round-2'))).selected,
      isTrue,
    );
  });

  testWidgets('resizing between desktop and mobile preserves navigation', (
    tester,
  ) async {
    await open(tester, location: '/uf/RJ?turno=2&visao=summary');
    for (final size in const [
      Size(390, 844),
      Size(768, 1024),
      Size(1920, 1080),
      Size(1366, 768),
    ]) {
      tester.view.physicalSize = size;
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
        'Rio de Janeiro',
      );
      expect(
        tester
            .widget<ChoiceChip>(find.byKey(const ValueKey('round-2')))
            .selected,
        isTrue,
      );
      expect(tester.takeException(), isNull);
    }
  });

  testWidgets('visible text contrast and touch targets in both themes', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    try {
      await open(tester);
      await expectLater(tester, meetsGuideline(textContrastGuideline));
      await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
      await tester.tap(find.byKey(const ValueKey('theme-toggle')));
      await tester.pumpAndSettle();
      await expectLater(tester, meetsGuideline(textContrastGuideline));
    } finally {
      semantics.dispose();
    }
  });
  testWidgets(
    'national screen, search, state results, rounds, comparison and return',
    (tester) async {
      await open(tester);
      expect(find.text(AppStrings.demo), findsOneWidget);
      expect(find.text('EXPLORAÇÃO NACIONAL'), findsOneWidget);
      await tester.enterText(
        find.byKey(const ValueKey('state-search')),
        'sao paulo',
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('select-SP')));
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
        'São Paulo',
      );
      expect(find.text(AppStrings.demo), findsOneWidget);
      await reveal(tester, find.byKey(const ValueKey('round-2')));
      await tester.tap(find.byKey(const ValueKey('round-2')));
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
        'São Paulo',
      );
      await reveal(tester, find.byKey(const ValueKey('view-comparison')));
      await tester.tap(find.byKey(const ValueKey('view-comparison')));
      await tester.pumpAndSettle();
      expect(find.text('Entre um turno e outro'), findsOneWidget);
      expect(find.textContaining('Não disputa o 2º turno.'), findsNWidgets(2));
      await reveal(tester, find.byKey(const ValueKey('back-brasil')));
      await tester.tap(find.byKey(const ValueKey('back-brasil')));
      await tester.pumpAndSettle();
      expect(find.text('EXPLORAÇÃO NACIONAL'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('search empty state and Enter selects a small UF', (
    tester,
  ) async {
    await open(tester);
    await tester.enterText(
      find.byKey(const ValueKey('state-search')),
      'inexistente',
    );
    await tester.pump();
    expect(find.text(AppStrings.noState), findsOneWidget);
    await tester.enterText(find.byKey(const ValueKey('state-search')), 'DF');
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.pumpAndSettle();
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'Distrito Federal',
    );
  });

  testWidgets('theme toggle preserves selection and methodology is available', (
    tester,
  ) async {
    await open(tester, location: '/uf/AC?turno=2&visao=summary');
    await tester.tap(find.byKey(const ValueKey('theme-toggle')));
    await tester.pumpAndSettle();
    expect(
      tester.widget<MaterialApp>(find.byType(MaterialApp)).themeMode,
      ThemeMode.dark,
    );
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
      'Acre',
    );
    await tester.tap(find.byTooltip(AppStrings.methodology));
    await tester.pumpAndSettle();
    expect(find.text(AppStrings.methodologyBody), findsOneWidget);
    await tester.tap(find.text('Entendi'));
    await tester.pumpAndSettle();
  });

  testWidgets('deep link and unavailable hierarchy do not fabricate content', (
    tester,
  ) async {
    await open(tester, location: '/uf/ZZ');
    expect(
      find.text('Este endereço não está disponível no M1.'),
      findsOneWidget,
    );
    expect(find.text(AppStrings.demo), findsOneWidget);
  });

  testWidgets('repository error and retry control', (tester) async {
    await open(tester, repository: ErrorRepository());
    expect(find.text(AppStrings.loadError), findsOneWidget);
    await tester.tap(find.text('Tentar novamente'));
    await tester.pumpAndSettle();
    expect(find.text(AppStrings.loadError), findsOneWidget);
  });

  testWidgets('empty dataset has an explicit state', (tester) async {
    await open(tester, repository: EmptyRepository());
    expect(find.text(AppStrings.empty), findsOneWidget);
  });

  testWidgets(
    'map pointer selects geometry and control clicks do not select a UF',
    (tester) async {
      await open(tester);
      final paintFinder = find.byKey(const ValueKey('brazil-map-paint'));
      final painter =
          tester.widget<CustomPaint>(paintFinder).painter! as BrazilMapPainter;
      final target = painter.geometry.states.firstWhere(
        (s) => s.state.code == 'AM',
      );
      final origin = tester.getTopLeft(paintFinder);
      await tester.tapAt(origin + painter.viewport.toScreen(target.label));
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
        'Amazonas',
      );
      await tester.tap(find.byKey(const ValueKey('map-reset')));
      await tester.pumpAndSettle();
      expect(
        tester.widget<Text>(find.byKey(const ValueKey('panel-title'))).data,
        'Brasil',
      );
    },
  );

  testWidgets('map keyboard can select and reset without hover', (
    tester,
  ) async {
    await open(tester);
    // The painted surface is inside the map's keyboard Focus.
    Focus.of(
      tester.element(find.byKey(const ValueKey('brazil-map-paint'))),
    ).requestFocus();
    await tester.pump();
    await tester.sendKeyEvent(LogicalKeyboardKey.arrowRight);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.pumpAndSettle();
    expect(find.text('VISÃO ESTADUAL · AL'), findsOneWidget);
    await tester.sendKeyEvent(LogicalKeyboardKey.escape);
    await tester.pumpAndSettle();
    expect(find.text('EXPLORAÇÃO NACIONAL'), findsOneWidget);
  });

  for (final size in const [
    Size(1920, 1080),
    Size(1366, 768),
    Size(768, 1024),
    Size(390, 844),
    Size(280, 700),
  ]) {
    testWidgets('responsive navigation without overflow at $size', (
      tester,
    ) async {
      await open(
        tester,
        size: size,
        location: '/uf/DF?turno=2&visao=comparison',
      );
      expect(find.text(AppStrings.demo), findsOneWidget);
      expect(tester.takeException(), isNull);
      await reveal(tester, find.text('Entre um turno e outro'));
      expect(tester.takeException(), isNull);
      await reveal(tester, find.byKey(const ValueKey('back-brasil')));
      await tester.tap(find.byKey(const ValueKey('back-brasil')));
      await tester.pumpAndSettle();
      expect(find.text('EXPLORAÇÃO NACIONAL'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
}
