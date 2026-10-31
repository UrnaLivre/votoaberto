import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/features/map/domain/geographic_catalog.dart';
import 'package:votoaberto/features/map/domain/world_geometry.dart';

class GeoBundle extends CachingAssetBundle {
  final calls = <String>[];
  final files = {
    for (final file in Directory('assets/geo').listSync().whereType<File>())
      file.path.replaceAll('\\', '/'): file.readAsBytesSync(),
  };
  @override
  Future<ByteData> load(String key) async {
    calls.add(key);
    final bytes = files[key];
    if (bytes == null) throw StateError('Missing local asset');
    return ByteData.sublistView(bytes);
  }
}

void main() {
  test(
    'verified local geographic package preserves TSE/IBGE identity and all domestic points',
    () async {
      final bundle = GeoBundle();
      final assets = GeographicAssets(bundle: bundle);
      final clock = Stopwatch()..start();
      final catalog = await assets.load();
      expect(catalog.locations.length, 5571);
      final bujari = catalog.municipal('AC', '1007')!;
      expect(bujari.tse, '1007');
      expect(bujari.ibge, '1200138');
      expect(catalog.municipal('AC', '1200138'), isNull);
      expect(catalog.municipal('ZZ', '1007'), isNull);
      expect(catalog.municipal('AC', 'unconfirmed'), isNull);
      expect(
        catalog.locations.values.where((p) => p.ibge == '2605459').single.kind,
        'representative',
      );
      expect(
        catalog.locations.values.where((p) => p.uf == 'DF').single.kind,
        'representative',
      );
      expect(catalog.foreign.values.where((p) => p.iso != null).length, 143);
      expect(
        catalog.foreign.values.map((p) => p.iso).whereType<String>().toSet(),
        hasLength(100),
      );
      expect(catalog.foreign['29432']!.iso, isNull);
      expect(catalog.foreign['30686']!.iso, isNull);
      expect(catalog.foreign['29173']!.iso, 'NP');
      expect(catalog.foreign['29173']!.sectionsByRound, {1: 1, 2: 1});
      final catalogMs = clock.elapsedMicroseconds / 1000;
      clock.reset();
      final world = WorldGeometry.decode(await assets.read('world.geojson'));
      final worldMs = clock.elapsedMicroseconds / 1000;
      final mapped = catalog.foreign.values
          .map((p) => p.iso)
          .whereType<String>()
          .toSet();
      expect(
        world.countries.map((c) => c.iso).toSet().containsAll(mapped),
        isTrue,
      );
      expect(world.countries.where((c) => c.iso == 'GF'), hasLength(1));
      expect(world.viewFor('FJ').width, lessThan(20));
      expect(world.viewFor('RU').width, lessThan(230));
      expect(world.hitTest(const Offset(-150, -64), {'US'}), 'US');
      expect(world.hitTest(const Offset(170, -65), {'RU'}), 'RU');
      expect(
        bundle.calls.where((p) => p.endsWith('manifest.json')),
        hasLength(1),
      );
      expect(bundle.calls.every((p) => p.startsWith('assets/geo/')), isTrue);
      // Diagnostic only: no machine-dependent performance assertion in CI.
      // ignore: avoid_print
      print(
        'GEOGRAPHY_QA ${jsonEncode({'catalog_ms': catalogMs, 'world_ms': worldMs, 'world_features': world.countries.length})}',
      );
    },
  );

  for (final filename in [
    'manifest.json',
    'municipal_locations.json',
    'overseas_correspondence.json',
    'world.geojson',
  ]) {
    test('tampered $filename is refused with no unverified fallback', () async {
      final bundle = GeoBundle();
      bundle.files['assets/geo/$filename'] = Uint8List.fromList(
        utf8.encode('{}'),
      );
      final assets = GeographicAssets(bundle: bundle);
      if (filename == 'world.geojson') {
        await expectLater(assets.read(filename), throwsFormatException);
      } else {
        await expectLater(assets.load(), throwsFormatException);
      }
    });
  }

  test(
    'unverified country or invalid point cannot be decoded as confirmed geography',
    () {
      final points = {
        'schema_version': 1,
        'crs': 'EPSG:4326',
        'locations': [
          ['SC', '001', '9990001', 91, -50, 'seat'],
        ],
      };
      final foreign = {
        'schema_version': 1,
        'source_dataset_id': 'synthetic',
        'localities': <Object>[],
      };
      expect(
        () => GeographicCatalog.decode(jsonEncode(points), jsonEncode(foreign)),
        throwsFormatException,
      );
      points['locations'] = <Object>[];
      foreign['localities'] = [
        {
          'tse': '001',
          'iso': 'US',
          'country': 'Fictício',
          'status': 'name_guess',
          'evidence': <Object>[],
        },
      ];
      expect(
        () => GeographicCatalog.decode(jsonEncode(points), jsonEncode(foreign)),
        throwsFormatException,
      );
    },
  );
}
