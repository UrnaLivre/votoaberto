import 'app_version_info.dart';
import 'update_service.dart';

PlatformUpdateProvider provider(AppVersionInfo version) =>
    const UnsupportedUpdateProvider();
