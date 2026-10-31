import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/features/elections/data/mock_election_repository.dart';
import 'package:votoaberto/features/elections/domain/election.dart';
import 'package:votoaberto/features/elections/domain/election_repository.dart';
import 'package:votoaberto/features/elections/domain/geography.dart';
import 'package:votoaberto/features/explorer/presentation/explorer_controller.dart';

class PendingRepository implements ElectionRepository {
  final requests = <Completer<ElectionDataset>>[];
  @override
  Future<ElectionDataset> load(Election election) {
    final result = Completer<ElectionDataset>();
    requests.add(result);
    return result.future;
  }
}

void main() {
  test('selection, round, filters and theme remain independent', () async {
    final c = ExplorerController(MockElectionRepository());
    addTearDown(c.dispose);
    await c.load();
    expect(c.status, LoadStatus.ready);
    c.navigate(BrazilianState.sp, ResultMode.first);
    c.navigate(BrazilianState.df, ResultMode.comparison);
    expect(c.selected, BrazilianState.df);
    expect(c.mode, ResultMode.comparison);
    expect(c.results, c.dataset!.results(BrazilianState.df));
    c.toggleTheme();
    expect(c.theme, ThemeMode.dark);
    expect(c.selected, BrazilianState.df);
    c.navigate(null, c.mode);
    expect(c.selected, isNull);
    expect(c.results, c.dataset!.national.rounds);
  });

  test(
    'latest retry wins; pending loads do not overwrite rapid selections',
    () async {
      final repo = PendingRepository();
      final c = ExplorerController(repo);
      addTearDown(c.dispose);
      final first = c.load();
      final second = c.load();
      c.navigate(BrazilianState.ac, ResultMode.first);
      c.navigate(BrazilianState.rj, ResultMode.comparison);
      repo.requests[1].complete(
        await MockElectionRepository().load(Election.demonstration),
      );
      await second;
      repo.requests[0].completeError(StateError('stale failure'));
      await first;
      expect(c.status, LoadStatus.ready);
      expect(c.selected, BrazilianState.rj);
    },
  );

  test('actual failure can be retried', () async {
    final repo = PendingRepository();
    final c = ExplorerController(repo);
    addTearDown(c.dispose);
    final first = c.load();
    repo.requests.first.completeError(StateError('offline'));
    await first;
    expect(c.status, LoadStatus.error);
    final retry = c.load();
    repo.requests.last.complete(
      await MockElectionRepository().load(Election.demonstration),
    );
    await retry;
    expect(c.status, LoadStatus.ready);
  });

  test('completion after disposal is ignored', () async {
    final repo = PendingRepository();
    final c = ExplorerController(repo);
    final load = c.load();
    c.dispose();
    repo.requests.first.complete(
      await MockElectionRepository().load(Election.demonstration),
    );
    await load;
  });
}
