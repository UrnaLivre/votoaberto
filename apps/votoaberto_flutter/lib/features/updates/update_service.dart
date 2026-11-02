import 'dart:async';

enum UpdateAvailability {
  upToDate,
  available,
  unavailable,
  unsupported,
  inProgress,
  readyToInstall,
}

class UpdateCheck {
  const UpdateCheck(this.availability, {this.identity, this.canStart = false});
  final UpdateAvailability availability;
  final String? identity;
  final bool canStart;
}

abstract interface class PlatformUpdateProvider {
  Future<UpdateCheck> check();

  /// Called only after an explicit user action. Windows has no implementation.
  Future<UpdateCheck> start();
}

class UnsupportedUpdateProvider implements PlatformUpdateProvider {
  const UnsupportedUpdateProvider();
  @override
  Future<UpdateCheck> check() async =>
      const UpdateCheck(UpdateAvailability.unsupported);
  @override
  Future<UpdateCheck> start() => check();
}

abstract interface class UpdateNoticeStore {
  Future<String?> read();
  Future<void> write(String identity);
}

/// One check per process/session, shared across all routes. No polling/retries.
class UpdateService {
  UpdateService(
    this.provider,
    this.notices, {
    this.timeout = const Duration(seconds: 8),
  });
  final PlatformUpdateProvider provider;
  final UpdateNoticeStore notices;
  final Duration timeout;
  Future<UpdateCheck>? _check;
  bool _claimed = false;
  bool _started = false;

  Future<UpdateCheck> checkOnce() => _check ??= _safeCheck();

  Future<UpdateCheck> _safeCheck() async {
    try {
      return await provider.check().timeout(timeout);
    } on Exception {
      return const UpdateCheck(UpdateAvailability.unavailable);
    }
  }

  Future<bool> claimNotice(UpdateCheck result) async {
    if (_claimed ||
        !result.canStart ||
        result.identity == null ||
        !{
          UpdateAvailability.available,
          UpdateAvailability.readyToInstall,
        }.contains(result.availability)) {
      return false;
    }
    _claimed = true;
    try {
      if (await notices.read().timeout(timeout) == result.identity) {
        return false;
      }
      await notices.write(result.identity!).timeout(timeout);
    } on Exception {
      // A failed local preference never blocks the app; once this session only.
    }
    return true;
  }

  Future<UpdateCheck> start() async {
    final result = await checkOnce();
    if (!result.canStart || _started) return result;
    _started = true;
    try {
      // Play owns the download lifetime; do not time out/cancel it mid-transfer.
      final next = await provider.start();
      if (next.availability == UpdateAvailability.readyToInstall) {
        _started = false;
      }
      return next;
    } on Exception {
      return const UpdateCheck(UpdateAvailability.unavailable);
    }
  }
}
