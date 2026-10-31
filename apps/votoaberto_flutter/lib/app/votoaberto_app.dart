import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';
import '../core/widgets.dart';
import '../core/institutional_link.dart';
import '../features/elections/domain/election.dart';
import '../features/elections/domain/election_repository.dart';
import '../features/elections/domain/geography.dart';
import '../features/explorer/presentation/explorer_controller.dart';
import '../features/explorer/presentation/explorer_page.dart';
import '../features/map/domain/brazil_geometry.dart';
import '../features/map/domain/geographic_catalog.dart';
import '../features/map/domain/world_geometry.dart';
import 'strings.dart';
import 'theme.dart';

class VotoAbertoApp extends StatefulWidget {
  const VotoAbertoApp({
    super.key,
    required this.repository,
    this.initialLocation,
    this.geometryLoader,
    this.geographicLoader,
    this.worldLoader,
    this.election = Election.demonstration,
  });
  final ElectionRepository repository;
  final String? initialLocation;
  final Future<BrazilGeometry> Function()? geometryLoader;
  final Future<GeographicCatalog> Function()? geographicLoader;
  final Future<WorldGeometry> Function()? worldLoader;
  final Election election;
  @override
  State<VotoAbertoApp> createState() => _VotoAbertoAppState();
}

class _VotoAbertoAppState extends State<VotoAbertoApp> {
  late final geographicAssets = GeographicAssets();
  late final controller =
      ExplorerController(widget.repository, election: widget.election)
        ..loadGeography(widget.geographicLoader ?? geographicAssets.load)
        ..load();
  late final router = GoRouter(
    initialLocation: widget.initialLocation,
    redirect: (context, state) {
      final path = state.uri.path;
      final uf = state.pathParameters['uf']?.toUpperCase();
      if (path == '/indisponivel') return null;
      final mode = ResultMode.fromQuery(state.uri.queryParameters);
      if (mode == null) return '/indisponivel';
      final query = {...state.uri.queryParameters}
        ..remove('turno')
        ..remove('visao')
        ..['modo'] = mode.queryValue;
      if (state.uri.query != Uri(queryParameters: query).query) {
        return state.uri.replace(queryParameters: query).toString();
      }
      if (uf != null &&
          BrazilianState.fromCode(uf) == null &&
          !(uf == 'ZZ' && widget.election.id != Election.demonstration.id)) {
        return '/indisponivel';
      }
      if (uf == 'ZZ') {
        final locality = state.pathParameters['municipality'];
        return state.uri
            .replace(
              path: locality == null ? '/mundo' : '/mundo/localidade/$locality',
            )
            .toString();
      }
      final country = state.pathParameters['country']?.toUpperCase();
      final municipality = state.pathParameters['municipality'];
      if ((country != null && !RegExp(r'^[A-Z]{2}$').hasMatch(country)) ||
          (municipality != null &&
              !RegExp(r'^\d{1,8}$').hasMatch(municipality))) {
        return '/indisponivel';
      }
      if (path == '/' || path.startsWith('/uf/') || path.startsWith('/mundo')) {
        // The router rebuilds the Page itself; notifying during its initial
        // parse would mark an ancestor dirty while MaterialApp is building.
        controller.navigate(
          BrazilianState.fromCode(uf),
          mode,
          notify: false,
          overseas: path.startsWith('/mundo'),
          country: country,
          municipality: municipality,
        );
      }
      return null;
    },
    routes: [
      GoRoute(path: '/', pageBuilder: (context, state) => _explorer()),
      GoRoute(path: '/uf/:uf', pageBuilder: (context, state) => _explorer()),
      GoRoute(
        path: '/uf/:uf/municipio/:municipality',
        pageBuilder: (context, state) => _explorer(),
      ),
      GoRoute(path: '/mundo', pageBuilder: (context, state) => _explorer()),
      GoRoute(
        path: '/mundo/localidade/:municipality',
        pageBuilder: (context, state) => _explorer(),
      ),
      GoRoute(
        path: '/mundo/:country',
        pageBuilder: (context, state) => _explorer(),
      ),
      GoRoute(
        path: '/mundo/:country/localidade/:municipality',
        pageBuilder: (context, state) => _explorer(),
      ),
      GoRoute(
        path: '/indisponivel',
        builder: (context, state) => _unavailable(context),
      ),
    ],
    errorBuilder: (context, state) => _unavailable(context),
  );

  // A stable Page identity retains the map camera across country/UF routes.
  NoTransitionPage<void> _explorer() => NoTransitionPage<void>(
    key: const ValueKey('explorer-route'),
    child: ExplorerPage(
      key: const ValueKey('explorer'),
      controller: controller,
      geometryLoader: widget.geometryLoader,
      worldLoader:
          widget.worldLoader ??
          () async => WorldGeometry.decode(
            await geographicAssets.read('world.geojson'),
          ),
    ),
  );

  Widget _unavailable(BuildContext context) => Scaffold(
    bottomNavigationBar: kIsWeb ? const InstitutionalLink() : null,
    body: SafeArea(
      child: Column(
        children: [
          if (widget.election.id == Election.demonstration.id)
            const DemoBanner(),
          Expanded(
            child: StatusMessage(
              message: widget.election.id == Election.demonstration.id
                  ? 'Este endereço não está disponível no M1.'
                  : 'Este endereço não está disponível.',
              onRetry: () => context.go('/'),
            ),
          ),
        ],
      ),
    ),
  );

  @override
  void dispose() {
    router.dispose();
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: controller,
    builder: (context, _) => MaterialApp.router(
      title: AppStrings.title,
      debugShowCheckedModeBanner: false,
      locale: const Locale('pt', 'BR'),
      supportedLocales: const [Locale('pt', 'BR')],
      localizationsDelegates: GlobalMaterialLocalizations.delegates,
      theme: AppTheme.build(Brightness.light),
      darkTheme: AppTheme.build(Brightness.dark),
      themeMode: controller.theme,
      routerConfig: router,
    ),
  );
}
