/// Stable product version. The fourth Windows component is the Android build.
class AppVersionInfo implements Comparable<AppVersionInfo> {
  const AppVersionInfo(this.major, this.minor, this.patch, this.build);
  final int major, minor, patch, build;

  static AppVersionInfo parse(String value) {
    final match = RegExp(
      r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\+([1-9]\d*)$',
    ).firstMatch(value);
    if (match == null) throw FormatException('Invalid stable version', value);
    final parts = [for (var i = 1; i <= 4; i++) int.parse(match.group(i)!)];
    if (parts.any((part) => part > 65535)) {
      throw FormatException('Version exceeds Windows component range', value);
    }
    return AppVersionInfo(parts[0], parts[1], parts[2], parts[3]);
  }

  String get publicVersion => '$major.$minor.$patch';
  String get identity => '$publicVersion+$build';
  String get windowsVersion => '$major.$minor.$patch.$build';

  @override
  int compareTo(AppVersionInfo other) {
    final left = [major, minor, patch, build];
    final right = [other.major, other.minor, other.patch, other.build];
    for (var i = 0; i < left.length; i++) {
      final order = left[i].compareTo(right[i]);
      if (order != 0) return order;
    }
    return 0;
  }
}
