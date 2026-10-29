import 'package:flutter/material.dart';
import '../../elections/domain/election.dart';
import '../../elections/domain/election_repository.dart';
import '../../elections/domain/geography.dart';

enum ExplorerView { summary, comparison, insights }

enum LoadStatus { loading, ready, error }

class ExplorerController extends ChangeNotifier {
  ExplorerController(this.repository);
  final ElectionRepository repository;
  ElectionDataset? dataset;
  LoadStatus status = LoadStatus.loading;
  BrazilianState? selected;
  ElectionRound round = ElectionRound.first;
  ExplorerView view = ExplorerView.summary;
  ThemeMode theme = ThemeMode.light;
  int _request = 0;
  bool _disposed = false;

  Future<void> load() async {
    final request = ++_request;
    status = LoadStatus.loading;
    notifyListeners();
    try {
      final next = await repository.load(Election.demonstration);
      if (_disposed || request != _request) return;
      if (!next.provenance.synthetic) {
        throw StateError('O M1 aceita somente conjuntos demonstrativos');
      }
      dataset = next;
      status = LoadStatus.ready;
    } catch (_) {
      if (_disposed || request != _request) return;
      dataset = null;
      status = LoadStatus.error;
    }
    notifyListeners();
  }

  /// Router is the source of navigation state; a selection needs no new fetch.
  void navigate(
    BrazilianState? state,
    ElectionRound nextRound,
    ExplorerView nextView, {
    bool notify = true,
  }) {
    if (selected == state && round == nextRound && view == nextView) return;
    selected = state;
    round = nextRound;
    view = nextView;
    if (notify) notifyListeners();
  }

  Map<ElectionRound, RoundResult>? get results => dataset?.results(selected);
  void toggleTheme() {
    theme = theme == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
