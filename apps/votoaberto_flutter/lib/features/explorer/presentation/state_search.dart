import 'package:flutter/material.dart';
import '../../../app/strings.dart';
import '../../../core/formatters.dart';
import '../../elections/domain/geography.dart';

class StateSearch extends StatefulWidget {
  const StateSearch({super.key, required this.onSelect});
  final ValueChanged<BrazilianState> onSelect;
  @override
  State<StateSearch> createState() => _StateSearchState();
}

class _StateSearchState extends State<StateSearch> {
  String _query = '';
  List<BrazilianState> _matches(String value) {
    final query = normalizeSearch(value);
    return BrazilianState.values
        .where((s) => normalizeSearch('${s.name} ${s.code}').contains(query))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final query = normalizeSearch(_query);
    final states = _matches(_query);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          key: const ValueKey('state-search'),
          decoration: const InputDecoration(
            labelText: AppStrings.search,
            prefixIcon: Icon(Icons.search),
          ),
          onChanged: (value) => setState(() => _query = value),
          textInputAction: TextInputAction.search,
          onSubmitted: (value) {
            final current = _matches(value);
            if (current.isNotEmpty) {
              FocusScope.of(context).unfocus();
              widget.onSelect(current.first);
            }
          },
        ),
        const SizedBox(height: 8),
        if (states.isEmpty)
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text(AppStrings.noState),
          )
        else
          SizedBox(
            height: query.isEmpty ? 176 : 224,
            child: Scrollbar(
              child: ListView.builder(
                primary: false,
                itemCount: states.length,
                itemBuilder: (context, i) {
                  final state = states[i];
                  return ListTile(
                    key: ValueKey('select-${state.code}'),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12),
                    leading: Text(
                      state.code,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.primary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    title: Text(state.name),
                    trailing: const Icon(Icons.arrow_outward, size: 18),
                    onTap: () {
                      FocusScope.of(context).unfocus();
                      widget.onSelect(state);
                    },
                  );
                },
              ),
            ),
          ),
      ],
    );
  }
}
