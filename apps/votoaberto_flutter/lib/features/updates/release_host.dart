import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'app_version_info.dart';
import 'platform_updates.dart';
import 'update_service.dart';

class ReleaseInfo extends InheritedWidget {
  const ReleaseInfo({super.key, required this.version, required super.child});
  final Future<AppVersionInfo?> Function() version;
  @override
  bool updateShouldNotify(ReleaseInfo oldWidget) =>
      version != oldWidget.version;
}

/// Lives above the router, so navigation never schedules a new notice/check.
class ReleaseHost extends StatefulWidget {
  const ReleaseHost({
    super.key,
    required this.child,
    this.versionLoader = installedAppVersion,
    this.serviceFactory = platformUpdateService,
  });
  final Widget child;
  final Future<AppVersionInfo?> Function() versionLoader;
  final UpdateService Function(AppVersionInfo) serviceFactory;
  @override
  State<ReleaseHost> createState() => _ReleaseHostState();
}

class _ReleaseHostState extends State<ReleaseHost> {
  late final version = widget.versionLoader();
  UpdateService? service;
  UpdateCheck? notice;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    if ((kReleaseMode && !kIsWeb) ||
        widget.serviceFactory != platformUpdateService) {
      unawaited(_check());
    }
  }

  Future<void> _check() async {
    final installed = await version;
    if (!mounted || installed == null) return;
    final updates = service = widget.serviceFactory(installed);
    final result = await updates.checkOnce();
    if (await updates.claimNotice(result) && mounted) {
      setState(() => notice = result);
    }
  }

  Future<void> _start() async {
    setState(() => busy = true);
    final result = await service!.start();
    if (!mounted) return;
    setState(() {
      busy = false;
      notice = result.availability == UpdateAvailability.readyToInstall
          ? result
          : null;
    });
  }

  @override
  Widget build(BuildContext context) => ReleaseInfo(
    version: () => version,
    child: Column(
      children: [
        Expanded(child: widget.child),
        if (notice != null)
          Material(
            color: Theme.of(context).colorScheme.surfaceContainer,
            child: SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 4,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        notice!.availability ==
                                UpdateAvailability.readyToInstall
                            ? 'Tudo pronto para atualizar o Voto Aberto.'
                            : 'Uma nova versão do Voto Aberto está disponível.',
                      ),
                    ),
                    TextButton(
                      onPressed: busy ? null : _start,
                      child: Text(busy ? 'Atualizando…' : 'Atualizar'),
                    ),
                    IconButton(
                      tooltip: 'Agora não',
                      onPressed: busy
                          ? null
                          : () => setState(() => notice = null),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    ),
  );
}

class ReleaseAboutButton extends StatelessWidget {
  const ReleaseAboutButton({super.key});
  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: 'Sobre o Voto Aberto',
    icon: const Icon(Icons.more_horiz),
    onPressed: () => showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Voto Aberto'),
        content: FutureBuilder<AppVersionInfo?>(
          future: context
              .dependOnInheritedWidgetOfExactType<ReleaseInfo>()
              ?.version(),
          builder: (_, snapshot) => Text(
            snapshot.data == null
                ? 'Versão indisponível'
                : 'Versão ${snapshot.data!.publicVersion}\nBuild ${snapshot.data!.build}',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fechar'),
          ),
        ],
      ),
    ),
  );
}
