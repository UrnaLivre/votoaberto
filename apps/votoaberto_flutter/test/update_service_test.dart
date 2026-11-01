import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:in_app_update/in_app_update.dart' as play;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:votoaberto/features/updates/android_update_provider.dart';
import 'package:votoaberto/features/updates/app_version_info.dart';
import 'package:votoaberto/features/updates/release_host.dart';
import 'package:votoaberto/features/updates/platform_updates.dart';
import 'package:votoaberto/features/updates/update_service.dart';
import 'package:votoaberto/features/updates/windows_update_provider.dart';

class Notices implements UpdateNoticeStore {
  String? value;
  @override
  Future<String?> read() async => value;
  @override
  Future<void> write(String identity) async => value = identity;
}

class Provider implements PlatformUpdateProvider {
  Provider(this.result);
  final Future<UpdateCheck> Function() result;
  int calls = 0, starts = 0;
  @override
  Future<UpdateCheck> check() {
    calls++;
    return result();
  }

  @override
  Future<UpdateCheck> start() async {
    starts++;
    return const UpdateCheck(UpdateAvailability.inProgress);
  }
}

Map<String, Object?> release(
  String version, {
  String? tag,
  bool draft = false,
  bool prerelease = false,
  String host = 'github.com',
  bool digest = true,
}) {
  final actualTag = tag ?? 'app-v$version';
  final name = 'votoaberto-$version-windows-x64-setup.exe';
  return {
    'tag_name': actualTag,
    'draft': draft,
    'prerelease': prerelease,
    'assets': [
      {
        'name': name,
        'state': 'uploaded',
        'size': 100,
        'digest': digest ? 'sha256:${'a' * 64}' : null,
        'browser_download_url':
            'https://$host/UrnaLivre/votoaberto/releases/download/$actualTag/$name',
      },
    ],
  };
}

class PlayClient implements PlayUpdateClient {
  PlayClient({
    this.code = 4,
    this.allowed = true,
    this.status = play.InstallStatus.unknown,
    this.availability = play.UpdateAvailability.updateAvailable,
  });
  final int code;
  final bool allowed;
  final play.InstallStatus status;
  final play.UpdateAvailability availability;
  int checks = 0, downloads = 0, completions = 0;
  @override
  Future<play.AppUpdateInfo> check() async {
    checks++;
    return play.AppUpdateInfo(
      updateAvailability: availability,
      immediateUpdateAllowed: true,
      immediateAllowedPreconditions: [],
      flexibleUpdateAllowed: allowed,
      flexibleAllowedPreconditions: [],
      availableVersionCode: code,
      installStatus: status,
      packageName: 'br.com.urnalivre.votoaberto',
      clientVersionStalenessDays: 1,
      updatePriority: 0,
    );
  }

  @override
  Future<play.AppUpdateResult> download() async {
    downloads++;
    return play.AppUpdateResult.success;
  }

  @override
  Future<void> complete() async {
    completions++;
  }
}

