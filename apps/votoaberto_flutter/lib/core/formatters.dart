import 'package:intl/intl.dart';

final _integer = NumberFormat.decimalPattern('pt_BR');
final _percent = NumberFormat('0.0', 'pt_BR');
String count(int? value) =>
    value == null ? 'Indisponível' : _integer.format(value);
String percent(double? value) =>
    value == null ? 'Indisponível' : '${_percent.format(value * 100)}%';
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
    'ä': 'a',
    'å': 'a',
    'è': 'e',
    'ë': 'e',
    'ì': 'i',
    'ï': 'i',
    'ò': 'o',
    'ö': 'o',
    'ù': 'u',
    'ü': 'u',
    'ñ': 'n',
    'ý': 'y',
    'ÿ': 'y',
  };
  accents.forEach(
    (key, replacement) => result = result.replaceAll(key, replacement),
  );
  return result.replaceAll(RegExp(r'[\u0300-\u036f]'), '');
}
