import 'dart:convert';
import 'dart:math' as math;
import 'dart:ui';

class CountryGeometry {
  CountryGeometry(this.iso, this.name, this.path, this.anchor);
  final String iso;
  final String name;
  final Path path;
  final Offset anchor;
  Rect get bounds => path.getBounds();
}

class WorldGeometry {
  WorldGeometry(this.countries);
  final List<CountryGeometry> countries;
  static const bounds = Rect.fromLTRB(-180, -85, 180, 90);
  static Offset project(double lon, double lat) => Offset(lon, -lat);

  factory WorldGeometry.decode(String source) {
    final json = jsonDecode(source) as Map<String, dynamic>;
    final shapes = <CountryGeometry>[];
    final seen = <String>{};
    for (final feature
        in (json['features'] as List).cast<Map<String, dynamic>>()) {
      final props = feature['properties'] as Map<String, dynamic>;
      final iso = props['iso'] as String;
      if (!seen.add(iso)) throw const FormatException('País duplicado');
      final geo = feature['geometry'] as Map<String, dynamic>;
      final coords = geo['coordinates'] as List;
      final List<dynamic> polygons;
      switch (geo['type']) {
        case 'Polygon':
          polygons = [coords];
        case 'MultiPolygon':
          polygons = coords;
        default:
          throw const FormatException('Geometria mundial inválida');
      }
      final longitudes = <double>[];
      for (final polygon in polygons) {
        for (final ring in polygon as List) {
          if ((ring as List).length < 4) {
            throw const FormatException('Anel incompleto');
          }
          for (final pair in ring) {
            final lon = (pair[0] as num).toDouble();
            final lat = (pair[1] as num).toDouble();
            if (!lon.isFinite ||
                !lat.isFinite ||
                lon.abs() > 180 ||
                lat.abs() > 90) {
              throw const FormatException('Coordenada mundial inválida');
            }
            longitudes.add(lon % 360);
          }
        }
      }
      if (longitudes.isEmpty) throw const FormatException('País sem geometria');
      longitudes.sort();
      var cut = longitudes.first;
      var largestGap = -1.0;
      for (var i = 0; i < longitudes.length; i++) {
        final next = i + 1 == longitudes.length
            ? longitudes.first + 360
            : longitudes[i + 1];
        if (next - longitudes[i] > largestGap) {
          largestGap = next - longitudes[i];
          cut = next % 360;
        }
      }
      // Put the cut in the largest empty longitude interval. Multipart countries
      // crossing ±180 then fit in one continuous camera; render periodic copies.
      final center = cut + (360 - largestGap) / 2;
      final shift = (center / 360).round() * 360;
      Offset point(dynamic pair) {
        var lon = (pair[0] as num).toDouble() % 360;
        if (lon < cut - 1e-8) lon += 360;
        return project(lon - shift, (pair[1] as num).toDouble());
      }

      final path = Path()..fillType = PathFillType.evenOdd;
      Rect? primary;
      for (final polygon in polygons) {
        for (var r = 0; r < (polygon as List).length; r++) {
          final ring = polygon[r] as List;
          final component = Path();
          for (var i = 0; i < ring.length; i++) {
            final p = point(ring[i]);
            if (i == 0) {
              component.moveTo(p.dx, p.dy);
            } else {
              component.lineTo(p.dx, p.dy);
            }
          }
          component.close();
          path.addPath(component, Offset.zero);
          final b = component.getBounds();
          if (r == 0 &&
              (primary == null ||
                  b.width * b.height > primary.width * primary.height)) {
            primary = b;
          }
        }
      }
      shapes.add(
        CountryGeometry(iso, props['name'] as String, path, primary!.center),
      );
    }
    return WorldGeometry(List.unmodifiable(shapes));
  }

  Rect viewFor(String? iso) {
    final country = countries.where((c) => c.iso == iso).firstOrNull;
    if (country == null) return bounds;
    final b = country.bounds;
    return Rect.fromCenter(
      center: b.center,
      width: math.max(5, b.width * 1.25),
      height: math.max(5, b.height * 1.25),
    );
  }

  String? hitTest(Offset point, Set<String> active, {double tolerance = 0}) {
    final sorted = countries.where((c) => active.contains(c.iso)).toList()
      ..sort(
        (a, b) => (a.bounds.width * a.bounds.height).compareTo(
          b.bounds.width * b.bounds.height,
        ),
      );
    for (final c in sorted) {
      for (final shift in [-360.0, 0.0, 360.0]) {
        final p = point - Offset(shift, 0);
        if (c.path.contains(p) ||
            (c.bounds.longestSide < tolerance * 2 &&
                (p - c.anchor).distance <= tolerance)) {
          return c.iso;
        }
      }
    }
    return null;
  }
}
