import 'package:in_app_update/in_app_update.dart' as play;
import 'update_service.dart';

abstract interface class PlayUpdateClient {
  Future<play.AppUpdateInfo> check();
  Future<play.AppUpdateResult> download();
  Future<void> complete();
}

class OfficialPlayUpdateClient implements PlayUpdateClient {
  @override
  Future<play.AppUpdateInfo> check() => play.InAppUpdate.checkForUpdate();
  @override
  Future<play.AppUpdateResult> download() =>
      play.InAppUpdate.startFlexibleUpdate();
  @override
  Future<void> complete() => play.InAppUpdate.completeFlexibleUpdate();
}

class AndroidUpdateProvider implements PlatformUpdateProvider {
  AndroidUpdateProvider(
    this.client, {
    required this.installedBuild,
    required this.isPlayInstall,
  });
  final PlayUpdateClient client;
  final int installedBuild;
  final Future<bool> Function() isPlayInstall;
  String? _identity;
  bool _downloaded = false;
  bool _eligible = false;

  @override
  Future<UpdateCheck> check() async {
    if (!await isPlayInstall()) {
      return const UpdateCheck(UpdateAvailability.unsupported);
    }
    final info = await client.check();
    final code = info.availableVersionCode;
    if (info.packageName != 'br.com.urnalivre.votoaberto') {
      return const UpdateCheck(UpdateAvailability.unavailable);
    }
    if (code == null ||
        code <= installedBuild ||
        info.updateAvailability == play.UpdateAvailability.updateNotAvailable) {
      return const UpdateCheck(UpdateAvailability.upToDate);
    }
    _identity = 'play:$code';
    if (info.installStatus == play.InstallStatus.downloaded) {
      _downloaded = true;
      _eligible = true;
      return UpdateCheck(
        UpdateAvailability.readyToInstall,
        identity: '$_identity:install',
        canStart: true,
      );
    }
    if ({
      play.InstallStatus.downloading,
      play.InstallStatus.pending,
      play.InstallStatus.installing,
    }.contains(info.installStatus)) {
      return const UpdateCheck(UpdateAvailability.inProgress);
    }
    _eligible =
        info.flexibleUpdateAllowed &&
        info.updateAvailability == play.UpdateAvailability.updateAvailable;
    return UpdateCheck(
      _eligible ? UpdateAvailability.available : UpdateAvailability.unavailable,
      identity: _identity,
      canStart: _eligible,
    );
  }

  @override
  Future<UpdateCheck> start() async {
    if (!_eligible) return const UpdateCheck(UpdateAvailability.unavailable);
    if (_downloaded) {
      await client.complete();
      return const UpdateCheck(UpdateAvailability.inProgress);
    }
    final result = await client.download();
    if (result != play.AppUpdateResult.success) {
      return const UpdateCheck(UpdateAvailability.unavailable);
    }
    _downloaded = true;
    // Completing restarts the app; request a second explicit user action.
    return UpdateCheck(
      UpdateAvailability.readyToInstall,
      identity: '$_identity:install',
      canStart: true,
    );
  }
}
