import 'dart:convert';
import 'dart:math' as math;
import 'dart:ui';

import '../../elections/domain/geography.dart';

/// Rendering adapter for GeoJSON Polygon / MultiPolygon, including interior
/// rings. No election/navigation dependency beyond a UF identifier.
class StateGeometry {
  StateGeometry(this.state, this.path, this.label);
  final BrazilianState state;
  final Path path;
  final Offset label;
  Rect get bounds => path.getBounds();
}

class BrazilGeometry {
  BrazilGeometry._(this.states, this.bounds);
  final List<StateGeometry> states;
  final Rect bounds;

  // Equirectangular with standard parallel 14°S. No areas or distances are
  // inferred from this presentation projection. Input is longitude, latitude.
  static Offset project(double longitude, double latitude) =>
      Offset(longitude * math.cos(14 * math.pi / 180), -latitude);

  factory BrazilGeometry.decode(String source) {
    final json = jsonDecode(source) as Map<String, dynamic>;
    final features = json['features'] as List<dynamic>;
    final states = <StateGeometry>[];
    for (final raw in features) {
      final feature = raw as Map<String, dynamic>;
      final properties = feature['properties'] as Map<String, dynamic>;
      final id = properties['codarea'] as String;
      final state = BrazilianState.values.firstWhere((s) => s.ibgeCode == id);
      final geometry = feature['geometry'] as Map<String, dynamic>;
      final coordinates = geometry['coordinates'] as List<dynamic>;
      final polygons = switch (geometry['type']) {
        'Polygon' => <dynamic>[coordinates],
        'MultiPolygon' => coordinates,
        _ => throw FormatException(
          'Geometria não suportada: ${geometry['type']}',
        ),
      };
      final path = Path()..fillType = PathFillType.evenOdd;
      for (final polygon in polygons) {
        for (final ring in polygon as List<dynamic>) {
          final points = ring as List<dynamic>;
          if (points.length < 4) throw const FormatException('Anel incompleto');
          for (var i = 0; i < points.length; i++) {
            final pair = points[i] as List<dynamic>;
            final x = (pair[0] as num).toDouble();
            final y = (pair[1] as num).toDouble();
            if (!x.isFinite || !y.isFinite || x.abs() > 180 || y.abs() > 90) {
              throw const FormatException('Coordenadas inválidas');
            }
            final point = project(x, y);
            if (i == 0) {
              path.moveTo(point.dx, point.dy);
            } else {
              path.lineTo(point.dx, point.dy);
            }
          }
          path.close();
        }
      }
      final anchor = _anchors[state]!;
      states.add(StateGeometry(state, path, project(anchor.$1, anchor.$2)));
    }
    if (states.length != 27 ||
        states.map((s) => s.state).toSet().length != 27) {
      throw const FormatException('São necessárias exatamente 27 UFs únicas');
    }
    final bounds = states
        .map((s) => s.bounds)
        .reduce((a, b) => a.expandToInclude(b));
    return BrazilGeometry._(List.unmodifiable(states), bounds);
  }

  BrazilianState? hitTest(Offset point) {
    // Smallest first resolves shared edges in favour of DF / small states.
    final ordered = [...states]
      ..sort(
        (a, b) => (a.bounds.width * a.bounds.height).compareTo(
          b.bounds.width * b.bounds.height,
        ),
      );
    for (final shape in ordered) {
      if (shape.path.contains(point)) return shape.state;
    }
    return null;
  }

  Rect viewFor(BrazilianState? state) {
    if (state == null) return bounds.inflate(1.5);
    final target = states.firstWhere((s) => s.state == state).bounds;
    return Rect.fromCenter(
      center: target.center,
      width: math.max(2.5, target.width * 1.35),
      height: math.max(2.5, target.height * 1.35),
    );
  }

  /// Label anchors are display positions inside the state, not polling points.
  static const _anchors = <BrazilianState, (double, double)>{
    BrazilianState.ac: (-70, -9.3),
    BrazilianState.al: (-36.5, -9.5),
    BrazilianState.ap: (-51.8, 1),
    BrazilianState.am: (-64, -4),
    BrazilianState.ba: (-41.5, -12.5),
    BrazilianState.ce: (-39.5, -5),
    BrazilianState.df: (-47.8, -15.8),
    BrazilianState.es: (-40.6, -19.5),
    BrazilianState.go: (-49.5, -16.5),
    BrazilianState.ma: (-45, -5),
    BrazilianState.mt: (-56, -13),
    BrazilianState.ms: (-54.5, -20.5),
    BrazilianState.mg: (-44.5, -18.5),
    BrazilianState.pa: (-53, -4),
    BrazilianState.pb: (-36.5, -7.2),
    BrazilianState.pr: (-51, -24.5),
    BrazilianState.pe: (-38, -8.5),
    BrazilianState.pi: (-42.5, -7.5),
    BrazilianState.rj: (-42.5, -22.2),
    BrazilianState.rn: (-36.5, -5.7),
    BrazilianState.rs: (-53, -30),
    BrazilianState.ro: (-63, -11),
    BrazilianState.rr: (-61, 2),
    BrazilianState.sc: (-50.3, -27),
    BrazilianState.sp: (-48.5, -22),
    BrazilianState.se: (-37.3, -10.5),
    BrazilianState.to: (-48.3, -10),
  };
}

/// Uniform fit keeps the geographic aspect ratio on every viewport size.
class MapViewport {
  MapViewport(this.world, this.size)
    : scale = math.min(size.width / world.width, size.height / world.height);
  final Rect world;
  final Size size;
  final double scale;
  Offset toScreen(Offset point) =>
      (point - world.center) * scale + size.center(Offset.zero);
  Offset toWorld(Offset point) =>
      (point - size.center(Offset.zero)) / scale + world.center;
}
