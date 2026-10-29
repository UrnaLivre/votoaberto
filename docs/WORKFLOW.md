# Fluxo de branches e revisão

## Política de branches do repositório central

O repositório `UrnaLivre/votoaberto` mantém **no máximo duas branches remotas** simultaneamente:

1. `main`: branch estável e integradora.
2. **Uma única branch ativa de trabalho** (por exemplo, `feat/m1-interactive-explorer`, `fix/...`, `docs/...`).

Esta política se aplica ao **repositório central**, não às branches existentes nos forks de colaboradores externos. Branches temporárias adicionais não devem ser criadas no repositório central enquanto a branch ativa anterior ainda existir.

## Ciclo de uma entrega

1. Atualizar a `main`, conferir que não há branch de trabalho abandonada e criar **uma** branch a partir da versão atual.
2. Desenvolver com commits pequenos e reversíveis; evitar secrets, binários compilados e dados eleitorais brutos.
3. Abrir PR `branch -> main` com escopo, resultados de testes, fontes/licenças, capturas quando UX e pendências conhecidas.
4. Verificar revisão, testes automáticos e builds relevantes. Não fazer merge com CI vermelho, conflitos ou bloqueios relevantes não resolvidos.
5. Fazer merge **sem force push**, preservando a rastreabilidade do histórico no GitHub.
6. **Depois de confirmar o merge**, excluir a branch remota já concluída e remover a cópia local; verificar novamente que restou somente `main`.
7. Só então criar a próxima branch de trabalho.

A prática de squash ou merge commit pode ser escolhida caso a caso, mas o histórico resultante deve deixar claro o que foi entregue e o PR deve permanecer acessível para auditoria do processo.

## Contribuições simultâneas

Enquanto já existir uma branch ativa no repositório central, colaboradores externos devem preferir branches **em forks próprios** e PRs direcionados à `main`; o mantenedor integra sequencialmente, após revisão. Não criar diversas branches remotas centrais para lidar com tarefas paralelas.

Mudanças urgentes devem ser combinadas com o responsável pela branch ativa ou esperar seu encerramento. Exceções à política exigem justificativa e prazo de limpeza registrados em issue/PR.

## Segurança e disciplina

- Nunca excluir a branch ativa **antes de** confirmar a integração e a disponibilidade dos commits na `main`.
- Não apagar `main`; não reescrever seu histórico.
- Não tratar teste local como substituto para CI quando o workflow puder ser executado.
- A exclusão de uma branch concluída não apaga os commits alcançáveis pela `main` nem o histórico de discussão do PR.
- Documentar qualquer limitação conhecida antes do merge; features pendentes ficam explícitas no roadmap.

## Conferência rápida

```bash
git fetch --prune origin
git branch -r
git status
```

Após merge e confirmação, excluir a branch **remota** pela interface GitHub (botão `Delete branch` no PR concluído) ou, se autorizado e disponível, com `git push origin --delete nome-da-branch`. Para a cópia local já integrada: `git switch main && git pull --ff-only && git branch -d nome-da-branch`.

A regra de duas branches evita acúmulo operacional, mas não substitui revisão de código, CI nem gerenciamento responsável de mudanças.
