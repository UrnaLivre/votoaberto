import 'dart:convert';
import 'dart:io';
import 'package:package_info_plus/package_info_plus.dart';
import 'android_update_provider.dart';
import 'app_version_info.dart';
import 'update_service.dart';
import 'windows_update_provider.dart';

PlatformUpdateProvider provider(AppVersionInfo version) {
  if (Platform.isAndroid) {
    return AndroidUpdateProvider(
      OfficialPlayUpdateClient(),
      installedBuild: version.build,
      isPlayInstall: () async =>
          (await PackageInfo.fromPlatform()).installerStore ==
          'com.android.vending',
    );
  }
  if (Platform.isWindows) {
    return WindowsUpdateProvider(version, githubReleasePage);
  }
  return const UnsupportedUpdateProvider();
}

Future<List<Object?>> githubReleasePage(int page) async {
  final client = HttpClient()..connectionTimeout = const Duration(seconds: 3);
  try {
    return await (() async {
      final request = await client.getUrl(
        Uri.https('api.github.com', '/repos/UrnaLivre/votoaberto/releases', {
          'per_page': '100',
          'page': '$page',
        }),
      );
      request.followRedirects = false;
      request.headers.set('Accept', 'application/vnd.github+json');
      request.headers.set('X-GitHub-Api-Version', '2022-11-28');
      request.headers.set('User-Agent', 'VotoAberto');
      final response = await request.close();
      if (response.statusCode != HttpStatus.ok) {
        throw const HttpException('Release query unavailable');
      }
      final bytes = <int>[];
      await for (final chunk in response) {
        bytes.addAll(chunk);
        if (bytes.length > 2 * 1024 * 1024) {
          throw const FormatException('Release response too large');
        }
      }
      final json = jsonDecode(utf8.decode(bytes));
      if (json is! List) {
        throw const FormatException('Invalid release response');
      }
      return json.cast<Object?>();
    })().timeout(const Duration(seconds: 5));
  } finally {
    client.close(force: true);
  }
}