void main() {
  final installed = AppVersionInfo.parse('0.5.0+3');
  const available = UpdateCheck(
    UpdateAvailability.available,
    identity: 'play:4',
    canStart: true,
  );

  test(
    'stable versions compare numeric components and expose installed version',
    () {
      expect(installed.publicVersion, '0.5.0');
      expect(installed.windowsVersion, '0.5.0.3');
      expect(installed.compareTo(AppVersionInfo.parse('0.5.0+3')), 0);
      expect(
        AppVersionInfo.parse('0.10.0+4').compareTo(installed),
        greaterThan(0),
      );
      expect(
        AppVersionInfo.parse('0.5.0+10').compareTo(installed),
        greaterThan(0),
      );
      for (final invalid in [
        'v0.5.0+3',
        '0.5.0',
        '0.5.0+0',
        '0.5.0+03',
        '0.5.0-rc.1+4',
        '0.5.0+65536',
      ]) {
        expect(() => AppVersionInfo.parse(invalid), throwsFormatException);
      }
    },
  );

  test('installed metadata is read from the package rather than a hardcoded version', () async {
    PackageInfo.setMockInitialValues(
      appName: 'Voto Aberto',
      packageName: 'br.com.urnalivre.votoaberto',
      version: '0.6.0',
      buildNumber: '8',
      buildSignature: 'test',
    );
    expect((await installedAppVersion())!.identity, '0.6.0+8');
  });

  test('Android recognizes a previously downloaded update without another download', () async {
    final client = PlayClient(status: play.InstallStatus.downloaded);
    final service = UpdateService(
      AndroidUpdateProvider(
        client,
        installedBuild: 3,
        isPlayInstall: () async => true,
      ),
      Notices(),
    );
    expect(
      (await service.checkOnce()).availability,
      UpdateAvailability.readyToInstall,
    );
    await service.start();
    expect(client.downloads, 0);
    expect(client.completions, 1);
  });

  for (final state in [
    UpdateAvailability.upToDate,
    UpdateAvailability.unavailable,
    UpdateAvailability.unsupported,
    UpdateAvailability.inProgress,
  ]) {
    test('$state is silent and checks only once even concurrently', () async {
      final provider = Provider(() async => UpdateCheck(state));
      final service = UpdateService(provider, Notices());
      final results = await Future.wait([
        service.checkOnce(),
        service.checkOnce(),
      ]);
      expect(results.first.availability, state);
      expect(provider.calls, 1);
      expect(await service.claimNotice(results.first), false);
      await service.start();
      expect(provider.starts, 0);
    });
  }

  test('offline, failed query and timeout stay silent', () async {
    for (final query in <Future<UpdateCheck> Function()>[
      () async => throw const SocketException('offline'),
      () async => throw const FormatException('bad response'),
      () => Completer<UpdateCheck>().future,
    ]) {
      final service = UpdateService(
        Provider(query),
        Notices(),
        timeout: const Duration(milliseconds: 5),
      );
      expect(
        (await service.checkOnce()).availability,
        UpdateAvailability.unavailable,
      );
    }
  });

  test(
    'notice is persisted once and no navigation/restart repeats it',
    () async {
      final store = Notices();
      final first = UpdateService(Provider(() async => available), store);
      expect(await first.claimNotice(await first.checkOnce()), true);
      expect(await first.claimNotice(available), false);
      final restart = UpdateService(Provider(() async => available), store);
      expect(await restart.claimNotice(await restart.checkOnce()), false);
    },
  );

  test(
    'Windows excludes data, tests, absent installers and foreign origin',
    () async {
      final provider = WindowsUpdateProvider(
        installed,
        (_) async => [
          release('9.0.0+10', tag: 'web-data-2026-v1'),
          release('8.0.0+10', draft: true),
          release('7.0.0+10', prerelease: true),
          release('6.0.0-rc.1+10'),
          release('5.0.0+10', host: 'evil.example'),
          release('4.0.0+10', digest: false),
          {'tag_name': 'app-v3.0.0+10'},
          release('3.0.0+2'),
          release('0.5.1+4'),
          release('0.6.0+5'),
        ],
      );
      final result = await provider.check();
      expect(result.availability, UpdateAvailability.available);
      expect(provider.candidate!.version.identity, '0.6.0+5');
      expect(
        result.canStart,
        false,
        reason: 'M9 owns installer validation and consent',
      );
      expect(
        (await provider.start()).availability,
        UpdateAvailability.unsupported,
      );
    },
  );

  test('Windows no published app release never invents an update', () async {
    for (final releases in [
      <Object?>[],
      [release('1.0.0+4', tag: 'web-data-2026-v1')],
      [release('0.5.0+3')],
    ]) {
      final result = await WindowsUpdateProvider(
        installed,
        (_) async => releases,
      ).check();
      expect(result.availability, UpdateAvailability.upToDate);
    }
  });

  test(
    'Windows paginates past data releases with a bounded request count',
    () async {
      final pages = <int>[];
      final provider = WindowsUpdateProvider(installed, (page) async {
        pages.add(page);
        return page == 1
            ? List.filled(100, release('9.0.0+5', tag: 'web-data-2026-v1'))
            : [release('0.6.0+4')];
      });
      expect(
        (await provider.check()).availability,
        UpdateAvailability.available,
      );
      expect(pages, [1, 2]);
      final bounded = WindowsUpdateProvider(
        installed,
        (_) async => List.filled(100, null),
      );
      expect(
        (await bounded.check()).availability,
        UpdateAvailability.unavailable,
      );
    },
  );

  test('external Android install never calls Play', () async {
    final client = PlayClient();
    final provider = AndroidUpdateProvider(
      client,
      installedBuild: 3,
      isPlayInstall: () async => false,
    );
    expect(
      (await provider.check()).availability,
      UpdateAvailability.unsupported,
    );
    expect(client.checks, 0);
  });

  test(
    'Android compares versionCodes and requires flexible eligibility',
    () async {
      for (final client in [
        PlayClient(code: 2),
        PlayClient(code: 3),
        PlayClient(allowed: false),
        PlayClient(availability: play.UpdateAvailability.updateNotAvailable),
      ]) {
        final result = await AndroidUpdateProvider(
          client,
          installedBuild: 3,
          isPlayInstall: () async => true,
        ).check();
        expect(result.canStart, false);
      }
    },
  );

  test(
    'Android flexible flow requires consent again before restarting',
    () async {
      final client = PlayClient();
      final service = UpdateService(
        AndroidUpdateProvider(
          client,
          installedBuild: 3,
          isPlayInstall: () async => true,
        ),
        Notices(),
      );
      expect(
        (await service.checkOnce()).availability,
        UpdateAvailability.available,
      );
      expect(client.downloads, 0);
      expect(
        (await service.start()).availability,
        UpdateAvailability.readyToInstall,
      );
      expect(client.completions, 0);
      await service.start();
      expect(client.downloads, 1);
      expect(client.completions, 1);
    },
  );

  testWidgets(
    'version, nonblocking startup and one dismissible notice across rebuilds',
    (tester) async {
      final provider = Provider(() async => available);
      final service = UpdateService(provider, Notices());
      Widget app() => MaterialApp(
        home: ReleaseHost(
          versionLoader: () async => installed,
          serviceFactory: (_) => service,
          child: const Scaffold(
            body: Column(children: [Text('Resultados'), ReleaseAboutButton()]),
          ),
        ),
      );
      await tester.pumpWidget(app());
      await tester.pumpAndSettle();
      expect(find.text('Resultados'), findsOneWidget);
      expect(
        find.text('Uma nova versão do Voto Aberto está disponível.'),
        findsOneWidget,
      );
      await tester.tap(find.byTooltip('Sobre o Voto Aberto'));
      await tester.pumpAndSettle();
      expect(find.text('Versão 0.5.0\nBuild 3'), findsOneWidget);
      await tester.tap(find.text('Fechar'));
      await tester.pumpAndSettle();
      await tester.tap(find.byTooltip('Agora não'));
      await tester.pumpWidget(app());
      await tester.pumpAndSettle();
      expect(find.text('Atualizar'), findsNothing);
      expect(provider.calls, 1);
    },
  );
}
