import 'package:intl/intl.dart';

final _integer = NumberFormat.decimalPattern('pt_BR');
final _percent = NumberFormat('0.0', 'pt_BR');
String count(int value) => _integer.format(value);
String percent(double value) => '${_percent.format(value * 100)}%';
String signedCount(int value) => '${value > 0 ? '+' : ''}${count(value)}';
String signedPercent(double? value) => value == null
    ? 'sem base de comparação'
    : '${value > 0 ? '+' : ''}${percent(value)}';

String normalizeSearch(String value) {
  var result = value.trim().toLowerCase();
  const accents = {
    'á': 'a',
    'à': 'a',
    'â': 'a',
    'ã': 'a',
    'é': 'e',
    'ê': 'e',
    'í': 'i',
    'ó': 'o',
    'ô': 'o',
    'õ': 'o',
    'ú': 'u',
    'ç': 'c',
  };
  accents.forEach(
    (key, replacement) => result = result.replaceAll(key, replacement),
  );
  return result;
}
