import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:votoaberto/features/map/domain/geographic_catalog.dart';

Map<String, dynamic> registerFixture() {
  final id = jsonDecode(
    File('assets/data/synthetic/manifest.json').readAsStringSync(),
  )['dataset_id'];
  return {
    'schema_version': 2,
    'source_dataset_id': id,
    'evidence_sources': {
      'fixture': {
        'url': 'https://cdn.tse.jus.br/fixture-not-a-real-source.zip',
        'sha256': List.filled(64, 'a').join(),
        'member_sha256': List.filled(64, 'b').join(),
        'member': 'fictional.csv',
        'election_year': 2026,
        'version': 'fixture',
        'reviewed_country_literals': {
          'US': ['PAIS FICTICIO A'],
          'PT': ['PAIS FICTICIO B'],
        },
      },
    },
    'localities': [
      for (final (code, iso, label, turns) in [
        ('00001', 'US', 'A', [1, 2]),
        ('00002', 'PT', 'B', [1]),
      ])
        {
          'tse': code,
          'name': 'LOCALIDADE FICTICIA',
          'iso': iso,
          'country': 'País fictício $label',
          'status': 'verified_official_section_register',
          'candidate_countries': [iso],
          'verified_rounds': turns,
          'evidence': [
            for (final turn in turns)
              {
                'source': 'fixture',
                'record': turn + 1,
                'tse': code,
                'iso': iso,
                'round': turn,
                'zone': '1',
                'section': int.parse(code).toString(),
                'local': '1015',
                'primary_section': '-1',
                'country_field': 'DS_ENDERECO',
                'country_literal': 'PAIS FICTICIO $label',
                'fields': {
                  'DS_ENDERECO': 'RUA FICTICIA, PAIS FICTICIO $label',
                  'NM_BAIRRO': 'CENTRO',
                  'NM_LOCAL_VOTACAO': 'LOCAL FICTICIO',
                },
              },
          ],
        },
    ],
  };
}

GeographicCatalog registerCatalog([Map<String, dynamic>? data]) =>
    GeographicCatalog.decode(
      jsonEncode({
        'schema_version': 1,
        'crs': 'EPSG:4326',
        'locations': <Object>[],
      }),
      jsonEncode(data ?? registerFixture()),
    );

void main() {
  test(
    'official identifier register retains exact per-turn section membership',
    () {
      final catalog = registerCatalog();
      expect(catalog.foreign['00001']!.iso, 'US');
      expect(catalog.foreign['00001']!.sectionsByRound, {1: 1, 2: 1});
      expect(catalog.foreign['00002']!.sectionsByRound, {1: 1});
    },
  );
  for (final mutation in [
    'name',
    'code',
    'country',
    'duplicate',
    'source',
    'hash',
    'year',
    'turn',
    'aggregated',
    'multi',
    'address',
    'owner',
    'schema',
  ]) {
    test('rejects incompatible documentary evidence: $mutation', () {
      final data = registerFixture();
      final rows = data['localities'] as List;
      final e = rows[0]['evidence'][0] as Map<String, dynamic>;
      final source = data['evidence_sources']['fixture'];
      switch (mutation) {
        case 'name':
          e['country_field'] = 'NM_MUNICIPIO';
          e['fields']['NM_MUNICIPIO'] = e['country_literal'];
        case 'code':
          e['tse'] = '99999';
        case 'country':
          e['iso'] = 'PT';
        case 'duplicate':
          rows[0]['evidence'].add(Map<String, Object>.from(e));
        case 'source':
          source['url'] = 'https://example.org/fixture.csv';
        case 'hash':
          source['member_sha256'] = 'unknown';
        case 'year':
          source['election_year'] = 2022;
        case 'turn':
          rows[0]['evidence'].removeLast();
        case 'aggregated':
          e['primary_section'] = '2';
        case 'multi':
          rows[0]['candidate_countries'] = ['US', 'PT'];
        case 'address':
          e['fields']['NM_BAIRRO'] = 'PAIS FICTICIO B';
        case 'owner':
          rows[1]['evidence'][0]['section'] = '1';
        case 'schema':
          data['schema_version'] = 1;
      }
      expect(() => registerCatalog(data), throwsFormatException);
    });
  }
}
