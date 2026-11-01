import 'package:flutter/foundation.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'app_version_info.dart';
import 'update_service.dart';
import 'platform_updates_stub.dart'
    if (dart.library.io) 'platform_updates_io.dart'
    as platform;

Future<AppVersionInfo?> installedAppVersion() async {
  try {
    final info = await PackageInfo.fromPlatform().timeout(
      const Duration(seconds: 3),
    );
    return AppVersionInfo.parse('${info.version}+${info.buildNumber}');
  } on Exception {
    return null;
  }
}

class LocalUpdateNoticeStore implements UpdateNoticeStore {
  final _preferences = SharedPreferencesAsync();
  static const key = 'last_update_notice';
  @override
  Future<String?> read() => _preferences.getString(key);
  @override
  Future<void> write(String identity) => _preferences.setString(key, identity);
}

UpdateService platformUpdateService(AppVersionInfo version) => UpdateService(
  // Debug, profile and Web never query Play/GitHub or write update preferences.
  kReleaseMode && !kIsWeb
      ? platform.provider(version)
      : const UnsupportedUpdateProvider(),
  LocalUpdateNoticeStore(),
);
