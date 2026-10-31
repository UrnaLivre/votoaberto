import 'package:flutter/material.dart';
import 'package:url_launcher_platform_interface/link.dart';

import 'institutional_link_stub.dart'
    if (dart.library.js_interop) 'institutional_link_web.dart'
    as platform;

const institutionalUrl = 'https://urnalivre.com.br/';

/// Kept in the Scaffold's layout so it never covers maps or result controls.
class InstitutionalLink extends StatelessWidget implements LinkInfo {
  const InstitutionalLink({super.key, this.openUrl});

  final void Function(String url)? openUrl;

  @override
  Uri get uri => Uri.parse(institutionalUrl);
  @override
  LinkTarget get target => LinkTarget.blank;
  @override
  bool get isDisabled => false;
  @override
  LinkWidgetBuilder get builder =>
      (context, followLink) => TextButton(
        key: const ValueKey('institutional-link'),
        onPressed: openUrl == null
            ? followLink
            : () => openUrl!(institutionalUrl),
        child: const Text(
          'Uma iniciativa Urna Livre',
          semanticsLabel: 'Uma iniciativa Urna Livre (abre em nova aba)',
          textAlign: TextAlign.center,
        ),
      );

  @override
  Widget build(BuildContext context) => SafeArea(
    top: false,
    minimum: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
    child: platform.buildLink(this),
  );
}
