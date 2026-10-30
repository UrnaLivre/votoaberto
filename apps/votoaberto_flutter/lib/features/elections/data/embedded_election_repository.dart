import 'dart:collection';
import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import '../domain/election.dart';
import '../domain/election_repository.dart';
import '../domain/geography.dart';

Map<String, dynamic> _verifiedJson((Uint8List, String?) input) {
  if (input.$2 != null && sha256.convert(input.$1).toString() != input.$2) {
    throw const FormatException(
      'Arquivo de dados não corresponde à versão instalada.',
    );
  }
  final value = jsonDecode(utf8.decode(input.$1));
  if (value is! Map<String, dynamic>) {
    throw const FormatException('Conteúdo de dados inválido.');
  }
  return value;
}

/// Shared AssetBundle implementation, with no network or dart:io dependency.
class EmbeddedElectionRepository implements MunicipalElectionRepository {
  EmbeddedElectionRepository({
    AssetBundle? bundle,
    required this.assetRoot,
    required this.expectedNature,
    this.expectedDatasetId,
    this.expectedManifestHash,
    this.cacheCapacity = 3,
  }) : bundle = bundle ?? rootBundle {
    if (cacheCapacity < 1) throw ArgumentError.value(cacheCapacity);
  }
  final AssetBundle bundle;
  final String assetRoot;
  final String expectedNature;
  final String? expectedDatasetId;
  final String? expectedManifestHash;
  final int cacheCapacity;
  Map<String, dynamic>? _manifest;
  ElectionDataset? _dataset;
  Future<ElectionDataset>? _loading;
  final _cities = <String, List<MunicipalitySummary>>{};
  final _pending = <String, Future<List<MunicipalitySummary>>>{};
  List<String> get cachedTerritories => List.unmodifiable(_cities.keys);

  Future<Map<String, dynamic>> _read(
    String name, {
    bool manifest = false,
  }) async {
    final info = manifest
        ? null
        : (_manifest!['artifacts'] as Map<String, dynamic>)[name]
              as Map<String, dynamic>?;
    if (!manifest && info == null) {
      throw const FormatException('Arquivo obrigatório não declarado.');
    }
    final data = await bundle.load('$assetRoot/$name');
    final bytes = data.buffer.asUint8List(
      data.offsetInBytes,
      data.lengthInBytes,
    );
    if (bytes.length > 8 * 1024 * 1024 ||
        (!manifest && bytes.length != info!['bytes'])) {
      throw const FormatException('Tamanho de arquivo inválido.');
    }
    final decoded = await compute(_verifiedJson, (
      bytes,
      manifest ? expectedManifestHash : info!['sha256'] as String,
    ));
    if (decoded['schema_version'] != 1 ||
        (!manifest && decoded['dataset_id'] != _manifest!['dataset_id'])) {
      throw const FormatException('Versão de dados incompatível.');
    }
    return decoded;
  }

  @override
  Future<ElectionDataset> load(Election election) async {
    if (election.id != Election.presidential2026.id ||
        election.year != 2026 ||
        election.office != Office.president) {
      throw const FormatException('Eleição não suportada.');
    }
    if (_dataset != null) return _dataset!;
    try {
      return await (_loading ??= _initialize(election));
    } catch (_) {
      _loading = null;
      _manifest = null;
      _dataset = null;
      rethrow;
    }
  }

