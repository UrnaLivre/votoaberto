import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../domain/brazil_geometry.dart';
import '../domain/world_geometry.dart';

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
  String? _keyboard;
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
        setState(
          () => _keyboard = choices[(index + delta) % choices.length].iso,
        );
      }
    } else {
      return KeyEventResult.ignored;
    }
    return KeyEventResult.handled;
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final name = widget.geometry.countries
        .where((c) => c.iso == (_focused ? _keyboard : _hovered))
        .firstOrNull
        ?.name;
    return Focus(
      onKeyEvent: _key,
      onFocusChange: (value) => setState(() => _focused = value),
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, _) => LayoutBuilder(
          builder: (context, constraints) {
            final viewport = MapViewport(_view, constraints.biggest);
            String? hit(Offset p) => widget.geometry.hitTest(
              viewport.toWorld(p),
              widget.active,
              tolerance: 7 / viewport.scale,
            );
            return DecoratedBox(
              decoration: BoxDecoration(
                color: colors.surfaceContainerLow,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: _focused ? colors.primary : colors.outlineVariant,
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
                                focused: _focused ? _keyboard : _hovered,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    Positioned(
                      top: 12,
                      left: 16,
                      right: 16,
                      child: IgnorePointer(
                        child: Text(
                          name ?? 'Países coloridos têm votação neste turno',
                        ),
                      ),
                    ),
                    Positioned(
                      bottom: 12,
                      left: 12,
                      child: FilledButton.tonalIcon(
                        key: const ValueKey('world-map-reset'),
                        onPressed: widget.onReset,
                        icon: const Icon(Icons.public),
                        label: const Text('Mundo'),
                      ),
                    ),
                    Positioned(
                      bottom: 18,
                      right: 12,
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
  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.clipRect(Offset.zero & size);
    final origin = viewport.toScreen(Offset.zero);
    canvas.translate(origin.dx, origin.dy);
    canvas.scale(viewport.scale);
    for (final country in geometry.countries) {
      final enabled = active.contains(country.iso);
      for (final shift in [-360.0, 0.0, 360.0]) {
        final delta = Offset(shift, 0);
        if (!country.bounds.shift(delta).overlaps(viewport.world)) continue;
        final path = country.path.shift(delta);
        final fill = enabled
            ? country.iso == selected
                  ? colors.primary
                  : colors.tertiary
            : colors.outlineVariant;
        canvas.drawPath(path, Paint()..color = fill);
        canvas.drawPath(
          path,
          Paint()
            ..color = country.iso == focused ? colors.onSurface : colors.surface
            ..style = PaintingStyle.stroke
            ..strokeWidth =
                (country.iso == focused ? 2.4 : .7) / viewport.scale,
        );
        // Keep small islands/countries discoverable at the global scale.
        if (enabled && country.bounds.longestSide * viewport.scale < 8) {
          canvas.drawCircle(
            country.anchor + delta,
            3.5 / viewport.scale,
            Paint()..color = fill,
          );
        }
      }
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
