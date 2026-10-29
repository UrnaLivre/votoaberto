import 'election.dart';

abstract interface class ElectionRepository {
  Future<ElectionDataset> load(Election election);
}

/// Extension point only. No fake network request or fallback to mock data.
/// M2 must implement transport, decoding, coverage and provenance validation.
abstract class ApiElectionRepository implements ElectionRepository {
  ApiElectionRepository(this.baseUri);
  final Uri baseUri;
}
