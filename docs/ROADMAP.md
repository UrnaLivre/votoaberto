# Roadmap do VotoAberto

O roteiro abaixo é **planejamento**, não promessa de prazo nem declaração de recursos existentes.

## M0 — Fundação pública

- [x] README e escopo inicial
- [x] Compromissos de neutralidade, transparência e distinção entre produtos UrnaLivre
- [x] Proposta de arquitetura, política de dados e contribuição
- [ ] Identidade visual oficial do VotoAberto; direitos e fontes dos materiais

## M1 — Primeira experiência de produto (entregue)

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

## M2 — Data Engine compartilhado e VotoAberto Auditor (próximo marco)

**M2.1 — Descoberta e integridade**

- [ ] Estrutura `pipelines/tse_importer/` reutilizável e `apps/votoaberto_auditor/` como CLI Windows/Linux
- [ ] Inventário local dos ZIPs de 2026, de seus membros e formatos; origem, tamanho, datas, SHA-256 e hashes oficiais de referência quando disponíveis
- [ ] Inspeção amostral/streaming de schemas reais, codificações e casos excepcionais com limites seguros; relatório reproduzível, sem extração em massa
- [ ] Fixtures sintéticos representativos, testes de arquivo malformado e documentação do que ainda não é suportado

**M2.2 — Extração e base pública**

- [ ] Importador configurável por cargo/turno/território/perfil, com padrão **presidente, dois turnos, perfil público compacto**
- [ ] Parsers para formatos oficialmente identificados; versões, erros e chaves compostas tratados explicitamente
- [ ] Geração de **SQLite público versionado** com votos presidenciais por seção, agregações válidas, manifesto/hash e relatório
- [ ] Boletins de urna tratados como **fontes de conferência** e investigação no Auditor, **sem copiar BUs integrais** para o dataset público
- [ ] Importação idempotente/incremental, staging e validação antes de publicação

**M2.3 — Reconciliação e dimensionamento**

- [ ] Reconciliar fontes por turno/UF/município/zona/seção, documentando divergências e cobertura; considerar exterior ZZ sem tratá-lo como UF
- [ ] Testar com arquivos locais oficiais, medir tempo/espaço/latência e decidir forma de distribuição para o Flutter
- [ ] Registrar formatos e filtros por cargo implementados; não afirmar suporte a outros cargos antes de validação

**Critério M2:** motor funcional e testado, dataset público presidencial reproduzível (ou lacunas claramente documentadas), sem dados fictícios apresentados como reais. A API e a conexão Flutter podem iniciar em um marco posterior.

Detalhes em [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md) e [ADR 0003](adr/0003-public-data-and-auditor.md).

## M3 — Dados reais no VotoAberto público e aprofundamento do Auditor

- [ ] Definir API/backend ou distribuição compacta com base nas medições do M2 e conectar o `ElectionRepository` real ao Flutter
- [ ] Navegação por município, zona e seção, comparações entre turnos e cobertura ZZ quando adequada à interface
- [ ] Referências aos BUs originais e resultados presidenciais extraídos, **sem armazenar boletins completos na base pública**
- [ ] Expandir consultas e relatórios analíticos do Auditor sobre os arquivos completos
- [ ] Exportação, metadados de origem, tratamento de divergências e documentação da reprodução independente

## M4 — Análises públicas e distribuição

- [ ] Gráficos exploratórios com cálculos testados e contexto explicativo
- [ ] Web e Android validados e publicados, distribuição Windows
- [ ] Testes de acessibilidade, desempenho e segurança
- [ ] Guia de leitura crítica: correlações, vieses, inferências e limites
- [ ] Política de revisão, correção e versionamento dos dados publicados

## Fora do escopo inicial

Sistema de coleta de votos, criptografia homomórfica, autenticação de eleitores, previsão eleitoral e certificação de integridade do processo. Outros cargos/anos ficam fora do **recorte público inicial**, mas o importador será arquitetado para admiti-los no futuro. Pesquisas futuras do UrnaLivre sobre votação verificável serão separadas deste aplicativo.
