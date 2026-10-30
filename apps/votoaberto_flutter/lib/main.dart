import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'app/votoaberto_app.dart';
import 'features/elections/data/embedded_election_repository.dart';
import 'features/elections/data/mock_election_repository.dart';
import 'features/elections/domain/election.dart';

class _BuildConfiguration {
  const _BuildConfiguration(this.mode, bool hasVersion, bool hasHash)
    : assert(
        mode != 'real' || (hasVersion && hasHash),
        'Build real requer o preflight: python tool/embedded_build.py ... --mode real',
      );
  final String mode;
}

const _configuration = _BuildConfiguration(
  String.fromEnvironment('VOTOABERTO_DATA', defaultValue: 'demo'),
  bool.hasEnvironment('VOTOABERTO_DATASET'),
  bool.hasEnvironment('VOTOABERTO_MANIFEST_SHA256'),
);

void main() {
  LicenseRegistry.addLicense(() async* {
    final license = await rootBundle.loadString(
      'assets/fonts/LICENSE-Roboto.txt',
    );
    yield LicenseEntryWithLineBreaks(['Roboto'], license);
  });
  // Composition root: the UI only receives the ElectionRepository contract.
  final mode = _configuration.mode;
  const version = String.fromEnvironment('VOTOABERTO_DATASET');
  const manifestHash = String.fromEnvironment('VOTOABERTO_MANIFEST_SHA256');
  if (!['demo', 'fixture', 'real'].contains(mode)) {
    throw StateError(
      'Modo de dados inválido. Use o comando de build documentado.',
    );
  }
  runApp(
    VotoAbertoApp(
      election: mode == 'demo'
          ? Election.demonstration
          : Election.presidential2026,
      repository: mode == 'demo'
          ? MockElectionRepository()
          : EmbeddedElectionRepository(
              assetRoot: mode == 'real'
                  ? 'assets/data/real'
                  : 'assets/data/synthetic',
              expectedNature: mode == 'real' ? 'official-derived' : 'synthetic',
              expectedDatasetId: version.isEmpty ? null : version,
              expectedManifestHash: manifestHash.isEmpty ? null : manifestHash,
            ),
    ),
  );
}
