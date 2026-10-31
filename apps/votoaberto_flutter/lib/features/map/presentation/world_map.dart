import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../domain/brazil_geometry.dart';
import '../domain/world_geometry.dart';
import 'map_controls.dart';

class WorldMap extends StatefulWidget {
  const WorldMap({
    super.key,
    required this.geometry,
    required this.active,
    required this.selected,
    required this.onSelect,
    required this.onReset,
  });
  final WorldGeometry geometry;
  final Set<String> active;
  final String? selected;
  final ValueChanged<String> onSelect;
  final VoidCallback onReset;
  @override
  State<WorldMap> createState() => _WorldMapState();
}

class _WorldMapState extends State<WorldMap>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animation = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 540),
  );
  late Rect _from = widget.geometry.viewFor(widget.selected);
  late Rect _to = _from;
  String? _hovered;
  late String? _keyboard = widget.selected ?? _choices.firstOrNull?.iso;
  bool _focused = false;
  Rect get _view =>
      Rect.lerp(_from, _to, Curves.easeInOutCubic.transform(_animation.value))!;
  List<CountryGeometry> get _choices =>
      widget.geometry.countries
          .where((c) => widget.active.contains(c.iso))
          .toList()
        ..sort((a, b) => a.name.compareTo(b.name));
  @override
  void didUpdateWidget(covariant WorldMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.selected != oldWidget.selected ||
        widget.geometry != oldWidget.geometry) {
      _from = _view;
      _animation.stop();
      _to = widget.geometry.viewFor(widget.selected);
      _hovered = null;
      _keyboard = widget.selected;
      if (MediaQuery.disableAnimationsOf(context)) {
        _animation.value = 1;
      } else {
        _animation.forward(from: 0);
      }
    }
    if (!widget.active.contains(_keyboard)) {
      _keyboard = _choices.firstOrNull?.iso;
    }
  }

  @override
  void dispose() {
    _animation.dispose();
    super.dispose();
  }

  KeyEventResult _key(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;
    final choices = _choices;
    final key = event.logicalKey;
    if (key == LogicalKeyboardKey.escape || key == LogicalKeyboardKey.home) {
      widget.onReset();
    } else if (key == LogicalKeyboardKey.enter ||
        key == LogicalKeyboardKey.space) {
      setState(() => _hovered = null);
      final next = widget.active.contains(_keyboard)
          ? _keyboard
          : choices.firstOrNull?.iso;
      if (next != null) widget.onSelect(next);
    } else if ([
      LogicalKeyboardKey.arrowLeft,
      LogicalKeyboardKey.arrowRight,
      LogicalKeyboardKey.arrowUp,
      LogicalKeyboardKey.arrowDown,
    ].contains(key)) {
      if (choices.isNotEmpty) {
        final index = choices.indexWhere((c) => c.iso == _keyboard);
        final delta =
            key == LogicalKeyboardKey.arrowLeft ||
                key == LogicalKeyboardKey.arrowUp
            ? -1
            : 1;
        setState(() {
          _hovered = null;
          _keyboard =
              choices[(index < 0
                      ? (delta < 0 ? choices.length - 1 : 0)
                      : (index + delta) % choices.length)]
                  .iso;
        });
      }
    } else {
      return KeyEventResult.ignored;
    }
    return KeyEventResult.handled;
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final interaction = _hovered ?? (_focused ? _keyboard : null);
    final name = widget.geometry.countries
        .where((c) => c.iso == interaction)
        .firstOrNull
        ?.name;
    return Focus(
      onKeyEvent: _key,
      onFocusChange: (value) => setState(() {
        _focused = value;
        if (value) _hovered = null;
      }),
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, _) => LayoutBuilder(
          builder: (context, constraints) {
            final viewport = MapViewport(_view, constraints.biggest);
            String? hit(Offset p) {
              final point = viewport.toWorld(p);
              if (!WorldGeometry.longitudeWindow(_view).contains(point)) {
                return null;
              }
              return widget.geometry.hitTest(
                point,
                widget.active,
                tolerance: 7 / viewport.scale,
              );
            }

            return DecoratedBox(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: _focused ? colors.primary : Colors.transparent,
                  width: 2,
                ),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: Stack(
                  children: [
                    Positioned.fill(
                      child: MouseRegion(
                        cursor: _hovered == null
                            ? SystemMouseCursors.basic
                            : SystemMouseCursors.click,
                        onHover: (e) {
                          final next = hit(e.localPosition);
                          if (next != _hovered) setState(() => _hovered = next);
                        },
                        onExit: (_) => setState(() => _hovered = null),
                        child: GestureDetector(
                          behavior: HitTestBehavior.opaque,
                          onTapUp: (e) {
                            final iso = hit(e.localPosition);
                            if (iso != null) widget.onSelect(iso);
                          },
                          child: Semantics(
                            label:
                                'Mapa da votação brasileira no exterior. ${widget.active.length} países ou territórios com dados neste turno. Setas percorrem países com dados; Enter seleciona; Escape retorna ao Mundo. A lista de países oferece a mesma seleção.',
                            child: CustomPaint(
                              key: const ValueKey('world-map-paint'),
                              painter: WorldMapPainter(
                                geometry: widget.geometry,
                                viewport: viewport,
                                colors: colors,
                                active: widget.active,
                                selected: widget.selected,
                                focused: interaction,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    MapCaption(name ?? 'Selecione um país'),
                    Positioned(
                      bottom: 12,
                      left: 12,
                      child: MapResetButton(
                        visible: _to != WorldGeometry.bounds,
                        buttonKey: const ValueKey('world-map-reset'),
                        onPressed: widget.onReset,
                      ),
                    ),
                    Positioned(
                      bottom:
                          constraints.maxWidth < 440 && widget.selected != null
                          ? 72
                          : 18,
                      right: 16,
                      child: IgnorePointer(
                        child: Text(
                          'Natural Earth',
                          style: Theme.of(context).textTheme.labelSmall,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class WorldMapPainter extends CustomPainter {
  WorldMapPainter({
    required this.geometry,
    required this.viewport,
    required this.colors,
    required this.active,
    this.selected,
    this.focused,
  });
  final WorldGeometry geometry;
  final MapViewport viewport;
  final ColorScheme colors;
  final Set<String> active;
  final String? selected;
  final String? focused;

  /// Large regions first, small islands last, matching small-first hit testing.
  List<CountryGeometry> get baseOrder => [...geometry.countries]
    ..sort(
      (a, b) => (b.bounds.width * b.bounds.height).compareTo(
        a.bounds.width * a.bounds.height,
      ),
    );

  /// Interaction outlines are a separate final pass, with hover/focus on top.
  List<CountryGeometry> get highlights => [
    for (final iso in {selected, focused})
      if (active.contains(iso))
        ...geometry.countries.where((c) => c.iso == iso),
  ];

  Color fillFor(CountryGeometry country) {
    if (!active.contains(country.iso)) return colors.outlineVariant;
    if (country.iso == selected) return colors.primary;
    if (country.iso == focused) return colors.primaryContainer;
    return mapRegionFill(colors, geometry.countries.indexOf(country));
  }

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.clipRect(Offset.zero & size);
    final origin = viewport.toScreen(Offset.zero);
    canvas.translate(origin.dx, origin.dy);
    canvas.scale(viewport.scale);
    // A single longitude window also clips letterboxing. Periodic copies only
    // supply the two halves of seam-crossing countries; no repeated world.
    final window = WorldGeometry.longitudeWindow(viewport.world);
    canvas.clipRect(window);
    final visible = Rect.fromPoints(
      viewport.toWorld(Offset.zero),
      viewport.toWorld(size.bottomRight(Offset.zero)),
    ).intersect(window);
    void draw(CountryGeometry country, {bool highlight = false}) {
      for (final delta in WorldGeometry.copiesIn(country, visible)) {
        final path = country.path.shift(delta);
        if (!highlight) {
          canvas.drawPath(path, Paint()..color = fillFor(country));
        }
        canvas.drawPath(
          path,
          Paint()
            ..color = highlight ? colors.onSurface : colors.surface
            ..style = PaintingStyle.stroke
            ..strokeWidth = (highlight ? 2.4 : .7) / viewport.scale,
        );
        if (active.contains(country.iso) &&
            country.bounds.longestSide * viewport.scale < 8) {
          canvas.drawCircle(
            country.anchor + delta,
            3.5 / viewport.scale,
            Paint()..color = fillFor(country),
          );
          if (highlight) {
            canvas.drawCircle(
              country.anchor + delta,
              3.5 / viewport.scale,
              Paint()
                ..color = colors.onSurface
                ..style = PaintingStyle.stroke
                ..strokeWidth = 2.4 / viewport.scale,
            );
          }
        }
      }
    }

    for (final country in baseOrder) {
      draw(country);
    }
    for (final country in highlights) {
      draw(country, highlight: true);
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant WorldMapPainter old) =>
      old.geometry != geometry ||
      old.viewport.world != viewport.world ||
      old.viewport.size != viewport.size ||
      old.colors != colors ||
      old.selected != selected ||
      old.focused != focused ||
      old.active.length != active.length ||
      !old.active.containsAll(active);
}
