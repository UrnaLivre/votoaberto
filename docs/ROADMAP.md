# Roadmap do VotoAberto

O roteiro abaixo é **planejamento**, não promessa de prazo nem declaração de recursos existentes.

## M0 — Fundação pública

- [x] README e escopo inicial
- [x] Compromissos de neutralidade, transparência e distinção entre produtos UrnaLivre
- [x] Proposta de arquitetura, política de dados e contribuição
- [ ] Identidade visual oficial do VotoAberto; direitos e fontes dos materiais

## M1 — Primeira experiência de produto (prioridade atual)

- [x] Projeto Flutter executável no Windows e Web, runner Android e CI multiplataforma
- [x] Mapa do Brasil com **27 UFs selecionáveis** e zoom/destaque/reversão
- [x] Tela nacional com painel lateral, pesquisa de UF e identidade visual temporária consistente
- [x] Tela estadual com comparação 1º/2º turno usando **somente dados fictícios claramente marcados**
- [x] Hierarquia futura representada por modelos/chaves e indicação explícita de indisponibilidade; Brasil/UF funcionais
- [x] Layout responsivo desktop/mobile, estados de vazio/erro/carregamento
- [x] Contrato `ElectionRepository`, mock funcional, extensão API abstrata; modelos e testes
- [x] Documentação de execução, limitações, testes e decisões de biblioteca de mapas

Evidências, plataformas efetivamente validadas e pendências de ambiente em
[VALIDATION.md](VALIDATION.md). Consulta granular, dados reais e publicação
continuam fora do M1; identidade oficial ainda depende dos materiais UrnaLivre.

**Critério M1:** mapa realmente clicável, seleção correta de UFs, interação coerente, execução local e resultados demonstrativos transparentes. Não aceitar telas estáticas disfarçadas de interativas.

## M2 — Ingestão e verificação das fontes TSE

- [x] Motor Python compartilhado e Auditor CLI, perfis public/analyst
- [x] Inventário dos três ZIPs fornecidos, origem, SHA-256 e conferência SHA-512 dos BWEBs
- [x] Inspeção de dois schemas reais, Latin-1 e particularidades documentadas
- [x] Importação presidencial de SC nos dois turnos, SQLite compacto e manifesto
- [x] Reconciliação BWEB × votação por seção de SC e testes sintéticos/CI preparado
- [ ] Ampliar importação/conferência reais para todas as UFs e ZZ (presença no CSV nacional confirmada)
- [ ] Implementar situações eleitorais e formatos atualmente não suportados
- [ ] API real e adaptador Flutter

Evidências e medições: [investigação dos formatos reais](TSE_2026_FORMAT_INVESTIGATION.md).

**Critério M2:** resultados reprocessáveis e cobertura explicitamente documentada, sem números inventados.

## M3 — Consulta granular e auditoria de dados

- [ ] Navegação a município, zona e seção
- [ ] Referências a boletins e fonte original, com clareza sobre arquivo versus interpretação
- [ ] Consulta e comparação por turno com manejo de seções agregadas/alteradas
- [ ] Exportação, metadados de origem, tratamento de divergências
- [ ] Documentação independente do pipeline de reprodução

## M4 — Análises públicas e distribuição

- [ ] Gráficos exploratórios com cálculos testados e contexto explicativo
- [ ] Web e Android validados e publicados, distribuição Windows
- [ ] Testes de acessibilidade, desempenho e segurança
- [ ] Guia de leitura crítica: correlações, vieses, inferências e limites
- [ ] Política de revisão, correção e versionamento dos dados publicados

## Fora do escopo inicial

Sistema de coleta de votos, criptografia homomórfica, autenticação de eleitores, previsão eleitoral, certificação de integridade do processo e outros cargos/anos. Pesquisas futuras do UrnaLivre sobre votação verificável serão separadas deste aplicativo.
