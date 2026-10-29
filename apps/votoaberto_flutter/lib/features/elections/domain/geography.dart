/// IBGE identifiers are strings. ZZ is an electoral scope, never a 28th UF.
enum BrazilianState {
  ac('12', 'AC', 'Acre'),
  al('27', 'AL', 'Alagoas'),
  ap('16', 'AP', 'Amapá'),
  am('13', 'AM', 'Amazonas'),
  ba('29', 'BA', 'Bahia'),
  ce('23', 'CE', 'Ceará'),
  df('53', 'DF', 'Distrito Federal'),
  es('32', 'ES', 'Espírito Santo'),
  go('52', 'GO', 'Goiás'),
  ma('21', 'MA', 'Maranhão'),
  mt('51', 'MT', 'Mato Grosso'),
  ms('50', 'MS', 'Mato Grosso do Sul'),
  mg('31', 'MG', 'Minas Gerais'),
  pa('15', 'PA', 'Pará'),
  pb('25', 'PB', 'Paraíba'),
  pr('41', 'PR', 'Paraná'),
  pe('26', 'PE', 'Pernambuco'),
  pi('22', 'PI', 'Piauí'),
  rj('33', 'RJ', 'Rio de Janeiro'),
  rn('24', 'RN', 'Rio Grande do Norte'),
  rs('43', 'RS', 'Rio Grande do Sul'),
  ro('11', 'RO', 'Rondônia'),
  rr('14', 'RR', 'Roraima'),
  sc('42', 'SC', 'Santa Catarina'),
  sp('35', 'SP', 'São Paulo'),
  se('28', 'SE', 'Sergipe'),
  to('17', 'TO', 'Tocantins');

  const BrazilianState(this.ibgeCode, this.code, this.name);
  final String ibgeCode;
  final String code;
  final String name;

  static BrazilianState? fromCode(String? value) {
    for (final state in values) {
      if (state.code == value?.toUpperCase()) return state;
    }
    return null;
  }
}

enum ElectoralTerritory { domestic, abroad }

class Municipality {
  const Municipality({
    required this.code,
    required this.name,
    required this.state,
  });

  /// TSE code; not interchangeable with an IBGE municipality code.
  final String code;
  final String name;
  final BrazilianState state;
}

class ElectoralZone {
  const ElectoralZone(this.code);
  final String code;
}

class ElectoralSection {
  const ElectoralSection(this.code);

  /// A section identifier does not identify a physical voting machine.
  final String code;
}

/// Future query hierarchy. Additional source fields can disambiguate records.
class ElectoralLocationKey {
  ElectoralLocationKey({
    required this.electionId,
    required this.round,
    required this.territoryCode,
    required this.municipalityCode,
    required this.zoneCode,
    required this.sectionCode,
    Map<String, String> additional = const {},
  }) : additional = Map.unmodifiable(additional);

  final String electionId;
  final int round;

  /// UF abbreviation or ZZ for abroad.
  final String territoryCode;
  final String municipalityCode;
  final String zoneCode;
  final String sectionCode;
  final Map<String, String> additional;
}
