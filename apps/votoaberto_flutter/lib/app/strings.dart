/// Shared pt-BR copy. Keep domain objects free of interface copy; migrate this
/// catalog to ARB when adding a second locale.
abstract final class AppStrings {
  static const title = 'VotoAberto';
  static const demo = 'DEMONSTRAÇÃO — DADOS FICTÍCIOS';
  static const independence = 'Uma iniciativa UrnaLivre. Independente do TSE.';
  static const search = 'Buscar estado ou sigla';
  static const noState = 'Nenhuma UF encontrada. Tente o nome ou a sigla.';
  static const loadError = 'Não foi possível carregar os dados selecionados.';
  static const empty = 'Não há dados para este recorte.';
  static const future =
      'Consultas por zona, seção e boletim serão acrescentadas em outro marco.';
  static const interpretation =
      'Diferenças entre turnos não identificam transferência de votos entre eleitores.';
  static const methodology = 'Fontes e metodologia';
  static const methodologyBody =
      '''Esta versão usa somente números fictícios e candidatos A, B, C e D. Nenhum resultado eleitoral do TSE foi importado.

Fonte dos números: gerador sintético VotoAberto, mock-v1. A visão Brasil soma as 27 UFs e não inclui o exterior. Os dois turnos usam o mesmo eleitorado apto por UF.

Comparecimento = válidos + brancos + nulos. Abstenção = aptos − comparecimento. Taxas de comparecimento e abstenção dividem por aptos; percentuais dos candidatos dividem por votos válidos. Brancos e nulos são contagens. Variação relativa = (2º − 1º) / 1º; com base zero, não é definida. Um candidato ausente do 2º turno não é tratado como tendo perdido todos os votos.

Cartografia: IBGE, API de Malhas Geográficas v3, qualidade intermediária, recorte por UF. Malha simplificada, sem precisão para medição ou limites eleitorais. Uso com citação da fonte; condições e SHA-256 em docs/CARTOGRAPHY.md. O mapa não representa votos, zonas ou equipamentos.

VotoAberto é software independente do ecossistema UrnaLivre. Não é mantido, homologado ou endossado pelo TSE. Uma seção, um boletim e um equipamento físico são entidades distintas.

$interpretation''';
  static const geographicMethodology =
      'Geografia: municípios associados por UF e identificadores TSE/IBGE da correspondência oficial gerada em 25/10/2026. '
      'Pontos do IBGE, Localidades do Brasil (Censo 2022, publicação de 2025), convertidos de SIRGAS2000 para WGS84. '
      'O marcador representa sede municipal ou ponto representativo, sem indicar urna ou local de votação.\n\n'
      'Mundo mostra somente a votação brasileira no exterior, já incluída no total Brasil. '
      'Países e territórios são associados por chaves de seção do edital de carga TRE-DF de setembro de 2026, conferidas com os registros observados. '
      'Associações ausentes ou contraditórias ficam sem país confirmado e mantêm seus resultados. '
      'Agregações parciais são identificadas; percentuais de país ficam indisponíveis enquanto houver lacunas de correspondência.\n\n'
      'Mapa mundial: Natural Earth 5.1.1, unidades cartográficas 1:50m simplificadas. Dados em domínio público. '
      'Fronteiras de apresentação não expressam reconhecimento oficial de disputas territoriais. '
      'Créditos: IBGE, TSE, TRE-DF e colaboradores Natural Earth. Fontes, versões, transformações e hashes em docs/GEOGRAPHIC_EXPLORER.md.';
}
