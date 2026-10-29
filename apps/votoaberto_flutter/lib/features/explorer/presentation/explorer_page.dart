import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import '../../../app/strings.dart';
import '../../../core/formatters.dart';
import '../../../core/widgets.dart';
import '../../elections/domain/election.dart';
import '../../elections/domain/geography.dart';
import '../../map/domain/brazil_geometry.dart';
import '../../map/presentation/brazil_map.dart';
import 'explorer_controller.dart';
import 'result_charts.dart';
import 'state_search.dart';

String explorerLocation(
  BrazilianState? state,
  ElectionRound round,
  ExplorerView view,
) => Uri(
  path: state == null ? '/' : '/uf/${state.code}',
  queryParameters: {
    'turno': round == ElectionRound.first ? '1' : '2',
    'visao': view.name,
  },
).toString();

class ExplorerPage extends StatefulWidget {
  const ExplorerPage({
    super.key,
    required this.controller,
    this.geometryLoader,
  });
  final ExplorerController controller;
  final Future<BrazilGeometry> Function()? geometryLoader;
  @override
  State<ExplorerPage> createState() => _ExplorerPageState();
}

class _ExplorerPageState extends State<ExplorerPage> {
  BrazilGeometry? _geometry;
  bool _geometryError = false;
  @override
  void initState() {
    super.initState();
    _loadMap();
  }

  Future<void> _loadMap() async {
    setState(() => _geometryError = false);
    try {
      final next =
          await (widget.geometryLoader?.call() ??
              rootBundle
                  .loadString('assets/geo/br_states.geojson')
                  .then(BrazilGeometry.decode));
      if (mounted) setState(() => _geometry = next);
    } catch (_) {
      if (mounted) setState(() => _geometryError = true);
    }
  }

  ExplorerController get c => widget.controller;
  void _navigate({
    BrazilianState? state,
    bool reset = false,
    ElectionRound? round,
    ExplorerView? view,
  }) {
    context.go(
      explorerLocation(
        reset ? null : state ?? c.selected,
        round ?? c.round,
        view ?? c.view,
      ),
    );
  }

