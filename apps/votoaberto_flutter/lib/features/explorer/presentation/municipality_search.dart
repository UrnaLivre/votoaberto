import 'package:flutter/material.dart';
import '../../../core/formatters.dart';
import '../../elections/domain/election.dart';

class MunicipalitySearch extends StatefulWidget {
  const MunicipalitySearch({
    super.key,
    required this.municipalities,
    required this.onSelect,
    this.abroad = false,
  });
  final List<MunicipalitySummary> municipalities;
  final ValueChanged<String> onSelect;
  final bool abroad;
  @override
  State<MunicipalitySearch> createState() => _MunicipalitySearchState();
}

class _MunicipalitySearchState extends State<MunicipalitySearch> {
  String _query = '';
  bool _showAll = false;
  List<MunicipalitySummary> matches(String value) {
    final query = normalizeSearch(value);
    return widget.municipalities
        .where(
          (s) => normalizeSearch(
            '${s.municipality.name} ${s.municipality.code}',
          ).contains(query),
        )
        .toList();
  }

  void select(String code) {
    FocusScope.of(context).unfocus();
    widget.onSelect(code);
  }

  @override
  Widget build(BuildContext context) {
    final cities = matches(_query);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          key: const ValueKey('municipality-search'),
          decoration: InputDecoration(
            labelText: widget.abroad
                ? 'Buscar localidade no exterior'
                : 'Buscar município',
            prefixIcon: const Icon(Icons.search),
          ),
          onChanged: (value) => setState(() => _query = value),
          textInputAction: TextInputAction.search,
          onSubmitted: (value) {
            final next = matches(value);
            if (next.isNotEmpty) select(next.first.municipality.code);
          },
        ),
        const SizedBox(height: 8),
        if (cities.isEmpty)
          const Padding(
            padding: EdgeInsets.all(12),
            child: Text('Nenhuma localidade encontrada.'),
          )
        else if (_query.isEmpty && !_showAll)
          TextButton.icon(
            key: const ValueKey('show-municipalities'),
            onPressed: () => setState(() => _showAll = true),
            icon: const Icon(Icons.list, size: 18),
            label: Text(
              'Ver ${widget.municipalities.length} ${widget.abroad ? 'localidades' : 'municípios'}',
            ),
          )
        else
          SizedBox(
            height: (cities.length * 76.0).clamp(76.0, 184.0).toDouble(),
            child: Scrollbar(
              child: ListView.builder(
                primary: false,
                itemCount: cities.length,
                itemBuilder: (context, index) {
                  final city = cities[index].municipality;
                  return ListTile(
                    key: ValueKey('municipality-${city.code}'),
                    title: Text(city.name),
                    subtitle: Text(
                      '${city.territoryCode} · código TSE ${city.code}',
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => select(city.code),
                  );
                },
              ),
            ),
          ),
      ],
    );
  }
}
