import 'package:flutter/widgets.dart';
import 'package:url_launcher_platform_interface/link.dart';
import 'package:url_launcher_web/url_launcher_web.dart';

// Use the official Web delegate directly: no native URL-launcher plugins.
Widget buildLink(LinkInfo link) => UrlLauncherPlugin().linkDelegate(link);
