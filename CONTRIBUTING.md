# Como contribuir

Obrigado por considerar contribuir com o **VotoAberto**, projeto open source do ecossistema UrnaLivre.

## Antes de abrir uma contribuição

- Consulte [README.md](README.md), [visão](docs/VISION.md) e [roadmap](docs/ROADMAP.md).
- Abra uma issue para mudanças amplas, dúvidas sobre dados oficiais e decisões de arquitetura relevantes.
- Evite incluir dados brutos de eleição ou datasets volumosos em commits/PRs.
- Preserve a neutralidade político-partidária: argumentos devem se apoiar em fontes, métodos e resultados reprodutíveis.

## Fluxo sugerido

1. Crie uma branch de nome descritivo, por exemplo `feat/state-map` ou `docs/data-lineage`.
2. Implemente mudanças menores e focadas com testes e documentação aplicáveis.
3. Execute formatação, análise estática e testes disponíveis antes do PR.
4. Descreva no PR **o que mudou**, **como testar**, **fontes/licenças** de novos materiais, limitações e capturas (quando UI).
5. Não faça merge de análises de dados sem proveniência e possibilidade de verificação.

## Regras para fontes e números

- Nunca apresente resultados fictícios como oficiais.
- Ao adicionar dados reais no futuro, inclua URL, atribuição, datas, hashes e método de transformação.
- Ao relatar um padrão anômalo, separe **observação**, **hipótese** e **conclusão**; informe alternativas plausíveis.
- Não confunda boletim de urna, seção eleitoral e equipamento físico.
- Não exponha informação pessoal desnecessária, segredos ou credenciais.

## Segurança e comportamento

Questões de segurança que possam ser exploradas não devem ser detalhadas publicamente antes de uma triagem adequada. Use o canal de relato privado do GitHub, se estiver habilitado; caso contrário, peça orientação sem divulgar detalhes de exploração.

Discussões devem permanecer técnicas e respeitosas, inclusive quando houver divergências de interpretação. Não são aceitos assédio, ataques pessoais ou propaganda partidária nos espaços do projeto.

## Licenças

Ao contribuir com código, você concorda com sua disponibilização sob a licença [MIT](LICENSE) do projeto, salvo acordo explícito diferente. Confirme que possui direitos para incluir contribuições e assets de terceiros; atribuições e condições dessas fontes devem acompanhar as alterações.
