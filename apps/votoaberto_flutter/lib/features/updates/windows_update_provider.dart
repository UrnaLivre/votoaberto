import 'app_version_info.dart';
import 'update_service.dart';

typedef ReleasePageLoader = Future<List<Object?>> Function(int page);

/// Metadata contract for M9. A digest is necessary, but is not a trust signature.
class WindowsRelease {
  const WindowsRelease(this.version, this.installer, this.sha256);
  final AppVersionInfo version;
  final Uri installer;
  final String sha256;

  static WindowsRelease? fromGithub(Object? value) {
    if (value is! Map ||
        value['draft'] != false ||
        value['prerelease'] != false) {
      return null;
    }
    final tag = value['tag_name'];
    if (tag is! String || !tag.startsWith('app-v')) return null;
    try {
      final version = AppVersionInfo.parse(tag.substring(5));
      final name = 'votoaberto-${version.identity}-windows-x64-setup.exe';
      final assets = value['assets'];
      if (assets is! List) return null;
      final matches = assets
          .where((a) => a is Map && a['name'] == name)
          .toList();
      if (matches.length != 1) return null;
      final asset = matches.single as Map;
      final digest = asset['digest'];
      final url = asset['browser_download_url'];
      final size = asset['size'];
      if (asset['state'] != 'uploaded' ||
          size is! int ||
          size <= 0 ||
          digest is! String ||
          !RegExp(r'^sha256:[a-f0-9]{64}$').hasMatch(digest) ||
          url is! String) {
        return null;
      }
      final uri = Uri.parse(url);
      if (uri.scheme != 'https' ||
          uri.host != 'github.com' ||
          uri.hasPort ||
          uri.userInfo.isNotEmpty ||
          uri.hasQuery ||
          uri.hasFragment ||
          uri.pathSegments.join('/') !=
              'UrnaLivre/votoaberto/releases/download/$tag/$name') {
        return null;
      }
      return WindowsRelease(version, uri, digest.substring(7));
    } on FormatException {
      return null;
    }
  }
}

class WindowsUpdateProvider implements PlatformUpdateProvider {
  WindowsUpdateProvider(this.installed, this.loadPage);
  final AppVersionInfo installed;
  final ReleasePageLoader loadPage;
  WindowsRelease? candidate;

  @override
  Future<UpdateCheck> check() async {
    final elapsed = Stopwatch()..start();
    WindowsRelease? best;
    // Paginate the releases collection, never /releases/latest. Bounded traffic.
    for (var page = 1; page <= 5; page++) {
      final releases = await loadPage(page);
      if (elapsed.elapsed >= const Duration(seconds: 8)) {
        return const UpdateCheck(UpdateAvailability.unavailable);
      }
      for (final value in releases) {
        final release = WindowsRelease.fromGithub(value);
        if (release != null &&
            release.version.compareTo(installed) > 0 &&
            release.version.build > installed.build &&
            (best == null || release.version.compareTo(best.version) > 0)) {
          best = release;
        }
      }
      if (releases.length < 100) {
        candidate = best;
        return best == null
            ? const UpdateCheck(UpdateAvailability.upToDate)
            : UpdateCheck(
                UpdateAvailability.available,
                identity: 'windows:${best.version.identity}',
              );
      }
    }
    // The bounded result may be incomplete; don't assert that it is current.
    return const UpdateCheck(UpdateAvailability.unavailable);
  }

  @override
  Future<UpdateCheck> start() async =>
      const UpdateCheck(UpdateAvailability.unsupported);
}