  void _chooseState() {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Explorar outra UF'),
        content: SizedBox(
          width: 380,
          child: StateSearch(
            onSelect: (state) {
              Navigator.pop(dialogContext);
              _navigate(state: state);
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Fechar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: c,
    builder: (context, _) => PopScope(
      canPop: c.selected == null,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop && c.selected != null) _navigate(reset: true);
      },
      child: Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              _header(context),
              const DemoBanner(),
              Expanded(
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    if (constraints.maxWidth >= 1080) {
                      return Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Expanded(
                            child: Padding(
                              padding: const EdgeInsets.fromLTRB(
                                40,
                                24,
                                32,
                                18,
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  _mapHeading(context),
                                  const SizedBox(height: 16),
                                  Expanded(child: _map(context)),
                                  const SizedBox(height: 12),
                                  _footer(context),
                                ],
                              ),
                            ),
                          ),
                          VerticalDivider(
                            width: 1,
                            color: Theme.of(context).colorScheme.outlineVariant,
                          ),
                          SizedBox(
                            width: 440,
                            child: SingleChildScrollView(
                              key: const ValueKey('panel-scroll'),
                              padding: const EdgeInsets.all(28),
                              child: _panel(context),
                            ),
                          ),
                        ],
                      );
                    }
                    return SingleChildScrollView(
                      key: const ValueKey('mobile-scroll'),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Padding(
                            padding: const EdgeInsets.fromLTRB(20, 22, 20, 0),
                            child: _mapHeading(context),
                          ),
                          SizedBox(
                            height: constraints.maxWidth < 500 ? 370 : 490,
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: _map(context),
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.all(20),
                            child: _panel(context),
                          ),
                          Padding(
                            padding: const EdgeInsets.all(20),
                            child: _footer(context),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );

  Widget _header(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
    child: Row(
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primary,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(
            Icons.how_to_vote_outlined,
            size: 21,
            color: Theme.of(context).colorScheme.onPrimary,
          ),
        ),
        const SizedBox(width: 10),
        const Expanded(
          child: Text(
            AppStrings.title,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              letterSpacing: -.6,
            ),
          ),
        ),
        if (MediaQuery.sizeOf(context).width > 650)
          Text(
            'DADOS ABERTOS · CIDADANIA',
            style: Theme.of(context).textTheme.labelSmall,
          ),
        const SizedBox(width: 10),
        IconButton(
          key: const ValueKey('theme-toggle'),
          tooltip: c.theme == ThemeMode.dark
              ? 'Usar tema claro'
              : 'Usar tema escuro',
          onPressed: c.toggleTheme,
          icon: Icon(
            c.theme == ThemeMode.dark
                ? Icons.light_mode_outlined
                : Icons.dark_mode_outlined,
          ),
        ),
        IconButton(
          tooltip: AppStrings.methodology,
          onPressed: () => showMethodology(context),
          icon: const Icon(Icons.info_outline),
        ),
      ],
    ),
  );

  Widget _mapHeading(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Wrap(
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          TextButton(
            key: const ValueKey('breadcrumb-brasil'),
            onPressed: () => _navigate(reset: true),
            child: const Text('Brasil'),
          ),
          if (c.selected != null) ...[
            const Icon(Icons.chevron_right, size: 16),
            Text(
              c.selected!.code,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(width: 12),
            Text(
              'Municípios · em breve',
              style: Theme.of(context).textTheme.labelSmall,
            ),
          ],
        ],
      ),
      const SizedBox(height: 8),
      Text(
        c.selected?.name ?? 'O Brasil, em perspectiva.',
        key: const ValueKey('map-title'),
        style: Theme.of(context).textTheme.headlineLarge,
      ),
      const SizedBox(height: 8),
      Text(
        c.selected == null
            ? '27 unidades federativas. Um caminho para explorar os dados.'
            : 'Explore os dois turnos e compare resultados demonstrativos.',
        style: Theme.of(context).textTheme.bodyMedium,
      ),
    ],
  );

  Widget _map(BuildContext context) {
    if (_geometryError) {
      return StatusMessage(
        message: 'Não foi possível abrir a malha do IBGE.',
        onRetry: _loadMap,
      );
    }
    if (_geometry == null) {
      return const StatusMessage(
        message: 'Abrindo o mapa local…',
        loading: true,
      );
    }
    return BrazilMap(
      geometry: _geometry!,
      selected: c.selected,
      onSelect: (state) => _navigate(state: state),
      onReset: () => _navigate(reset: true),
    );
  }

  Widget _panel(BuildContext context) {
    if (c.status == LoadStatus.loading) {
      return const StatusMessage(
        message: 'Carregando dados locais…',
        loading: true,
      );
    }
    if (c.status == LoadStatus.error) {
      return StatusMessage(message: AppStrings.loadError, onRetry: c.load);
    }
    final rounds = c.results;
    if (rounds == null || !rounds.containsKey(c.round)) {
      return const StatusMessage(message: AppStrings.empty);
    }
    final national = c.selected == null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          national
              ? 'EXPLORAÇÃO NACIONAL'
              : 'VISÃO ESTADUAL · ${c.selected!.code}',
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.5,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          national ? 'Brasil' : c.selected!.name,
          key: const ValueKey('panel-title'),
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 4),
        const Text('Eleições Presidenciais 2026'),
        const SizedBox(height: 18),
        if (national) ...[
          const Text(
            'Comece por uma UF ou compare os turnos. Todos os números desta versão são fictícios.',
          ),
          const SizedBox(height: 20),
          StateSearch(onSelect: (state) => _navigate(state: state)),
        ] else ...[
          Wrap(
            spacing: 8,
            children: [
              TextButton.icon(
                key: const ValueKey('back-brasil'),
                onPressed: () => _navigate(reset: true),
                icon: const Icon(Icons.west, size: 18),
                label: const Text('Voltar ao Brasil'),
              ),
              TextButton.icon(
                onPressed: _chooseState,
                icon: const Icon(Icons.search, size: 18),
                label: const Text('Outra UF'),
              ),
            ],
          ),
        ],
        const Divider(),
        Wrap(
          spacing: 8,
          runSpacing: 4,
          children: [
            for (final round in ElectionRound.values)
              ChoiceChip(
                key: ValueKey('round-${round.index + 1}'),
                label: Text('${round.index + 1}º turno'),
                selected: c.round == round,
                onSelected: (_) => _navigate(round: round),
              ),
          ],
        ),
        const SizedBox(height: 14),
        Wrap(
          spacing: 4,
          children: [
            for (final entry in const [
              (ExplorerView.summary, 'Resumo'),
              (ExplorerView.comparison, 'Comparar'),
              (ExplorerView.insights, 'Explorar os Dados'),
            ])
              TextButton(
                key: ValueKey('view-${entry.$1.name}'),
                style: TextButton.styleFrom(
                  backgroundColor: c.view == entry.$1
                      ? Theme.of(context).colorScheme.secondaryContainer
                      : null,
                ),
                onPressed: () => _navigate(view: entry.$1),
                child: Text(entry.$2),
              ),
          ],
        ),
        const SizedBox(height: 26),
        if (c.view == ExplorerView.summary) _summary(context, rounds[c.round]!),
        if (c.view == ExplorerView.comparison)
          if (rounds.containsKey(ElectionRound.first) &&
              rounds.containsKey(ElectionRound.second)) ...[
            Text(
              'Entre um turno e outro',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            const Text('DEMONSTRAÇÃO · valores e variações fictícios'),
            const SizedBox(height: 20),
            ComparisonChart(
              first: rounds[ElectionRound.first]!,
              second: rounds[ElectionRound.second]!,
            ),
            const Text(AppStrings.interpretation),
          ] else
            const StatusMessage(message: 'A comparação requer os dois turnos.'),
        if (c.view == ExplorerView.insights) _insights(context),
        const Divider(),
        TextButton.icon(
          onPressed: () => showMethodology(context),
          icon: const Icon(Icons.menu_book_outlined, size: 18),
          label: const Text(AppStrings.methodology),
        ),
        const SizedBox(height: 12),
        const Text(AppStrings.future, style: TextStyle(fontSize: 12)),
        const SizedBox(height: 16),
        Text(
          'Fonte: gerador sintético · mock-v1\n${national || c.view == ExplorerView.insights ? '27 UFs · exterior não incluído' : c.selected!.code} · ${c.round.index + 1}º turno',
          style: Theme.of(context).textTheme.labelSmall,
        ),
      ],
    );
  }

  Widget _summary(BuildContext context, RoundResult result) {
    final t = result.totals;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Participação em números',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 20),
        Text(
          percent(t.turnoutRate),
          key: const ValueKey('turnout-rate'),
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.w700,
          ),
        ),
        Text('de comparecimento · ${count(t.turnout)} eleitores'),
        const SizedBox(height: 22),
        _metric(context, 'Eleitores aptos', count(t.eligible)),
        _metric(
          context,
          'Abstenção',
          '${count(t.abstention)} · ${percent(t.abstentionRate)}',
        ),
        _metric(context, 'Votos válidos', count(t.valid)),
        _metric(context, 'Votos brancos', count(t.blank)),
        _metric(context, 'Votos nulos', count(t.invalid)),
        const Divider(),
        Text(
          'Distribuição dos votos válidos',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 4),
        const Text(
          'Candidatos fictícios · % dos votos válidos',
          style: TextStyle(fontSize: 12),
        ),
        const SizedBox(height: 20),
        DistributionChart(result: result),
      ],
    );
  }

  Widget _metric(BuildContext context, String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: Wrap(
      alignment: WrapAlignment.spaceBetween,
      spacing: 16,
      runSpacing: 4,
      children: [
        Text(label),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
      ],
    ),
  );

  Widget _insights(BuildContext context) {
    final ranking = [...c.dataset!.states]
      ..sort((a, b) {
        final rate = b.rounds[c.round]!.totals.turnoutRate.compareTo(
          a.rounds[c.round]!.totals.turnoutRate,
        );
        return rate == 0 ? a.state.code.compareTo(b.state.code) : rate;
      });
    if (ranking.isEmpty) return const StatusMessage(message: AppStrings.empty);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Explorar os Dados',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 10),
        Text(
          'Maiores taxas de comparecimento fictício · ${c.round.index + 1}º turno',
        ),
        const SizedBox(height: 16),
        for (var i = 0; i < ranking.length; i++)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Text(
              '${i + 1}'.padLeft(2, '0'),
              style: Theme.of(context).textTheme.labelLarge,
            ),
            title: Text(ranking[i].state.name),
            subtitle: Text(ranking[i].state.code),
            trailing: Text(
              percent(ranking[i].rounds[c.round]!.totals.turnoutRate),
            ),
            onTap: () =>
                _navigate(state: ranking[i].state, view: ExplorerView.summary),
          ),
        const SizedBox(height: 16),
        const Text(
          'Como ler: comparecimento ÷ eleitores aptos. Ordenação decrescente; '
          'empates por sigla. Este ranking usa somente o mock-v1 das 27 UFs, sem exterior. '
          'Não descreve a eleição real nem explica comportamentos individuais.',
        ),
      ],
    );
  }

  Widget _footer(BuildContext context) => Text(
    'VotoAberto 0.1.0 · ${AppStrings.independence}',
    style: Theme.of(context).textTheme.labelSmall,
  );
}