  Future<ElectionDataset> _initialize(Election election) async {
    final m = await _read('manifest.json', manifest: true);
    if (m['data_nature'] != expectedNature ||
        m['validation'] != 'passed' ||
        m['local_preview'] != true ||
        (expectedDatasetId != null && m['dataset_id'] != expectedDatasetId)) {
      throw const FormatException(
        'O conjunto instalado não corresponde ao modo selecionado.',
      );
    }
    if (m['dataset_id'] is! String ||
        m['source_sqlite_sha256'] is! String ||
        !RegExp(
          r'^[a-f0-9]{64}$',
        ).hasMatch(m['source_sqlite_sha256'] as String) ||
        m['source_schema_version'] != 1 ||
        m['public_readiness'] is! Map ||
        m['territories'] is! List ||
        m['elections'] is! List) {
      throw const FormatException('Manifesto incompleto.');
    }
    final territories = (m['territories'] as List).cast<String>();
    if (expectedNature == 'official-derived' &&
        (territories.length != 28 || !territories.contains('ZZ'))) {
      throw const FormatException(
        'A prévia nacional exige as 27 UFs e o exterior.',
      );
    }
    if (territories.toSet().length != territories.length ||
        territories.any(
          (uf) => uf != 'ZZ' && BrazilianState.fromCode(uf) == null,
        )) {
      throw const FormatException('Abrangência inválida.');
    }
    final elections = (m['elections'] as List).cast<Map<String, dynamic>>();
    if (elections.isEmpty ||
        elections.map((e) => e['round']).toSet().length != elections.length ||
        elections.any(
          (e) =>
              e['year'] != election.year ||
              e['office'] != 'president' ||
              ![1, 2].contains(e['round']),
        )) {
      throw const FormatException('Eleição/turno incompatível.');
    }
    for (final e in elections) {
      final catalog = (e['candidates'] as List).cast<Map<String, dynamic>>();
      if (catalog.isEmpty ||
          catalog.map((c) => c['id']).toSet().length != catalog.length ||
          catalog.any(
            (c) =>
                c['id'] != '${e['id']}:${c['number']}' ||
                c['name'] is! String ||
                c['number'] is! String,
          )) {
        throw const FormatException('Catálogo de candidatos inválido.');
      }
    }
    final artifacts = m['artifacts'] as Map<String, dynamic>;
    for (final name in [
      'national.json',
      'states.json',
      'validation.json',
      for (final uf in territories) 'municipalities/$uf.json',
    ]) {
      final item = artifacts[name];
      if (item is! Map ||
          item['bytes'] is! int ||
          item['sha256'] is! String ||
          !RegExp(r'^[a-f0-9]{64}$').hasMatch(item['sha256'] as String)) {
        throw const FormatException(
          'Arquivo obrigatório ausente no manifesto.',
        );
      }
    }
    _manifest = m;
    final national = await _read('national.json');
    final states = await _read('states.json');
    final summaries = <StateSummary>[];
    NationalSummary? abroad;
    final seen = <String>{};
    for (final entry
        in (states['territories'] as List).cast<Map<String, dynamic>>()) {
      final uf = entry['code'] as String;
      if (!territories.contains(uf) || !seen.add(uf)) {
        throw const FormatException('UF duplicada ou inválida.');
      }
      final rounds = _rounds(entry['rounds']);
      if (expectedNature == 'official-derived' && rounds.length != 2) {
        throw const FormatException(
          'A prévia nacional exige os dois turnos em cada abrangência.',
        );
      }
      if (uf == 'ZZ') {
        abroad = NationalSummary(rounds);
      } else {
        summaries.add(
          StateSummary(state: BrazilianState.fromCode(uf)!, rounds: rounds),
        );
      }
    }
    if (seen.length != territories.length ||
        national['includes_abroad'] != seen.contains('ZZ')) {
      throw const FormatException('Cobertura inicial inconsistente.');
    }
    _dataset = ElectionDataset(
      election: election,
      provenance: DataProvenance(
        source: m['attribution'] as String,
        version: m['dataset_id'] as String,
        synthetic: m['data_nature'] == 'synthetic',
        sourceRelease: m['source_release'] as String,
        sha256: m['source_sqlite_sha256'] as String,
        publicReadiness: (m['public_readiness'] as Map)['status'] as String,
        transformations:
            'Somas por códigos TSE de município e UF; totais de seção agregados separadamente. '
            'Brasil inclui ZZ; Brasil doméstico exclui ZZ. Campos ausentes não são zero. '
            'Integridade matemática e reconciliação conferidas na origem; '
            'completude de todas as seções e autenticação de origem não atestadas.',
      ),
      states: summaries,
      national: NationalSummary(_rounds(national['rounds'])),
      domestic: NationalSummary(_rounds(national['domestic_rounds'])),
      overseas: abroad,
    );
    _assertSum([
      for (final state in summaries) state.rounds,
    ], _dataset!.domestic!.rounds);
    _assertSum([
      for (final state in summaries) state.rounds,
      if (abroad != null) abroad.rounds,
    ], _dataset!.national.rounds);
    return _dataset!;
  }

