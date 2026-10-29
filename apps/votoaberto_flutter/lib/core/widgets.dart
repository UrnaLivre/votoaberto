import 'package:flutter/material.dart';
import '../app/strings.dart';

class DemoBanner extends StatelessWidget {
  const DemoBanner({super.key});
  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Semantics(
      container: true,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        color: colors.tertiaryContainer,
        child: Text(
          AppStrings.demo,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: colors.onTertiaryContainer,
            fontWeight: FontWeight.w700,
            letterSpacing: 1,
          ),
        ),
      ),
    );
  }
}

class StatusMessage extends StatelessWidget {
  const StatusMessage({
    super.key,
    required this.message,
    this.onRetry,
    this.loading = false,
  });
  final String message;
  final VoidCallback? onRetry;
  final bool loading;
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (loading)
            const CircularProgressIndicator()
          else
            Icon(
              onRetry == null ? Icons.inbox_outlined : Icons.cloud_off_outlined,
              size: 36,
            ),
          const SizedBox(height: 16),
          Text(message, textAlign: TextAlign.center),
          if (onRetry != null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: FilledButton(
                onPressed: onRetry,
                child: const Text('Tentar novamente'),
              ),
            ),
        ],
      ),
    ),
  );
}

Future<void> showMethodology(BuildContext context) => showDialog<void>(
  context: context,
  builder: (context) => AlertDialog(
    title: const Text(AppStrings.methodology),
    content: const SizedBox(
      width: 580,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              AppStrings.demo,
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            SelectableText(AppStrings.methodologyBody),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => showLicensePage(
          context: context,
          applicationName: AppStrings.title,
          applicationVersion: '0.1.0',
        ),
        child: const Text('Licenças de software'),
      ),
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Entendi'),
      ),
    ],
  ),
);
