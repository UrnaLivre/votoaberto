import '../../elections/domain/election.dart';

/// One UI choice; election data continues to retain its original rounds.
enum ResultMode {
  first('1', '1º turno', ElectionRound.first),
  second('2', '2º turno', ElectionRound.second),
  comparison('comparacao', 'Comparação', null);

  const ResultMode(this.queryValue, this.label, this.round);
  final String queryValue;
  final String label;
  final ElectionRound? round;

  static ResultMode? fromQuery(Map<String, String> query) {
    final mode = query['modo'];
    if (mode != null) {
      return values.where((v) => v.queryValue == mode).firstOrNull;
    }
    final round = query['turno'];
    final view = query['visao'];
    if ((round != null && !['1', '2'].contains(round)) ||
        (view != null &&
            !['summary', 'comparison', 'insights'].contains(view))) {
      return null;
    }
    if (view == 'comparison') return comparison;
    return round == '2' ? second : first;
  }
}
