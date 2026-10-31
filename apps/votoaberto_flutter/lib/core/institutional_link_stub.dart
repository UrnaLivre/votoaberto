import 'package:flutter/widgets.dart';
import 'package:url_launcher_platform_interface/link.dart';

// Native layouts never include the footer. This delegate supports widget tests.
Widget buildLink(LinkInfo link) => Builder(
  builder: (context) => MergeSemantics(
    child: Semantics(
      link: true,
      linkUrl: link.uri,
      child: link.builder(context, null),
    ),
  ),
);
