import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:go_router/go_router.dart';
import '../core/widgets.dart';
import '../features/elections/domain/election.dart';
import '../features/elections/domain/election_repository.dart';
import '../features/elections/domain/geography.dart';
import '../features/explorer/presentation/explorer_controller.dart';
import '../features/explorer/presentation/explorer_page.dart';
import '../features/map/domain/brazil_geometry.dart';
import 'strings.dart';
import 'theme.dart';

class VotoAbertoApp extends StatefulWidget {
  const VotoAbertoApp({
    super.key,
    required this.repository,
    this.initialLocation,
    this.geometryLoader,
    this.election = Election.demonstration,
  });
  final ElectionRepository repository;
  final String? initialLocation;
  final Future<BrazilGeometry> Function()? geometryLoader;
  final Election election;
  @override
  State<VotoAbertoApp> createState() => _VotoAbertoAppState();
}

class _VotoAbertoAppState extends State<VotoAbertoApp> {
  late final controller = ExplorerController(
    widget.repository,
    election: widget.election,
  )..load();
  late final router = GoRouter(
    initialLocation: widget.initialLocation,
    redirect: (context, state) {
      final path = state.uri.path;
      final uf = state.pathParameters['uf']?.toUpperCase();
      final requestedRound = state.uri.queryParameters['turno'];
      final requestedView = state.uri.queryParameters['visao'];
      if ((requestedRound != null && !['1', '2'].contains(requestedRound)) ||
          (requestedView != null &&
              !ExplorerView.values.any((v) => v.name == requestedView))) {
        return '/indisponivel';
      }
      if (uf != null &&
          BrazilianState.fromCode(uf) == null &&
          !(uf == 'ZZ' && widget.election.id != Election.demonstration.id)) {
        return '/indisponivel';
      }
      if (path == '/' || path.startsWith('/uf/')) {
        final round = state.uri.queryParameters['turno'] == '2'
            ? ElectionRound.second
            : ElectionRound.first;
        final viewName = state.uri.queryParameters['visao'];
        final view =
            ExplorerView.values.where((v) => v.name == viewName).firstOrNull ??
            ExplorerView.summary;
        // The router rebuilds the Page itself; notifying during its initial
        // parse would mark an ancestor dirty while MaterialApp is building.
        controller.navigate(
          BrazilianState.fromCode(uf),
          round,
          view,
          notify: false,
          overseas: uf == 'ZZ',
          municipality: state.pathParameters['municipality'],
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
    ),
  );

  Widget _unavailable(BuildContext context) => Scaffold(
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
