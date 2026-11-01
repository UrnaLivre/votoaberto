import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../../../app/strings.dart';
import '../../../core/formatters.dart';
import '../../../core/institutional_link.dart';
import '../../../core/widgets.dart';
import '../../updates/release_host.dart';
import '../../elections/domain/election.dart';
import '../../elections/domain/geography.dart';
import '../../map/domain/brazil_geometry.dart';
import '../../map/domain/world_geometry.dart';
import '../../map/domain/geographic_catalog.dart';
import '../../map/presentation/brazil_map.dart';
import '../../map/presentation/world_map.dart';
import 'explorer_controller.dart';
import 'municipality_search.dart';
import 'result_charts.dart';
import 'round_summary.dart';
import 'overseas_special_cases_dialog.dart';
import 'state_search.dart';

String explorerLocation(
  BrazilianState? state,
  ResultMode mode, {
  bool abroad = false,
  String? municipality,
  String? country,
}) => Uri(
  path: abroad
      ? '/mundo${country == null ? '' : '/$country'}${municipality == null ? '' : '/localidade/$municipality'}'
      : state == null
      ? '/'
      : '/uf/${state.code}${municipality == null ? '' : '/municipio/$municipality'}',
  queryParameters: {'modo': mode.queryValue},
).toString();

class ExplorerPage extends StatefulWidget {
  const ExplorerPage({
    super.key,
    required this.controller,
    this.geometryLoader,
    this.worldLoader,
  });
  final ExplorerController controller;
  final Future<BrazilGeometry> Function()? geometryLoader;
  final Future<WorldGeometry> Function()? worldLoader;
  @override
  State<ExplorerPage> createState() => _ExplorerPageState();
}

class _ExplorerPageState extends State<ExplorerPage> {
  final _specialCasesFocus = FocusNode(debugLabel: 'Casos especiais');

  Future<void> _showSpecialCases() async {
    final cases = c.specialCases;
    if (cases.isEmpty) return;
    await showDialog<void>(
      context: context,
      traversalEdgeBehavior: TraversalEdgeBehavior.closedLoop,
      animationStyle: MediaQuery.disableAnimationsOf(context)
          ? AnimationStyle.noAnimation
          : null,
      builder: (_) => OverseasSpecialCasesDialog(controller: c, cases: cases),
    );
    if (mounted &&
        _specialCasesFocus.context != null &&
        _specialCasesFocus.canRequestFocus) {
      _specialCasesFocus.requestFocus();
    }
  }

  BrazilGeometry? _geometry;
  bool _geometryError = false;
  WorldGeometry? _world;
  bool _worldError = false;
  bool _worldLoading = false;
  void _geographicChange() {
    if (c.abroad && _world == null && !_worldError && !_worldLoading) {
      _loadWorld();
    }
  }

  Future<void> _loadWorld() async {
    _worldLoading = true;
    _worldError = false;
    try {
      final world =
          await (widget.worldLoader?.call() ??
              GeographicAssets()
                  .read('world.geojson')
                  .then(WorldGeometry.decode));
      if (mounted) setState(() => _world = world);
    } catch (_) {
      if (mounted) setState(() => _worldError = true);
    }
    _worldLoading = false;
  }

