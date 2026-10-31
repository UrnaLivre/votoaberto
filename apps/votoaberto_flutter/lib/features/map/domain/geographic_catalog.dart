import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/services.dart';
import 'brazil_geometry.dart';
import 'country_evidence.dart';

class MunicipalLocation {
  const MunicipalLocation(
    this.uf,
    this.tse,
    this.ibge,
    this.latitude,
    this.longitude,
    this.kind,
  );
  final String uf;
  final String tse;
  final String ibge;
  final double latitude;
  final double longitude;
  final String kind;
  Offset get point => BrazilGeometry.project(longitude, latitude);
}

class ForeignLocality {
  const ForeignLocality(
    this.tse,
    this.iso,
    this.country,
    this.status, {
    this.sectionsByRound = const {},
  });
  final String tse;
  final String? iso;
  final String? country;
  final String status;
  final Map<int, int> sectionsByRound;
}

class GeographicCatalog {
  GeographicCatalog({
    required this.locations,
    required this.foreign,
    required this.sourceDatasetId,
  });
  final Map<String, MunicipalLocation> locations;
  final Map<String, ForeignLocality> foreign;
  final String sourceDatasetId;
  MunicipalLocation? municipal(String? uf, String? tse) =>
      locations['$uf/$tse'];

  factory GeographicCatalog.decode(String municipal, String overseas) {
    final points = jsonDecode(municipal) as Map<String, dynamic>;
    final abroad = jsonDecode(overseas) as Map<String, dynamic>;
    if (points['schema_version'] != 1 ||
        points['crs'] != 'EPSG:4326' ||
        ![1, 2].contains(abroad['schema_version'])) {
      throw const FormatException('Versão geográfica incompatível');
    }
    if (abroad['schema_version'] == 1 &&
        abroad.containsKey('evidence_sources')) {
      throw const FormatException('Evidência direta exige contrato v2');
    }
    final locations = <String, MunicipalLocation>{};
    for (final raw in points['locations'] as List) {
      final row = raw as List;
      final lat = (row[3] as num).toDouble();
      final lon = (row[4] as num).toDouble();
      final key = '${row[0]}/${row[1]}';
      if (row[0] is! String ||
          row[1] is! String ||
          row[2] is! String ||
          !lat.isFinite ||
          !lon.isFinite ||
          lat.abs() > 90 ||
          lon.abs() > 180 ||
          !['seat', 'representative'].contains(row[5]) ||
          locations.containsKey(key)) {
        throw const FormatException('Ponto municipal inválido ou duplicado');
      }
      locations[key] = MunicipalLocation(
        row[0] as String,
        row[1] as String,
        row[2] as String,
        lat,
        lon,
        row[5] as String,
      );
    }
    final foreign = <String, ForeignLocality>{};
    final owners = <String, String>{};
    final sources =
        abroad['evidence_sources'] as Map<String, dynamic>? ?? const {};
    for (final row
        in (abroad['localities'] as List).cast<Map<String, dynamic>>()) {
      final code = row['tse'] as String;
      final iso = row['iso'] as String?;
      if (foreign.containsKey(code) ||
          !RegExp(r'^[0-9]+$').hasMatch(code) ||
          int.parse(code) == 0) {
        throw const FormatException('Correspondência exterior sem evidência');
      }
      final counts = validateCountryEvidence(row, sources);
      if (iso != null) {
        for (final e in row['evidence'] as List) {
          final keys = e is List
              ? [
                  for (final turn in [1, 2]) '$turn/${e[1]}/${e[2]}',
                ]
              : ['${e['round']}/${e['zone']}/${e['section']}'];
          for (final key in keys) {
            if (owners.containsKey(key) && owners[key] != code) {
              throw const FormatException('Seção com múltiplos proprietários');
            }
            owners[key] = code;
          }
        }
      }
      foreign[code] = ForeignLocality(
        code,
        iso,
        row['country'] as String?,
        row['status'] as String,
        sectionsByRound: counts,
      );
    }
    return GeographicCatalog(
      locations: Map.unmodifiable(locations),
      foreign: Map.unmodifiable(foreign),
      sourceDatasetId: abroad['source_dataset_id'] as String,
    );
  }
}

/// Static files only, including Web. Hash pins prevent accidental mixed versions.
class GeographicAssets {
  GeographicAssets({AssetBundle? bundle}) : bundle = bundle ?? rootBundle;
  final AssetBundle bundle;
  static const manifestHash =
      'ab4be0d225aa2209c976ec2238c1faa1a4c922d8d2f80ac8f87ba078f5746c47';
  Future<Map<String, dynamic>>? _manifest;
  Future<Map<String, dynamic>> _loadManifest() async {
    final bytes = await bundle.load('assets/geo/manifest.json');
    final data = bytes.buffer.asUint8List(
      bytes.offsetInBytes,
      bytes.lengthInBytes,
    );
    if (sha256.convert(data).toString() != manifestHash) {
      throw const FormatException('Manifesto geográfico divergente');
    }
    final value = jsonDecode(utf8.decode(data)) as Map<String, dynamic>;
    if (value['schema_version'] != 1) {
      throw const FormatException('Versão geográfica inválida');
    }
    return value;
  }

  Future<String> read(String name) async {
    final m = await (_manifest ??= _loadManifest());
    final info =
        (m['artifacts'] as Map<String, dynamic>)[name] as Map<String, dynamic>;
    final bytes = await bundle.load('assets/geo/$name');
    final data = bytes.buffer.asUint8List(
      bytes.offsetInBytes,
      bytes.lengthInBytes,
    );
    if (data.length != info['bytes'] ||
        sha256.convert(data).toString() != info['sha256']) {
      throw const FormatException('Asset geográfico divergente');
    }
    return utf8.decode(data);
  }

  Future<GeographicCatalog> load() async {
    final sources = await Future.wait([
      read('municipal_locations.json'),
      read('overseas_correspondence.json'),
    ]);
    return GeographicCatalog.decode(sources[0], sources[1]);
  }
}
