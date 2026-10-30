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

## M2 — Data Engine compartilhado e VotoAberto Auditor (integrado pelo PR #2)

**M2.1 — Descoberta e integridade**

- [x] Estrutura `pipelines/tse_importer/` reutilizável e `apps/votoaberto_auditor/` como CLI Windows/Linux
- [x] Inventário local dos ZIPs de 2026, de seus membros e formatos; origem, tamanho, datas, SHA-256 e hashes oficiais de referência quando disponíveis
- [x] Inspeção amostral/streaming de schemas reais, codificações e casos excepcionais com limites seguros; relatório reproduzível, sem extração em massa
- [x] Fixtures sintéticos representativos, testes de arquivo malformado e documentação do que ainda não é suportado

**M2.2 — Extração e base pública**

- [x] Importador configurável por cargo/turno/território/perfil, com padrão **presidente, dois turnos, perfil público compacto**
- [x] Parsers para formatos oficialmente identificados; versões, erros e chaves compostas tratados explicitamente
- [x] Geração de **SQLite público versionado** com votos presidenciais por seção, agregações válidas, manifesto/hash e relatório
- [x] Boletins de urna tratados como **fontes de conferência** e investigação no Auditor, **sem copiar BUs integrais** para o dataset público
- [x] Importação idempotente/incremental, staging e validação antes de publicação

**M2.3 — Reconciliação e dimensionamento**

- [x] Reconciliar fontes presidenciais dos dois turnos de SC por município/zona/seção; ZZ identificado no CSV e coberto por fixtures, sem alegar conferência nacional
- [x] Testar com os três ZIPs locais oficiais e medir processamento/espaço de SC
- [x] Expandir conferência real para os arquivos fornecidos de todas as UFs/ZZ, documentada no M3.1
- [ ] Ampliar formatos excepcionais suportados e decidir distribuição/latência Flutter
- [x] Registrar formatos e filtros por cargo implementados; não afirmar suporte a outros cargos antes de validação

**Critério M2:** motor funcional e testado, dataset público presidencial reproduzível (ou lacunas claramente documentadas), sem dados fictícios apresentados como reais. A API e a conexão Flutter podem iniciar em um marco posterior.

Detalhes em [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md) e [ADR 0003](adr/0003-public-data-and-auditor.md).

## M3 — Dados reais no VotoAberto público e aprofundamento do Auditor

- [x] Definir distribuição compacta e conectar repositório real ao Flutter — M4, JSON embarcado em prévia local
- [x] Navegação municipal, comparações e ZZ — M4
- [ ] Navegação por zona/seção através de futura API
- [ ] Referências aos BUs originais e resultados presidenciais extraídos, **sem armazenar boletins completos na base pública**
- [ ] Expandir consultas e relatórios analíticos do Auditor sobre os arquivos completos
- [ ] Exportação, metadados de origem, tratamento de divergências e documentação da reprodução independente

### M3.1 — Primeira importação nacional local

- [x] Orçamento de disco, reserva livre, registro de propriedade e limpeza de artefatos próprios
- [x] Consolidação sequencial por UF/turno e relatórios de reconciliação limitados
- [x] Inventário nacional local, piloto AC/2º turno e leitura real dos BWEBs de ZZ
- [x] Concluir carga nacional local com os 56 pares e 5.731.614 resultados presidenciais reconciliados
- [x] Validar SQLite, matemática, referências e regressão SC; medir disco/memória e eliminar intermediários próprios
- [ ] Revisar distribuição e política pública após conferir integralmente os dados

[Operação](NATIONAL_IMPORT.md) e [evidências e limites](TSE_2026_NATIONAL_INVESTIGATION.md).
A base é elegível localmente, com `public_readiness: not_ready`; a presença dos
56 pares não comprova completude de todas as seções.

## M4 — MVP municipal offline (validação local)

- [x] Exportar release SQLite somente leitura para JSON compacto com catálogo por turno
- [x] Validar municípios/UFs/Brasil/doméstico/ZZ por SQL independente e hashes
- [x] Integrar assets, cache limitado e navegação Brasil → UF → município
- [x] Preservar mock, mapa, temas, URLs e testes; buscas sem acento e por teclado
- [x] Separar builds fixture/demo/real e impedir fallback fictício no modo real
- [x] Executar exportação real e teste Windows com HTTP da aplicação bloqueado
- [x] Compilar Web, Windows e APK debug localmente com os JSONs reais
- [ ] Validar em dispositivo Android físico e acessibilidade com usuários
- [ ] Autenticação/proveniência completa e revisão da prontidão pública da base
- [ ] PWA offline entre sessões e política de atualização de cache

[Contrato e operação](EMBEDDED_DATA_MVP.md), [relatório e limites](M4_COMPLETION_REPORT.md).
Assets reais ficam fora do Git; `not_ready` continua bloqueando publicação pública.

## Etapas posteriores — Análises públicas e distribuição

- [ ] Gráficos exploratórios com cálculos testados e contexto explicativo
- [ ] Web e Android validados e publicados, distribuição Windows
- [ ] Testes de acessibilidade, desempenho e segurança
- [ ] Guia de leitura crítica: correlações, vieses, inferências e limites
- [ ] Política de revisão, correção e versionamento dos dados publicados

## Fora do escopo inicial

Sistema de coleta de votos, criptografia homomórfica, autenticação de eleitores, previsão eleitoral e certificação de integridade do processo. Outros cargos/anos ficam fora do **recorte público inicial**, mas o importador será arquitetado para admiti-los no futuro. Pesquisas futuras do UrnaLivre sobre votação verificável serão separadas deste aplicativo.

Evidências M2: [investigação de SC](TSE_2026_FORMAT_INVESTIGATION.md),
[operação](DATA_ENGINE_OPERATIONS.md) e relatório de consolidação da revisão.