  void _assertSum(
    List<Map<ElectionRound, RoundResult>> parts,
    Map<ElectionRound, RoundResult> total,
  ) {
    final rounds = parts.expand((p) => p.keys).toSet();
    if (rounds.length != total.length || !rounds.containsAll(total.keys)) {
      throw const FormatException('Turnos agregados incompatíveis.');
    }
    for (final round in rounds) {
      final records = parts
          .map((p) => p[round])
          .whereType<RoundResult>()
          .toList();
      final target = total[round]!;
      final metrics = <String, int? Function(VoteTotals)>{
        'counted': (t) => t.counted,
        'valid': (t) => t.valid,
        'blank': (t) => t.blank,
        'null': (t) => t.invalid,
        'eligible': (t) => t.eligible,
        'turnout': (t) => t.turnout,
        'abstention': (t) => t.abstention,
      };
      for (final entry in metrics.entries) {
        final values = records
            .map((r) => entry.value(r.totals))
            .whereType<int>()
            .toList();
        final sum = values.isEmpty ? null : values.fold(0, (a, b) => a + b);
        final available = records.fold(
          0,
          (a, r) => a + r.totals.availableSections[entry.key]!,
        );
        if (sum != entry.value(target.totals) ||
            available != target.totals.availableSections[entry.key]) {
          throw const FormatException('Soma dos totais agregados divergente.');
        }
      }
      final votes = <String, int>{};
      for (final record in records) {
        for (final c in record.candidates) {
          votes[c.candidate.id] = (votes[c.candidate.id] ?? 0) + c.votes;
        }
      }
      if (votes.length != target.candidates.length ||
          target.candidates.any((c) => votes[c.candidate.id] != c.votes) ||
          records.fold(0, (a, r) => a + r.totals.sections) !=
              target.totals.sections) {
        throw const FormatException(
          'Soma dos resultados agregados divergente.',
        );
      }
    }
  }

