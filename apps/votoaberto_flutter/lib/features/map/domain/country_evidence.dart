/// Validates reviewed documentary assertions; never geocodes city names.
Map<int, int> validateCountryEvidence(
  Map<String, dynamic> row,
  Map<String, dynamic> sources,
) {
  Never invalid() => throw const FormatException(
    'Correspondência exterior sem evidência documental compatível',
  );
  bool id(dynamic value) =>
      value is String && RegExp(r'^[1-9][0-9]*$').hasMatch(value);
  final iso = row['iso'];
  if (iso == null) {
    if (row['country'] != null) invalid();
    return const {};
  }
  if (iso is! String ||
      !RegExp(r'^[A-Z]{2}$').hasMatch(iso) ||
      row['country'] is! String ||
      (row['country'] as String).trim().isEmpty ||
      row['evidence'] is! List ||
      (row['evidence'] as List).isEmpty) {
    invalid();
  }
  final seen = <String>{};
  if (row['status'] == 'verified_section_join') {
    for (final e in row['evidence'] as List) {
      if (e is! List ||
          e.length != 4 ||
          e[0] != iso ||
          !id(e[1]) ||
          !id(e[2]) ||
          e[3] is! int ||
          (e[3] as int) < 1 ||
          !seen.add(e.join('/'))) {
        invalid();
      }
    }
    return const {};
  }
  if (row['status'] != 'verified_official_section_register' ||
      row['candidate_countries'] is! List ||
      (row['candidate_countries'] as List).length != 1 ||
      (row['candidate_countries'] as List).single != iso) {
    invalid();
  }
  const countryFields = ['DS_ENDERECO', 'NM_BAIRRO', 'NM_LOCAL_VOTACAO'];
  final counts = <int, int>{};
  final locations = <String>{};
  bool containsLiteral(String value, String literal) => RegExp(
    r'(?<!\w)' + RegExp.escape(literal) + r'(?!\w)',
    unicode: true,
  ).hasMatch(value);
  for (final raw in row['evidence'] as List) {
    if (raw is! Map<String, dynamic>) invalid();
    final e = raw;
    final source = sources[e['source']];
    if (source is! Map<String, dynamic>) invalid();
    final url = Uri.tryParse(source['url'] as String? ?? '');
    if (url == null ||
        url.scheme != 'https' ||
        ![
          'cdn.tse.jus.br',
          'www.tse.jus.br',
          'www.tre-df.jus.br',
        ].contains(url.host) ||
        source['election_year'] != 2026 ||
        source['version'] is! String ||
        (source['version'] as String).isEmpty ||
        source['member'] is! String ||
        (source['member'] as String).isEmpty) {
      invalid();
    }
    for (final key in ['sha256', 'member_sha256']) {
      if (source[key] is! String ||
          !RegExp(r'^[a-f0-9]{64}$').hasMatch(source[key] as String)) {
        invalid();
      }
    }
    final field = e['country_field'];
    final literal = e['country_literal'];
    final fields = e['fields'];
    final labels = source['reviewed_country_literals'];
    if (!countryFields.contains(field) ||
        literal is! String ||
        literal.isEmpty ||
        fields is! Map<String, dynamic> ||
        fields[field] is! String ||
        labels is! Map<String, dynamic> ||
        labels[iso] is! List ||
        !(labels[iso] as List).contains(literal) ||
        !containsLiteral(fields[field] as String, literal) ||
        e['iso'] != iso ||
        e['tse'] != row['tse'] ||
        e['round'] is! int ||
        ![1, 2].contains(e['round']) ||
        !id(e['zone']) ||
        !id(e['section']) ||
        !id(e['local']) ||
        e['record'] is! int ||
        (e['record'] as int) < 2 ||
        e['primary_section'] != '-1') {
      invalid();
    }
    if (!seen.add('${e['round']}/${e['zone']}/${e['section']}')) invalid();
    for (final other in labels.entries) {
      if (other.key == iso) continue;
      for (final value in other.value as List) {
        for (final key in countryFields) {
          if (containsLiteral(fields[key] as String? ?? '', value as String)) {
            invalid();
          }
        }
      }
    }
    locations.add(countryFields.map((f) => fields[f]).join('\u0000'));
    final turn = e['round'] as int;
    counts[turn] = (counts[turn] ?? 0) + 1;
  }
  final turns = counts.keys.toList()..sort();
  if (row['verified_rounds'] is! List ||
      (row['verified_rounds'] as List).join(',') != turns.join(',') ||
      locations.length != 1) {
    invalid();
  }
  return Map.unmodifiable(counts);
}
