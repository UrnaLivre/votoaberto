import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'app/votoaberto_app.dart';
import 'features/elections/data/mock_election_repository.dart';

void main() {
  LicenseRegistry.addLicense(() async* {
    final license = await rootBundle.loadString(
      'assets/fonts/LICENSE-Roboto.txt',
    );
    yield LicenseEntryWithLineBreaks(['Roboto'], license);
  });
  // Composition root: the UI only receives the ElectionRepository contract.
  runApp(VotoAbertoApp(repository: MockElectionRepository()));
}
