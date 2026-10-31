import '../../map/domain/geographic_catalog.dart';

/// Explanatory UI for known residuals. This does not assign countries or votes.
enum OverseasSpecialCase {
  brussels(
    '29432',
    'Bruxelas',
    'Esta localidade eleitoral reúne seções com locais de votação documentados na Bélgica e em Luxemburgo. '
        'Os resultados disponíveis estão agregados por localidade e ainda não podem ser distribuídos entre os dois países sem uma apuração específica por seção.',
    'Os votos abaixo são o agregado da localidade TSE 29432, não os resultados individuais da Bélgica ou de Luxemburgo.',
  ),
  tripoli(
    '30686',
    'Trípoli',
    'Esta localidade aparece associada administrativamente à Líbia, mas o local de votação cadastrado fica em Túnis, na Tunísia. '
        'A documentação analisada ainda não permite estabelecer um critério definitivo de atribuição territorial para seus resultados.',
    'O país de atribuição permanece pendente de esclarecimento documental.',
  );

  const OverseasSpecialCase(this.code, this.title, this.explanation, this.note);
  final String code;
  final String title;
  final String explanation;
  final String note;

  bool matches(ForeignLocality? locality) =>
      locality?.tse == code &&
      locality?.iso == null &&
      (this == brussels
          ? locality?.status == 'conflicting_section_countries'
          : locality?.status == 'no_verified_section_join');
}
