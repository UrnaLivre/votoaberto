import 'package:flutter/material.dart';
import '../../elections/domain/election.dart';
import '../../elections/domain/country.dart';
import '../../elections/domain/election_repository.dart';
import '../../elections/domain/geography.dart';
import '../../map/domain/geographic_catalog.dart';

export 'result_mode.dart';

import 'result_mode.dart';

enum LoadStatus { loading, ready, error }

class ExplorerController extends ChangeNotifier {
  ExplorerController(this.repository, {this.election = Election.demonstration});
  final ElectionRepository repository;
  final Election election;
  ElectionDataset? dataset;
  LoadStatus status = LoadStatus.loading;
  BrazilianState? selected;
  ResultMode mode = ResultMode.first;
  ThemeMode theme = ThemeMode.light;
  int _request = 0;
  bool _disposed = false;
  bool abroad = false;
  String? countryCode;
  GeographicCatalog? geography;
  bool geographyError = false;
  int _geographicRequest = 0;
  List<CountrySummary> countries = const [];
  List<MunicipalitySummary> unmappedLocalities = const [];
  CountrySummary? get country =>
      countries.where((c) => c.iso == countryCode).firstOrNull;
  String? get mapCountryCode =>
      countryCode ??
      (abroad &&
              municipalityCode != null &&
              geography?.sourceDatasetId == dataset?.provenance.version
          ? countries
                .where(
                  (c) => c.localities.any(
                    (loc) => loc.municipality.code == municipalityCode,
                  ),
                )
                .firstOrNull
                ?.iso
          : null);
  Set<String> get activeCountries => countries
      .where(
        (c) => mode.round == null
            ? c.rounds.values.any((r) => r.totals.counted > 0)
            : (c.rounds[mode.round]?.totals.counted ?? 0) > 0,
      )
      .map((c) => c.iso)
      .toSet();
  List<MunicipalitySummary> get visibleMunicipalities =>
      countryCode == null ? municipalities : country?.localities ?? const [];
  String? municipalityCode;
  List<MunicipalitySummary> municipalities = const [];
  LoadStatus municipalStatus = LoadStatus.ready;
  int _municipalRequest = 0;
  String? _loadedTerritory;
  String? get territoryCode => abroad ? 'ZZ' : selected?.code;
  bool get municipalSupported => repository is MunicipalElectionRepository;
  MunicipalitySummary? get municipality => visibleMunicipalities
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
      _aggregateCountries();
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
    ResultMode nextMode, {
    bool notify = true,
    bool overseas = false,
    String? municipality,
    String? country,
  }) {
    if (overseas) state = null;
    if (!overseas) country = null;
    if (selected == state &&
        mode == nextMode &&
        abroad == overseas &&
        countryCode == country &&
        municipalityCode == municipality) {
      return;
    }
    final territoryChanged = selected != state || abroad != overseas;
    selected = state;
    abroad = overseas;
    countryCode = country;
    municipalityCode = municipality;
    mode = nextMode;
    if (territoryChanged) {
      _municipalRequest++;
      municipalities = const [];
      countries = const [];
      unmappedLocalities = const [];
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
      _aggregateCountries();
      _loadedTerritory = uf;
      municipalStatus = LoadStatus.ready;
    } catch (_) {
      if (_disposed || request != _municipalRequest) return;
      municipalities = const [];
      countries = const [];
      unmappedLocalities = const [];
      municipalStatus = LoadStatus.error;
    }
    notifyListeners();
  }

  Map<ElectionRound, RoundResult>? get results => municipalityCode != null
      ? municipality?.rounds
      : abroad
      ? countryCode != null
            ? country?.rounds
            : dataset?.overseas?.rounds
      : dataset?.results(selected);

  Future<void> loadGeography(
    Future<GeographicCatalog> Function() loader,
  ) async {
    final request = ++_geographicRequest;
    geographyError = false;
    try {
      final value = await loader();
      if (_disposed || request != _geographicRequest) return;
      geography = value;
      _aggregateCountries();
    } catch (_) {
      if (_disposed || request != _geographicRequest) return;
      geographyError = true;
      geography = null;
      countries = const [];
    }
    if (!_disposed && request == _geographicRequest) notifyListeners();
  }

  void _aggregateCountries() {
    countries = const [];
    unmappedLocalities = const [];
    if (!abroad || municipalities.isEmpty) return;
    final catalog = geography;
    if (catalog == null ||
        catalog.sourceDatasetId != dataset?.provenance.version) {
      unmappedLocalities = municipalities;
      return;
    }
    final grouped = <String, List<MunicipalitySummary>>{};
    final missing = <MunicipalitySummary>[];
    for (final loc in municipalities) {
      final match = catalog.foreign[loc.municipality.code];
      final counts = match?.sectionsByRound ?? const <int, int>{};
      final compatible =
          counts.isEmpty ||
          (counts.length == loc.rounds.length &&
              loc.rounds.entries.every(
                (r) => counts[r.key.index + 1] == r.value.totals.sections,
              ));
      final iso = compatible ? match?.iso : null;
      if (iso == null) {
        missing.add(loc);
      } else {
        (grouped[iso] ??= []).add(loc);
      }
    }
    countries = [
      for (final e in grouped.entries)
        CountrySummary(
          e.key,
          catalog.foreign[e.value.first.municipality.code]!.country!,
          List.unmodifiable(e.value),
          aggregateLocalities(e.value),
        ),
    ]..sort((a, b) => a.name.compareTo(b.name));
    unmappedLocalities = List.unmodifiable(missing);
  }

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
