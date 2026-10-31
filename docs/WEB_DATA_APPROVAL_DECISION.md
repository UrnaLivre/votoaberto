# Decisão proposta ao operador — primeira base Web

**Estado: READY_FOR_DATA_APPROVAL. Nenhuma aprovação formal foi registrada.**
Revisar em conjunto com a [política](DATA_PROVENANCE_POLICY.md), a
[entrega M6.1](WEB_DATA_PROVENANCE_FINALIZATION.md) e o
[candidato estruturado](WEB_DATA_APPROVAL_CANDIDATE.json).

## Objeto exato da decisão

| Campo | Valor preparado |
| --- | --- |
| Dataset eleitoral, preservado | `e4e9c9cb5189ab5d4e124bfc` |
| Nova release de metadados | `cf1a3b405d96fb5dd676f025` |
| SHA-256 do novo manifesto | `c1dd2ae876eecfd685d67bb5f53bb7efd223c8db5772a76a83b773b0da2a54e3` |
| SHA-256 de `provenance.json` | `2b1fadbd610cbe5bbb3be6084519f80a25fc8fd40c8b853c87b27f0652a07a53` |
| Política | `tse-presidential-documented-provenance-1` |
| Tag de dados proposta | `web-data-2026-v1` — ainda não criada |
| Publicação/deploy | Não autorizado por esta preparação |

O ID eleitoral identifica os JSONs preservados. A nova identidade e o novo hash
identificam a avaliação/metadados alterados. A aprovação exige os dois IDs e o
manifesto exato; a aprovação de outro manifesto ou revisão não é reutilizável.

## Pontos para uma decisão única informada

- [ ] Aceito as 56 referências SHA-512 oficiais da fotografia M6, agora comparadas
  também com os bytes locais atuais. A anomalia RR está documentada e resolvida;
  a URL inferida do ZIP não é descrita como consulta efetuada.
- [ ] Aceito a política geral que admite o recurso nacional sem checksum publicado,
  com catálogo, aquisição documentada, hashes atuais e reconciliação completa
  com BWEBs que possuem referência oficial. Não estou declarando um hash local
  como checksum oficial nem uma assinatura digital inexistente.
- [ ] Confirmo a confiança no testemunho de aquisição direta do TSE já declarado
  na mensagem M6.1. Entendo que é testemunho retrospectivo, não log de download
  contemporâneo ou prova criptográfica independente.
- [ ] Aceito o escopo presidencial de 2026, ambos os turnos, 27 UFs e ZZ, e as
  limitações: completude exaustiva de seções não avaliada, equipamentos não
  autenticados, ausência de assinatura independente e nenhuma conclusão sobre
  cargos não selecionados ou legitimidade absoluta do processo eleitoral.
- [ ] Aprovo a redistribuição dos derivados e as atribuições abaixo, com as
  transformações identificadas e separação da licença MIT do código.
- [ ] Aprovo os IDs/hashes acima e a proposta de tag de dados para a etapa
  posterior de preparação da release, sem confundir isso com deploy autorizado.

## Redistribuição e atribuição consolidadas

Consulta documental: 31/10/2026. Metadados TSE/termos na
[evidência M6](WEB_DATA_REDISTRIBUTION_EVIDENCE.json); fundamento complementar
primário na [evidência M6.1](WEB_DATA_REDISTRIBUTION_SUPPLEMENT.json).

