# ADR 0002 — Estado, contratos de dados e navegação

Estado: aceito. Data: 2026-10-29.

## Decisão

Usar `ChangeNotifier` / `ListenableBuilder`, parte do Flutter, para o pequeno
estado compartilhado do M1. Riverpod é uma alternativa válida para mais
dependências e consultas, mas não traz benefício proporcional para um único
dataset imutável e um explorador neste marco.

`go_router` representa `/` e `/uf/SP?turno=2&visao=comparison`. UF, turno e
visão vêm da URL; o controller reflete essa navegação sem emitir notificações
durante o parse inicial (a própria rota reconstrói a Page). Uma identidade de
Page estável preserva a câmera entre Brasil e UF. Tema permanece na sessão.
Retornar ao Brasil mantém turno e visão. Novas seleções não fazem requests:
o dataset é carregado uma vez. Retry de carga usa geração de request para
ignorar respostas antigas e não notificar após dispose.

O contrato `ElectionRepository.load(Election)` retorna modelos tipados e
proveniência. `MockElectionRepository` é a implementação funcional.
`ApiElectionRepository` é uma **classe abstrata**, com URI base: não simula HTTP
nem retorna mock disfarçado. A seleção da implementação fica em `main.dart`.
O M1 recusa dataset sem marca sintética para impedir remoção acidental do aviso.

Município, zona, seção, referência a BU e chave composta existem como tipos,
sem registros fabricados. Códigos são strings; município TSE não é código IBGE;
ZZ é abrangência eleitoral futura. Campos adicionais preservam discriminadores
que os arquivos reais vierem a exigir. Não há entidade de urna física inferida
de seção/BU. As rotas granulares serão adicionadas com cobertura efetiva no M3;
endereços não implementados mostram indisponibilidade explícita.

## Mock e cálculos

`mock-v1` usa índice alfabético da enumeração fixa de UFs, aritmética inteira e
mesmo eleitorado apto em ambos os turnos. Não reproduz população nem resultado
real. A soma dos candidatos é válida; comparecimento é válidos + brancos + nulos;
abstenção é aptos − comparecimento. Brasil é soma das 27 UFs, sem exterior.
Taxas dividem por aptos; candidatos dividem por válidos. Variação relativa usa
o 1º turno como base e é indefinida para base zero. Candidato ausente do 2º turno
é exibido como não participante, sem uma falsa variação de −100%.

## Troca por API

Implementar a classe abstrata com transporte/decodificação, adaptar o DTO ao
domínio, adicionar testes de contrato e validar cobertura/proveniência. Injetar
a implementação no composition root. A liberação de dados reais também exigirá
substituir explicitamente o bloqueio sintético e a sinalização global, após a
revisão metodológica do M2. Não basta ocultar um badge.

## Limitações conscientes

Tema não persiste entre execuções. Sem cache persistente, autenticação ou
requisições por UF. Strings compartilhadas ficam em `app/strings.dart`, locale
pt-BR e Flutter localizations/intl; migração completa das demais strings a ARB
fica para a inclusão do segundo idioma. Estado de zoom é apresentação efêmera.
