import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/widgets.dart';
import '../../elections/domain/election.dart';
import 'explorer_controller.dart';
import 'overseas_special_case.dart';
import 'round_summary.dart';

const specialCasesTitle = 'Casos especiais — Votação no exterior';

class OverseasSpecialCasesDialog extends StatelessWidget {
  const OverseasSpecialCasesDialog({
    super.key,
    required this.controller,
    required this.cases,
  });
  final ExplorerController controller;
  final List<OverseasSpecialCase> cases;

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.sizeOf(context);
    final inset = size.width < 600 ? 12.0 : 24.0;
    final reduced = MediaQuery.disableAnimationsOf(context);
    return DefaultTabController(
      length: cases.length,
      animationDuration: reduced ? Duration.zero : kTabScrollDuration,
      child: Builder(
        builder: (context) {
          final tabs = DefaultTabController.of(context);
          void changeTab(int direction) => tabs.animateTo(
            (tabs.index + direction) % cases.length,
            duration: reduced ? Duration.zero : kTabScrollDuration,
          );
          return CallbackShortcuts(
            bindings: {
              const SingleActivator(LogicalKeyboardKey.escape): () =>
                  Navigator.pop(context),
            },
            child: Dialog(
              insetPadding: EdgeInsets.all(inset),
              constraints: BoxConstraints(
                maxWidth: 760,
                maxHeight: math.max(0, math.min(800, size.height - inset * 2)),
              ),
              child: Semantics(
                key: const ValueKey('special-cases-surface'),
                container: true,
                scopesRoute: true,
                explicitChildNodes: true,
                namesRoute: true,
                label: specialCasesTitle,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(24, 16, 12, 8),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              specialCasesTitle,
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                          ),
                          IconButton(
                            key: const ValueKey('special-cases-close'),
                            tooltip: 'Fechar casos especiais',
                            onPressed: () => Navigator.pop(context),
                            icon: const Icon(Icons.close),
                          ),
                        ],
                      ),
                    ),
                    CallbackShortcuts(
                      bindings: {
                        const SingleActivator(
                          LogicalKeyboardKey.arrowRight,
                        ): () =>
                            changeTab(1),
                        const SingleActivator(
                          LogicalKeyboardKey.arrowLeft,
                        ): () =>
                            changeTab(-1),
                      },
                      child: TabBar(
                        tabs: [
                          for (final entry in cases)
                            Tab(
                              key: ValueKey('special-tab-${entry.code}'),
                              text: entry.title,
                            ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: ListenableBuilder(
                        listenable: controller,
                        builder: (context, _) => TabBarView(
                          children: [
                            for (final entry in cases)
                              _CaseContent(
                                controller: controller,
                                entry: entry,
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _CaseContent extends StatelessWidget {
  const _CaseContent({required this.controller, required this.entry});
  final ExplorerController controller;
  final OverseasSpecialCase entry;

  @override
  Widget build(BuildContext context) {
    final locality = controller.municipalities
        .where((loc) => loc.municipality.code == entry.code)
        .firstOrNull;
    return SingleChildScrollView(
      key: PageStorageKey('special-scroll-${entry.code}'),
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Semantics(
            header: true,
            child: Text(
              entry.title,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Localidade eleitoral TSE ${entry.code}',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 16),
          Text(entry.explanation),
          const SizedBox(height: 12),
          Text(entry.note, style: Theme.of(context).textTheme.bodySmall),
          if (controller.synthetic) ...[
            const SizedBox(height: 12),
            const Text(
              'DEMONSTRAÇÃO · resultados fictícios',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
          ],
          const SizedBox(height: 24),
          if (controller.municipalStatus == LoadStatus.loading)
            const StatusMessage(
              message: 'Carregando resultados locais…',
              loading: true,
            )
          else if (controller.municipalStatus == LoadStatus.error)
            StatusMessage(
              message:
                  'Não foi possível carregar os resultados desta localidade.',
              onRetry: controller.loadMunicipalities,
            )
          else if (!controller.abroad ||
              locality == null ||
              !controller.specialCases.contains(entry))
            const StatusMessage(
              message: 'Localidade ausente ou indisponível neste conjunto consultado.',
            )
          else ...[
            for (final round in ElectionRound.values) ...[
              Semantics(
                header: true,
                child: Text(
                  'Resultados — ${round == ElectionRound.first ? '1º' : '2º'} turno',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              const SizedBox(height: 16),
              if (locality.rounds[round] case final result?)
                RoundSummary(
                  key: ValueKey('special-result-${entry.code}-${round.name}'),
                  result: result,
                  synthetic: controller.synthetic,
                )
              else
                Text(
                  'Não há registro de resultados desta localidade para o ${round == ElectionRound.first ? '1º' : '2º'} turno na base consultada.',
                ),
              const SizedBox(height: 24),
            ],
            Text(
              'Estes resultados já integram os totais do exterior e do Brasil. A consulta nesta janela não acrescenta votos aos agregados.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ],
      ),
    );
  }
}
