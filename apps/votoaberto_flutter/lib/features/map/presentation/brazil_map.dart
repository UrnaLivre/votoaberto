import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../elections/domain/geography.dart';
import '../domain/brazil_geometry.dart';
import '../domain/geographic_catalog.dart';
import 'map_controls.dart';

class BrazilMap extends StatefulWidget {
  const BrazilMap({
    super.key,
    required this.geometry,
    required this.selected,
    required this.onSelect,
    required this.onReset,
    this.location,
    this.locationName,
  });
  final BrazilGeometry geometry;
  final BrazilianState? selected;
  final ValueChanged<BrazilianState> onSelect;
  final VoidCallback onReset;
  final MunicipalLocation? location;
  final String? locationName;

  @override
  State<BrazilMap> createState() => _BrazilMapState();
}

class _BrazilMapState extends State<BrazilMap>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animation = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 540),
  );
  Rect _target() {
    final view = widget.geometry.viewFor(widget.selected);
    final point = widget.location?.point;
    return point == null || view.contains(point)
        ? view
        : view.expandToInclude(Rect.fromCircle(center: point, radius: .6));
  }

  late Rect _from = _target();
  late Rect _to = _from;
  BrazilianState? _hovered;
  BrazilianState _keyboard = BrazilianState.ac;
  bool _focused = false;
  Rect get _view =>
      Rect.lerp(_from, _to, Curves.easeInOutCubic.transform(_animation.value))!;

  @override
  void didUpdateWidget(covariant BrazilMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selected != widget.selected ||
        oldWidget.location != widget.location ||
        oldWidget.geometry != widget.geometry) {
      final current = _view;
      _animation.stop();
      _from = current;
      _to = _target();
      _hovered = null;
      if (widget.selected != null) _keyboard = widget.selected!;
      if (MediaQuery.disableAnimationsOf(context)) {
        _animation.value = 1;
      } else {
        _animation.forward(from: 0);
      }
    }
  }

  @override
  void dispose() {
    _animation.dispose();
    super.dispose();
  }

  KeyEventResult _key(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;
    final key = event.logicalKey;
    if (key == LogicalKeyboardKey.escape || key == LogicalKeyboardKey.home) {
      widget.onReset();
    } else if (key == LogicalKeyboardKey.enter ||
        key == LogicalKeyboardKey.space) {
      widget.onSelect(_keyboard);
    } else if ([
      LogicalKeyboardKey.arrowLeft,
      LogicalKeyboardKey.arrowUp,
      LogicalKeyboardKey.arrowRight,
      LogicalKeyboardKey.arrowDown,
    ].contains(key)) {
      final backwards =
          key == LogicalKeyboardKey.arrowLeft ||
          key == LogicalKeyboardKey.arrowUp;
      setState(
        () => _keyboard = BrazilianState
            .values[(_keyboard.index + (backwards ? 26 : 1)) % 27],
      );
    } else {
      return KeyEventResult.ignored;
    }
    return KeyEventResult.handled;
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Focus(
      onFocusChange: (value) => setState(() => _focused = value),
      onKeyEvent: _key,
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, _) => LayoutBuilder(
          builder: (context, constraints) {
            final viewport = MapViewport(_view, constraints.biggest);
            BrazilianState? hit(Offset local) =>
                widget.geometry.hitTest(viewport.toWorld(local));
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
                            final state = hit(e.localPosition);
                            if (state != null) widget.onSelect(state);
                          },
                          child: Semantics(
                            label:
                                'Mapa do Brasil. ${widget.selected?.name ?? 'Visão nacional'}. '
                                'Setas percorrem UFs, Enter seleciona, Escape retorna ao Brasil. '
                                'A busca e a lista oferecem as mesmas 27 UFs para leitores de tela.',
                            child: CustomPaint(
                              key: const ValueKey('brazil-map-paint'),
                              painter: BrazilMapPainter(
                                geometry: widget.geometry,
                                viewport: viewport,
                                colors: colors,
                                selected: widget.selected,
                                hovered: _hovered,
                                focused: _focused ? _keyboard : null,
                                onSelect: widget.onSelect,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    if (widget.location != null)
                      Positioned(
                        left: viewport.toScreen(widget.location!.point).dx - 14,
                        top: viewport.toScreen(widget.location!.point).dy - 28,
                        child: IgnorePointer(
                          child: Semantics(
                            label:
                                '${widget.locationName}. ${widget.location!.kind == 'seat' ? 'Sede municipal' : 'Ponto representativo'}. Não indica urna ou local de votação.',
                            child: Icon(
                              Icons.location_on,
                              key: const ValueKey('municipal-marker'),
                              size: 28,
                              color: colors.error,
                              shadows: [
                                Shadow(color: colors.surface, blurRadius: 3),
                              ],
                            ),
                          ),
                        ),
                      ),
                    MapCaption(
                      _focused
                          ? '${_keyboard.name} · Enter para selecionar'
                          : _hovered?.name ?? 'Selecione um estado no mapa',
                    ),
                    Positioned(
                      bottom: 12,
                      left: 12,
                      child: MapResetButton(
                        visible: widget.selected != null,
                        buttonKey: const ValueKey('map-reset'),
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
                          'IBGE · malha simplificada',
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

class BrazilMapPainter extends CustomPainter {
  BrazilMapPainter({
    required this.geometry,
    required this.viewport,
    required this.colors,
    this.selected,
    this.hovered,
    this.focused,
    required this.onSelect,
  });
  final BrazilGeometry geometry;
  final MapViewport viewport;
  final ColorScheme colors;
  final BrazilianState? selected;
  final BrazilianState? hovered;
  final BrazilianState? focused;
  final ValueChanged<BrazilianState> onSelect;

  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()..color = colors.outlineVariant.withValues(alpha: .45);
    for (var x = 20.0; x < size.width; x += 24) {
      for (var y = 20.0; y < size.height; y += 24) {
        canvas.drawCircle(Offset(x, y), .65, grid);
      }
    }
    canvas.save();
    final origin = viewport.toScreen(Offset.zero);
    canvas.translate(origin.dx, origin.dy);
    canvas.scale(viewport.scale);
    final shapes = [...geometry.states]
      ..sort(
        (a, b) => (a.state == selected ? 1 : 0).compareTo(
          b.state == selected ? 1 : 0,
        ),
      );
    for (final shape in shapes) {
      final active = shape.state == selected;
      final over = shape.state == hovered;
      final focus = shape.state == focused;
      final fill = active
          ? colors.primary
          : over
          ? colors.tertiaryContainer
          : mapRegionFill(colors, shape.state.index);
      canvas.drawPath(shape.path, Paint()..color = fill);
      canvas.drawPath(
        shape.path,
        Paint()
          ..color = focus
              ? colors.tertiary
              : active
              ? colors.onSurface
              : colors.surface
          ..style = PaintingStyle.stroke
          ..strokeJoin = StrokeJoin.round
          ..strokeWidth =
              (focus
                  ? 3
                  : active
                  ? 1.8
                  : 1.1) /
              viewport.scale,
      );
    }
    canvas.restore();
    final occupied = <Rect>[];
    // Selected, keyboard-focused and DF labels have first placement priority.
    final labels = [...geometry.states]
      ..sort((a, b) {
        int priority(StateGeometry s) => s.state == selected
            ? 0
            : s.state == focused
            ? 1
            : s.state == BrazilianState.df
            ? 2
            : 3;
        return priority(a).compareTo(priority(b));
      });
    for (final shape in labels) {
      final point = viewport.toScreen(shape.label);
      final rect = Rect.fromCenter(center: point, width: 25, height: 20);
      if (!(Offset.zero & size).deflate(30).contains(point) ||
          occupied.any((other) => other.overlaps(rect))) {
        continue;
      }
      occupied.add(rect.inflate(2));
      final text = TextPainter(
        text: TextSpan(
          text: shape.state.code,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            color: shape.state == selected
                ? colors.onPrimary
                : colors.onSurface,
          ),
        ),
        textDirection: ui.TextDirection.ltr,
      )..layout();
      text.paint(canvas, point - Offset(text.width / 2, text.height / 2));
    }
  }

  @override
  bool shouldRepaint(covariant BrazilMapPainter oldDelegate) =>
      oldDelegate.viewport.world != viewport.world ||
      oldDelegate.viewport.size != viewport.size ||
      oldDelegate.colors != colors ||
      oldDelegate.selected != selected ||
      oldDelegate.hovered != hovered ||
      oldDelegate.focused != focused ||
      oldDelegate.geometry != geometry;
}
