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

O ranking ordena a taxa de comparecimento do turno selecionado, dividindo comparecimento por aptos; empates são resolvidos por sigla. Filtro: 27 UFs, presidente, 2026, mock-v1. Trata-se de uma demonstração de cálculo, sem conclusão sobre eleitores reais.

Cartografia: IBGE, API de Malhas Geográficas v3, qualidade intermediária, recorte por UF. Malha simplificada, sem precisão para medição ou limites eleitorais. Uso com citação da fonte; condições e SHA-256 em docs/CARTOGRAPHY.md. O mapa não representa votos, zonas ou equipamentos.

VotoAberto é software independente do ecossistema UrnaLivre. Não é mantido, homologado ou endossado pelo TSE. Uma seção, um boletim e um equipamento físico são entidades distintas.

$interpretation''';
}
