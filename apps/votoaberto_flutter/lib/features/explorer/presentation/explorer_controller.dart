import 'package:flutter/material.dart';
import '../../elections/domain/election.dart';
import '../../elections/domain/election_repository.dart';
import '../../elections/domain/geography.dart';

enum ExplorerView { summary, comparison, insights }

enum LoadStatus { loading, ready, error }

class ExplorerController extends ChangeNotifier {
  ExplorerController(this.repository, {this.election = Election.demonstration});
  final ElectionRepository repository;
  final Election election;
  ElectionDataset? dataset;
  LoadStatus status = LoadStatus.loading;
  BrazilianState? selected;
  ElectionRound round = ElectionRound.first;
  ExplorerView view = ExplorerView.summary;
  ThemeMode theme = ThemeMode.light;
  int _request = 0;
  bool _disposed = false;
  bool abroad = false;
  String? municipalityCode;
  List<MunicipalitySummary> municipalities = const [];
  LoadStatus municipalStatus = LoadStatus.ready;
  int _municipalRequest = 0;
  String? _loadedTerritory;
  String? get territoryCode => abroad ? 'ZZ' : selected?.code;
  bool get municipalSupported => repository is MunicipalElectionRepository;
  MunicipalitySummary? get municipality => municipalities
      .where((s) => s.municipality.code == municipalityCode)
      .firstOrNull;
  bool get synthetic =>
      dataset?.provenance.synthetic ?? election.id == Election.demonstration.id;

  Future<void> load() async {
    final request = ++_request;
    status = LoadStatus.loading;
    notifyListeners();
    try {
      final next = await repository.load(election);
      if (_disposed || request != _request) return;
      if (next.election.id != election.id ||
          next.election.year != election.year) {
        throw StateError('Eleição incompatível com a seleção');
      }
      dataset = next;
      status = LoadStatus.ready;
      if (territoryCode != null) await loadMunicipalities();
    } catch (_) {
      if (_disposed || request != _request) return;
      dataset = null;
      status = LoadStatus.error;
    }
    if (!_disposed && request == _request) notifyListeners();
  }

  /// Router is the source of navigation state; a selection needs no new fetch.
  void navigate(
    BrazilianState? state,
    ElectionRound nextRound,
    ExplorerView nextView, {
    bool notify = true,
    bool overseas = false,
    String? municipality,
  }) {
    if (selected == state &&
        round == nextRound &&
        view == nextView &&
        abroad == overseas &&
        municipalityCode == municipality) {
      return;
    }
    final territoryChanged = selected != state || abroad != overseas;
    selected = state;
    abroad = overseas;
    municipalityCode = municipality;
    round = nextRound;
    view = nextView;
    if (territoryChanged) {
      _municipalRequest++;
      municipalities = const [];
      _loadedTerritory = null;
      municipalStatus = territoryCode == null
          ? LoadStatus.ready
          : LoadStatus.loading;
      // Router parses during build; load/notify only after that stack completes.
      if (dataset != null) Future.microtask(loadMunicipalities);
    }
    if (notify) notifyListeners();
  }

  Future<void> loadMunicipalities() async {
    final uf = territoryCode;
    if (_disposed || uf == null || !municipalSupported || dataset == null) {
      municipalStatus = LoadStatus.ready;
      return;
    }
    if (_loadedTerritory == uf) return;
    final request = ++_municipalRequest;
    municipalStatus = LoadStatus.loading;
    notifyListeners();
    try {
      final next = await (repository as MunicipalElectionRepository)
          .loadMunicipalities(election, uf);
      if (_disposed || request != _municipalRequest || uf != territoryCode) {
        return;
      }
      municipalities = next;
      _loadedTerritory = uf;
      municipalStatus = LoadStatus.ready;
    } catch (_) {
      if (_disposed || request != _municipalRequest) return;
      municipalities = const [];
      municipalStatus = LoadStatus.error;
    }
    notifyListeners();
  }

  Map<ElectionRound, RoundResult>? get results => municipalityCode != null
      ? municipality?.rounds
      : abroad
      ? dataset?.overseas?.rounds
      : dataset?.results(selected);
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
