# Roadmap do VotoAberto

O roteiro abaixo é **planejamento**, não promessa de prazo nem declaração de recursos existentes.

## M0 — Fundação pública

- [x] README e escopo inicial
- [x] Compromissos de neutralidade, transparência e distinção entre produtos UrnaLivre
- [x] Proposta de arquitetura, política de dados e contribuição
- [ ] Identidade visual oficial do VotoAberto; direitos e fontes dos materiais

## M1 — Primeira experiência de produto (prioridade atual)

- [ ] Projeto Flutter executável no Windows, com suporte planejado a Web e Android
- [ ] Mapa do Brasil com **27 UFs selecionáveis** e zoom/destaque/reversão
- [ ] Tela nacional com painel lateral, pesquisa de UF e identidade visual consistente
- [ ] Tela estadual com comparação 1º/2º turno usando **somente dados fictícios claramente marcados**
- [ ] Hierarquia de navegação futura: município → zona → seção → boletim (sem inventar dados reais)
- [ ] Layout responsivo desktop/mobile, estados de vazio/erro/carregamento
- [ ] Separação `ElectionRepository` mock/API; modelos e testes essenciais
- [ ] Documentação de execução, limitações, testes e decisões de biblioteca de mapas

**Critério M1:** mapa realmente clicável, seleção correta de UFs, interação coerente, execução local e resultados demonstrativos transparentes. Não aceitar telas estáticas disfarçadas de interativas.

## M2 — Ingestão e verificação das fontes TSE

- [ ] Inventário dos ZIPs de 2026, origem, metadados e SHA-256
- [ ] Inspeção de schema real, codificações e casos excepcionais
- [ ] Normalização presidencial dos dois turnos e exterior, quando aplicável
- [ ] Testes de reconciliação com resultados oficiais e relatório de cobertura
- [ ] Banco/índices e implementação da API real

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
