import 'package:flutter/material.dart';

/// Identical framing action on both maps. Route selection owns visibility;
/// outgoing content cannot receive pointer, keyboard or semantics actions.
class MapResetButton extends StatelessWidget {
  const MapResetButton({
    super.key,
    required this.visible,
    required this.onPressed,
    required this.buttonKey,
  });
  final bool visible;
  final VoidCallback onPressed;
  final Key buttonKey;

  @override
  Widget build(BuildContext context) => IgnorePointer(
    ignoring: !visible,
    child: ExcludeFocus(
      excluding: !visible,
      child: ExcludeSemantics(
        excluding: !visible,
        child: AnimatedSwitcher(
          duration: MediaQuery.disableAnimationsOf(context)
              ? Duration.zero
              : const Duration(milliseconds: 220),
          switchInCurve: Curves.easeInOut,
          switchOutCurve: Curves.easeInOut,
          child: visible
              ? FilledButton.tonalIcon(
                  key: buttonKey,
                  onPressed: onPressed,
                  icon: const Icon(Icons.zoom_out_map, size: 18),
                  label: const Text('Ver mapa inteiro'),
                )
              : const SizedBox.shrink(),
        ),
      ),
    ),
  );
}

class MapCaption extends StatelessWidget {
  const MapCaption(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) => Positioned(
    top: 14,
    left: 16,
    right: 16,
    child: IgnorePointer(
      child: Text(text, style: Theme.of(context).textTheme.labelMedium),
    ),
  );
}

/// The existing Brazilian state fill, shared without changing its colors.
Color mapRegionFill(ColorScheme colors, int index) => Color.lerp(
  colors.surfaceContainerHighest,
  colors.primaryContainer,
  .3 + (index % 4) * .1,
)!;