| Material efetivamente usado | Termo/fundamento proposto | Conduta de atribuição |
| --- | --- | --- |
| TSE/AGEL, [Resultados 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026) e [BWEB 2026](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna) | Catálogos declaram Creative Commons Atribuição/`cc-by`, sem versão numérica explícita. O [link indicado](https://opendefinition.org/licenses/cc-by/) atualmente apresenta CC BY 4.0 | TSE, títulos, URLs, acesso, licença como declarada e transformações; nenhum endosso presumido |
| TSE/SMG, [códigos TSE/IBGE](https://dadosabertos.tse.jus.br/dataset/codigos-oficiais-de-uf-e-municipios-segundo-o-tse-e-o-ibge), e TSE/AGEL, [locais 2026](https://dadosabertos.tse.jus.br/dataset/eleitorado-2026/resource/300626b4-2b24-4d2e-b4fc-46b569cfffe5) | CC BY declarada no catálogo, também sem versão explícita | Mesmos créditos; identificação dos joins por códigos e limites da correspondência |
| IBGE, [Malhas v3](https://servicodados.ibge.gov.br/api/docs/malhas?versao=3) e [Localidades do Brasil, Censo 2022](https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/) | Reutilização de bases públicas com crédito, fundamentada no produto oficial, PDA IBGE e no [Decreto 8.777/2016 atualizado, arts. 2–4](https://www2.camara.leg.br/legin/fed/decret/2016/decreto-8777-11-maio-2016-783082-normaatualizada-pe.html). Não atribuir CC/MIT ou SPDX que o recurso não declara | IBGE, produtos, URLs, projeção/conversão, seleção e arredondamento; limitações cartográficas |
| Natural Earth 5.1.1, geometria e rótulos 1:50m | [Termos oficiais](https://www.naturalearthdata.com/about/terms-of-use/): domínio público em todas as versões | Crédito mantido, embora facultativo; simplificação e arredondamento informados |
| TRE-DF, [edital de carga/lacração 2026](https://www.tre-df.jus.br/comunicacao/noticias/arquivos/edital-carga_e_lacracao_das_urnas_eletronicas__df_e_zz____2026/@@download/file) | Fatos/correspondências extraídos de ato oficial; [Lei 9.610/1998, art. 8º, IV](https://www2.camara.leg.br/legin/fed/lei/1998/lei-9610-19-fevereiro-1998-365399-normaatualizada-pl.html). Não atribuir CC inexistente | TRE-DF, título, URL e indicação de extração independente; sem reprodução de logos, fotos ou documento integral |

**Conclusão documental proposta:** os dados TSE possuem termo de atribuição;
Natural Earth declara domínio público. Para IBGE, o fundamento é a reutilização
de bases públicas e o crédito, sem inventar licença específica. O Decreto atualizado
autoriza uso gratuito das bases sob direitos patrimoniais da União e exige
identificação de condições de terceiros. A inferência aplicada aqui abrange as
bases vetoriais/estatísticas oficiais usadas, sem indicação identificada de
restrição específica de terceiros nesses recursos. Não se estende a mapas
impressos, imagens, logos ou quaisquer materiais IBGE com condições distintas.

Para TRE-DF, a inferência abrange os fatos derivados do ato oficial, não elementos
gráficos de terceiros. A consulta nova da página do edital foi indisponível (403)
em M6; mantém-se o documento/hash retido, sem afirmar nova autenticação.

Isso é avaliação documental para decisão do operador, não parecer jurídico formal.
A falta de um rótulo SPDX, de versão CC explícita ou de assinatura digital não
gera por si um requisito técnico impossível. As ressalvas acima devem integrar
a aprovação; se o operador rejeitar essa fundamentação, pode solicitar confirmação
específica do órgão antes de aprovar. Não há investigação técnica essencial
pendente para a via metodológica implementada.

### Texto de crédito recomendado

> Dados eleitorais: Tribunal Superior Eleitoral, Portal de Dados Abertos —
> Resultados 2026 e Boletins de Urna, votação presidencial, ambos os turnos;
> códigos TSE/IBGE e locais de votação 2026. Licença declarada nos catálogos:
> Creative Commons Atribuição, sem versão numérica explícita. Consulta de
> proveniência em 31/10/2026. O Voto Aberto realiza processamento independente:
> seleção, reconciliação, agregação e conversão para JSON. Fontes, hashes,
> transformações e limitações acompanham o manifesto. Não se presume endosso
> do TSE ou certificação do processo eleitoral.
>
> Cartografia e referências: IBGE — Malhas Geográficas v3 e Localidades do Brasil,
> Censo 2022; Natural Earth 5.1.1, domínio público; TRE-DF, edital de carga e
> lacração 2026. Coordenadas convertidas/selecionadas e geometria mundial
> simplificada pelo Voto Aberto. Mapas servem à navegação, sem precisão para
> medições, limites eleitorais ou localização de equipamentos.

Esse texto deve acompanhar os links da tabela, preservando títulos, datas,
termos e indicação de modificações. Os créditos do app já identificam os quatro
fornecedores e processamento independente. MIT continua limitada ao código.

## Registro após a decisão

Somente após autorização explícita, preencher revisor/data e alterar as duas
decisões em `apps/votoaberto_flutter/web-data-approval.json`:
`provenance_approval.approved` e `redistribution_review.approved`. Seus valores
continuam **false** nesta entrega. Não mudar ID/hash para superar falha do gate.

Uma validação posterior usa `web_release.py preflight` e `bundle`. O candidato
atual retorna saída 2 precisamente porque a decisão ainda não foi registrada.
Criar tag/release de dados, enviar commits ou publicar é uma etapa posterior,
com autorização própria; `WEB_DEPLOY_ENABLED` permanece desativada nesta missão.