  @override
  void dispose() {
    c.removeListener(_geographicChange);
    _specialCasesFocus.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _loadMap();
    c.addListener(_geographicChange);
    _geographicChange();
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
    ResultMode? mode,
    String? municipality,
    bool clearMunicipality = false,
    bool abroad = false,
    String? country,
    bool worldReset = false,
  }) {
    final world = !reset && state == null && (abroad || c.abroad);
    context.go(
      explorerLocation(
        reset || world ? null : state ?? c.selected,
        mode ?? c.mode,
        abroad: world,
        country: world
            ? (worldReset || abroad ? null : country ?? c.countryCode)
            : null,
        municipality:
            reset ||
                clearMunicipality ||
                state != null ||
                abroad ||
                worldReset ||
                country != null
            ? null
            : municipality ?? c.municipalityCode,
      ),
    );
  }

  void _back() {
    if (c.municipalityCode != null) {
      _navigate(clearMunicipality: true, country: c.mapCountryCode);
    } else if (c.countryCode != null) {
      _navigate(worldReset: true);
    } else {
      _navigate(reset: true);
    }
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
      canPop:
          c.selected == null &&
          c.countryCode == null &&
          c.municipalityCode == null,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) _back();
      },
      child: Scaffold(
        bottomNavigationBar: kIsWeb ? const InstitutionalLink() : null,
        body: SafeArea(
          child: Column(
            children: [
              _header(context),
              if (c.dataset == null &&
                  c.election.id != Election.demonstration.id)
                const Padding(
                  padding: EdgeInsets.all(8),
                  child: Text(
                    'Conjunto local selecionado · aguardando leitura',
                  ),
                )
              else
                SourceBanner(synthetic: c.synthetic),
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
    child: Column(
      children: [
        Row(
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
            const ReleaseAboutButton(),
            IconButton(
              tooltip: AppStrings.methodology,
              onPressed: c.dataset == null
                  ? null
                  : () => showMethodology(
                      context,
                      provenance: c.dataset?.provenance,
                    ),
              icon: const Icon(Icons.info_outline),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: SegmentedButton<bool>(
            segments: const [
              ButtonSegment(
                value: false,
                label: Text('Brasil'),
                icon: Icon(Icons.flag_outlined),
              ),
              ButtonSegment(
                value: true,
                label: Text('Mundo'),
                icon: Icon(Icons.public),
              ),
            ],
            selected: {c.abroad},
            onSelectionChanged: (value) =>
                value.first ? _navigate(abroad: true) : _navigate(reset: true),
          ),
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
            key: ValueKey(c.abroad ? 'breadcrumb-mundo' : 'breadcrumb-brasil'),
            onPressed: () =>
                c.abroad ? _navigate(worldReset: true) : _navigate(reset: true),
            child: Text(c.abroad ? 'Mundo' : 'Brasil'),
          ),
          if (c.abroad) ...[
            if (c.mapCountryCode != null) ...[
              const Icon(Icons.chevron_right, size: 16),
              TextButton(
                onPressed: () => _navigate(
                  country: c.mapCountryCode,
                  clearMunicipality: true,
                ),
                key: const ValueKey('breadcrumb-country'),
                child: Text(
                  c.countries
                          .where((v) => v.iso == c.mapCountryCode)
                          .firstOrNull
                          ?.name ??
                      c.mapCountryCode!,
                ),
              ),
            ],
          ] else if (c.selected != null) ...[
            const Icon(Icons.chevron_right, size: 16),
            TextButton(
              onPressed: () => _navigate(clearMunicipality: true),
              key: const ValueKey('breadcrumb-uf'),
              child: Text(c.selected!.code),
            ),
          ],
          if (c.municipality != null) ...[
            const Icon(Icons.chevron_right, size: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Text(
                c.municipality!.municipality.name,
                key: const ValueKey('breadcrumb-locality'),
              ),
            ),
          ],
        ],
      ),
      const SizedBox(height: 8),
      Text(
        c.municipality?.municipality.name ??
            (c.abroad
                ? c.country?.name ??
                      (c.countryCode != null ? 'País indisponível' : 'Mundo')
                : c.selected?.name ?? 'O Brasil, em perspectiva.'),
        key: const ValueKey('map-title'),
        style: Theme.of(context).textTheme.headlineLarge,
      ),
      const SizedBox(height: 8),
      Text(
        c.abroad
            ? 'Votação brasileira no exterior. Selecione um país com dados ou uma localidade eleitoral.'
            : c.synthetic
            ? 'Explore os dois turnos e compare resultados demonstrativos.'
            : 'Resultados presidenciais por UF e município. Selecione no mapa ou use a busca.',
        style: Theme.of(context).textTheme.bodyMedium,
      ),
      if (!c.abroad &&
          c.municipalityCode != null &&
          c.municipalStatus == LoadStatus.ready)
        Text(
          c.geography?.municipal(c.territoryCode, c.municipalityCode) == null
              ? 'Localização não confirmada neste mapa. A consulta eleitoral foi preservada.'
              : 'Marcador: sede municipal ou ponto representativo. Não indica urna ou local de votação.',
          style: Theme.of(context).textTheme.labelSmall,
        ),
    ],
  );

  Widget _map(BuildContext context) {
    if (c.abroad) {
      _geographicChange();
      if (_worldError) {
        return StatusMessage(
          message: 'Não foi possível abrir o mapa mundial local.',
          onRetry: _loadWorld,
        );
      }
      if (_world == null) {
        return const StatusMessage(
          message: 'Abrindo mapa mundial local…',
          loading: true,
        );
      }
      return WorldMap(
        geometry: _world!,
        active: c.activeCountries,
        selected: c.mapCountryCode,
        onSelect: (iso) => _navigate(country: iso),
        onReset: () => _navigate(worldReset: true),
      );
    }

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
      location: c.municipality == null
          ? null
          : c.geography?.municipal(c.territoryCode, c.municipalityCode),
      locationName: c.municipality?.municipality.name,
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
    final national = !c.abroad && c.selected == null;
    final municipal = c.municipalityCode != null;
    final title = municipal
        ? c.municipality?.municipality.name ??
              (c.abroad ? 'Localidade indisponível' : 'Município indisponível')
        : c.abroad
        ? c.country?.name ??
              (c.countryCode == null ? 'Mundo' : 'País indisponível')
        : national
        ? 'Brasil'
        : c.selected!.name;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          national
              ? 'EXPLORAÇÃO NACIONAL'
              : municipal
              ? c.abroad
                    ? 'LOCALIDADE ELEITORAL'
                    : 'VISÃO MUNICIPAL · ${c.territoryCode}'
              : c.abroad
              ? c.countryCode == null
                    ? 'VOTAÇÃO NO EXTERIOR'
                    : 'PAÍS · VOTAÇÃO BRASILEIRA'
              : 'VISÃO ESTADUAL · ${c.selected!.code}',
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: Theme.of(context).colorScheme.primary,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.5,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          title,
          key: const ValueKey('panel-title'),
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 4),
        const Text('Eleições Presidenciais 2026'),
        const SizedBox(height: 18),
        SegmentedButton<ResultMode>(
          key: const ValueKey('result-mode'),
          showSelectedIcon: false,
          style: SegmentedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 14),
            textStyle: Theme.of(context).textTheme.labelMedium,
          ),
          segments: [
            for (final mode in ResultMode.values)
              ButtonSegment(
                value: mode,
                label: Text(mode.label, key: ValueKey('mode-${mode.name}')),
              ),
          ],
          selected: {c.mode},
          onSelectionChanged: (value) => _navigate(mode: value.single),
        ),
        const SizedBox(height: 18),
        if (national) ...[
          Text(
            c.synthetic
                ? 'Comece por uma UF ou compare os turnos. Todos os números desta versão são fictícios.'
                : 'Brasil inclui os votos no exterior. Selecione uma UF para consultar seus municípios.',
          ),
          if (c.dataset?.overseas != null)
            TextButton.icon(
              key: const ValueKey('select-ZZ'),
              onPressed: () => _navigate(abroad: true),
              icon: const Icon(Icons.public),
              label: const Text('Consultar votação no exterior'),
            ),
          const SizedBox(height: 20),
          StateSearch(onSelect: (state) => _navigate(state: state)),
        ] else if (!c.abroad) ...[
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
        if (c.abroad) _worldNavigation(context),
        if (!national && !c.abroad && c.municipalSupported) ...[
          const SizedBox(height: 12),
          if (c.municipalStatus == LoadStatus.loading)
            const StatusMessage(message: 'Abrindo localidades…', loading: true)
          else if (c.municipalStatus == LoadStatus.error)
            StatusMessage(
              message:
                  'Não foi possível carregar as localidades desta abrangência.',
              onRetry: c.loadMunicipalities,
            )
          else
            MunicipalitySearch(
              key: ValueKey('cities-${c.territoryCode}-${c.municipalityCode}'),
              municipalities: c.municipalities,
              abroad: c.abroad,
              onSelect: (code) => _navigate(municipality: code),
            ),
          if (municipal)
            TextButton.icon(
              key: const ValueKey('back-uf'),
              onPressed: () => _navigate(clearMunicipality: true),
              icon: const Icon(Icons.west),
              label: Text('Voltar para ${c.territoryCode}'),
            ),
        ],
        const Divider(),
        const SizedBox(height: 26),
        if (rounds == null ||
            (c.mode.round != null && !rounds.containsKey(c.mode.round)))
          StatusMessage(
            message: municipal && c.municipalStatus == LoadStatus.loading
                ? 'Abrindo município…'
                : municipal
                ? c.abroad
                      ? 'Localidade eleitoral ou turno não disponível neste conjunto.'
                      : 'Município ou turno não disponível neste conjunto.'
                : AppStrings.empty,
          )
        else if (c.mode.round != null)
          _summary(context, rounds[c.mode.round]!)
        else if (rounds.containsKey(ElectionRound.first) &&
            rounds.containsKey(ElectionRound.second)) ...[
          Text(
            'Entre um turno e outro',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          Text(
            c.synthetic
                ? 'DEMONSTRAÇÃO · valores e variações fictícios'
                : 'Contagens publicadas · aptos e candidaturas podem mudar',
          ),
          const SizedBox(height: 20),
          ComparisonChart(
            first: rounds[ElectionRound.first]!,
            second: rounds[ElectionRound.second]!,
            synthetic: c.synthetic,
            percentages: _percentages,
          ),
          const Text(AppStrings.interpretation),
        ] else
          const StatusMessage(message: 'A comparação requer os dois turnos.'),
        const Divider(),
        TextButton.icon(
          onPressed: () =>
              showMethodology(context, provenance: c.dataset?.provenance),
          icon: const Icon(Icons.menu_book_outlined, size: 18),
          label: const Text(AppStrings.methodology),
        ),
        const SizedBox(height: 12),
        const Text(AppStrings.future, style: TextStyle(fontSize: 12)),
        const SizedBox(height: 16),
        Text(
          c.synthetic
              ? 'Fonte: gerador sintético · ${c.dataset!.provenance.version}\n${national
                    ? (c.dataset!.overseas == null ? '27 UFs · exterior não incluído' : '27 UFs + exterior fictício')
                    : c.abroad
                    ? 'Votação no exterior'
                    : c.territoryCode} · ${c.mode.label}'
              : 'Fonte: dados abertos do TSE · processamento independente pelo VotoAberto\nPrévia local · ${c.mode.label}',
          style: Theme.of(context).textTheme.labelSmall,
        ),
      ],
    );
  }

  bool get _percentages =>
      !(c.abroad &&
          c.countryCode != null &&
          c.municipalityCode == null &&
          c.unmappedLocalities.isNotEmpty);

  Widget _summary(BuildContext context, RoundResult result) => RoundSummary(
    result: result,
    synthetic: c.synthetic,
    percentages: _percentages,
    afterCounted:
        !c.abroad &&
            c.territoryCode == null &&
            c.dataset?.domestic?.rounds[c.mode.round] != null
        ? ExpansionTile(
            tilePadding: EdgeInsets.zero,
            title: const Text('Brasil doméstico · 27 UFs'),
            children: [
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  '${count(c.dataset!.domestic!.rounds[c.mode.round]!.totals.counted)} votos contabilizados',
                ),
                subtitle: const Text(
                  'Recorte sem votação no exterior. O resultado Brasil acima inclui o exterior.',
                ),
              ),
            ],
          )
        : null,
  );

  Widget _worldNavigation(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      if (c.municipalityCode != null &&
          c.mapCountryCode == null &&
          c.municipalStatus == LoadStatus.ready)
        const Text(
          'País desta localidade eleitoral ainda não confirmado. Os resultados continuam disponíveis.',
        ),
      Wrap(
        spacing: 8,
        children: [
          TextButton.icon(
            key: const ValueKey('geographic-back'),
            onPressed: _back,
            icon: Icon(
              c.countryCode == null && c.municipalityCode == null
                  ? Icons.flag_outlined
                  : Icons.west,
            ),
            label: Text(
              c.municipalityCode != null
                  ? c.mapCountryCode == null
                        ? 'Voltar ao Mundo'
                        : 'Voltar ao país'
                  : c.countryCode != null
                  ? 'Voltar ao Mundo'
                  : 'Consultar votação no Brasil',
            ),
          ),
          if (c.countryCode != null || c.municipalityCode != null)
            TextButton(
              onPressed: () => _navigate(worldReset: true),
              child: const Text('Todos os países'),
            ),
        ],
      ),
      if (c.countryCode == null &&
          c.municipalityCode == null &&
          c.specialCases.isNotEmpty)
        OutlinedButton.icon(
          key: const ValueKey('special-cases-open'),
          focusNode: _specialCasesFocus,
          onPressed: _showSpecialCases,
          icon: const Icon(Icons.info_outline, size: 18),
          label: Text('Casos especiais (${c.specialCases.length})'),
        ),
      if (c.municipalStatus == LoadStatus.loading)
        const StatusMessage(
          message: 'Abrindo localidades eleitorais…',
          loading: true,
        )
      else if (c.municipalStatus == LoadStatus.error)
        StatusMessage(
          message: 'Não foi possível abrir as localidades eleitorais.',
          onRetry: c.loadMunicipalities,
        )
      else ...[
        if (c.geographyError)
          const Text(
            'Correspondência geográfica indisponível. Consulte as localidades eleitorais abaixo.',
          ),
        if (c.countryCode == null) ...[
          Text(
            '${c.activeCountries.length} países ou territórios com votação ${c.mode == ResultMode.comparison ? 'em pelo menos um dos turnos' : 'neste turno'}.',
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            key: ValueKey('country-selector-${c.mode.name}'),
            initialValue: null,
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'País com votação no recorte',
            ),
            items: [
              for (final country in c.countries.where(
                (country) => c.activeCountries.contains(country.iso),
              ))
                DropdownMenuItem(
                  value: country.iso,
                  child: Text(country.name, overflow: TextOverflow.ellipsis),
                ),
            ],
            onChanged: (iso) {
              if (iso != null) _navigate(country: iso);
            },
          ),
          const SizedBox(height: 12),
        ] else if (c.country != null) ...[
          Text(
            '${c.country!.localities.length} localidades eleitorais associadas ao país.',
          ),
          if (c.unmappedLocalities.isNotEmpty)
            const Text(
              'Agregação parcial: há localidades do exterior sem país confirmado. Este país reúne somente as associações verificadas.',
            ),
          if (!c.activeCountries.contains(c.countryCode))
            const Text(
              'Sem votação registrada para este país no turno selecionado.',
            ),
        ],
        if (c.visibleMunicipalities.isNotEmpty)
          MunicipalitySearch(
            key: ValueKey(
              'world-localities-${c.countryCode}-${c.municipalityCode}',
            ),
            municipalities: c.visibleMunicipalities,
            abroad: true,
            onSelect: (code) => context.go(
              explorerLocation(
                null,
                c.mode,
                abroad: true,
                country: c.countries
                    .where(
                      (country) => country.localities.any(
                        (loc) => loc.municipality.code == code,
                      ),
                    )
                    .firstOrNull
                    ?.iso,
                municipality: code,
              ),
            ),
          ),
        if (c.countryCode == null && c.otherUnmappedLocalities.isNotEmpty)
          ExpansionTile(
            title: Text(
              'Outras localidades sem país confirmado (${c.otherUnmappedLocalities.length})',
            ),
            children: [
              for (final loc in c.otherUnmappedLocalities)
                ListTile(
                  title: Text(loc.municipality.name),
                  subtitle: Text(
                    'Localidade eleitoral · código TSE ${loc.municipality.code}',
                  ),
                  onTap: () => context.go(
                    explorerLocation(
                      null,
                      c.mode,
                      abroad: true,
                      municipality: loc.municipality.code,
                    ),
                  ),
                ),
            ],
          ),
      ],
      const SizedBox(height: 12),
      const Text(
        'Cores indicam presença de dados no recorte selecionado. Cinza: sem registros associados. Fronteiras cartográficas não representam reconhecimento oficial de disputas territoriais.',
        style: TextStyle(fontSize: 12),
      ),
    ],
  );

  Widget _footer(BuildContext context) => Text(
    'VotoAberto 0.5.0 · ${AppStrings.independence}',
    style: Theme.of(context).textTheme.labelSmall,
  );
}