  Map<ElectionRound, RoundResult> _rounds(dynamic raw) {
    final result = <ElectionRound, RoundResult>{};
    for (final row in (raw as List).cast<Map<String, dynamic>>()) {
      final election = (_manifest!['elections'] as List)
          .cast<Map<String, dynamic>>()
          .where((e) => e['id'] == row['election'])
          .firstOrNull;
      if (election == null || row['round'] != election['round']) {
        throw const FormatException('Eleição/turno divergente.');
      }
      final round = row['round'] == 1
          ? ElectionRound.first
          : ElectionRound.second;
      if (result.containsKey(round)) {
        throw const FormatException('Turno duplicado.');
      }
      final totals = row['totals'] as Map<String, dynamic>;
      final available = (row['available_sections'] as Map<String, dynamic>)
          .cast<String, int>();
      final sections = row['sections'] as int;
      final keys = [
        'counted',
        'valid',
        'blank',
        'null',
        'eligible',
        'turnout',
        'abstention',
      ];
      if (sections < 1 ||
          keys.any(
            (k) =>
                !available.containsKey(k) ||
                available[k]! < 0 ||
                available[k]! > sections ||
                ((totals[k] == null) != (available[k] == 0)),
          )) {
        throw const FormatException('Disponibilidade inválida.');
      }
      final catalog = {
        for (final c
            in (election['candidates'] as List).cast<Map<String, dynamic>>())
          c['id'] as String: Candidate(
            c['id'] as String,
            c['name'] as String,
            number: c['number'] as String,
            sourceCandidateId: c['source_candidate_id'] as String?,
          ),
      };
      final votes = (row['candidates'] as Map<String, dynamic>)
          .cast<String, int>();
      if (votes.keys.any((id) => !catalog.containsKey(id))) {
        throw const FormatException('Candidato desconhecido.');
      }
      final candidates = [
        for (final entry in votes.entries)
          CandidateResult(catalog[entry.key]!, entry.value),
      ]..sort((a, b) => a.candidate.number!.compareTo(b.candidate.number!));
      final t = VoteTotals(
        eligible: totals['eligible'] as int?,
        valid: totals['valid'] as int,
        blank: totals['blank'] as int?,
        invalid: totals['null'] as int?,
        counted: totals['counted'] as int,
        turnoutValue: totals['turnout'] as int?,
        abstentionValue: totals['abstention'] as int?,
        deriveParticipation: false,
        sections: sections,
        availableSections: Map.unmodifiable(available),
      );
      if ((t.complete('valid') &&
              t.complete('blank') &&
              t.complete('null') &&
              t.valid + t.blank! + t.invalid! != t.counted) ||
          (t.complete('turnout') && t.turnout != t.counted) ||
          (t.complete('eligible') &&
              t.complete('turnout') &&
              t.complete('abstention') &&
              t.eligible != t.turnout! + t.abstention!)) {
        throw const FormatException('Totais incompatíveis.');
      }
      result[round] = RoundResult(
        round: round,
        totals: t,
        candidates: candidates,
        electionId: row['election'] as String,
        unreportedCandidates: List.unmodifiable(
          catalog.entries
              .where((e) => !votes.containsKey(e.key))
              .map((e) => e.value),
        ),
      );
    }
    return result;
  }

  @override
  Future<List<MunicipalitySummary>> loadMunicipalities(
    Election election,
    String territory,
  ) async {
    await load(election);
    if (!(_manifest!['territories'] as List).contains(territory)) {
      throw const FormatException('Abrangência indisponível.');
    }
    final cached = _cities.remove(territory);
    if (cached != null) {
      _cities[territory] = cached;
      return cached;
    }
    try {
      return await (_pending[territory] ??= _loadCities(territory));
    } finally {
      _pending.remove(territory);
    }
  }

  Future<List<MunicipalitySummary>> _loadCities(String uf) async {
    final json = await _read('municipalities/$uf.json');
    if (json['uf'] != uf) {
      throw const FormatException('UF municipal divergente.');
    }
    final seen = <String>{};
    final cities = <MunicipalitySummary>[];
    for (final city
        in (json['municipalities'] as List).cast<Map<String, dynamic>>()) {
      final code = city['code'] as String;
      final name = city['name'] as String;
      if (code.isEmpty || name.isEmpty || !seen.add(code)) {
        throw const FormatException('Município duplicado/inválido.');
      }
      cities.add(
        MunicipalitySummary(
          municipality: Municipality(
            code: code,
            name: name,
            state: BrazilianState.fromCode(uf),
            territoryCode: uf,
          ),
          rounds: _rounds(city['rounds']),
        ),
      );
    }
    if (cities.length != (_manifest!['municipality_counts'] as Map)[uf]) {
      throw const FormatException('Contagem municipal divergente.');
    }
    cities.sort((a, b) => a.municipality.name.compareTo(b.municipality.name));
    final parent = uf == 'ZZ'
        ? _dataset!.overseas!.rounds
        : _dataset!.states.firstWhere((s) => s.state.code == uf).rounds;
    _assertSum([for (final city in cities) city.rounds], parent);
    final result = List<MunicipalitySummary>.unmodifiable(cities);
    _cities[uf] = result;
    while (_cities.length > cacheCapacity) {
      _cities.remove(_cities.keys.first);
    }
    return result;
  }
}
