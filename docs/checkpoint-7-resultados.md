# Checkpoint 7 - pitch, entrega LaTeX e auditoria final

Revisão de 07/11/2026. Entregas locais concluídas. O pedido atual dispensa slides;
ensaio oral, apresentação e submissão no AVA permanecem com a equipe.

## Documentos prontos

| Entrega | PDF compilado | Fonte editável | Páginas |
|---|---|---|---:|
| Pitch em roteiro, com falas e perguntas/respostas | [pitch.pdf](../output/pdf/pitch.pdf) | [pitch.tex](../relatorio/pitch.tex) | 6 |
| Acompanhamento e auditoria | [acompanhamento.pdf](../output/pdf/acompanhamento.pdf) | [acompanhamento.tex](../relatorio/acompanhamento.tex) | 5 |
| Artigo científico | [artigo_latex.pdf](../output/pdf/artigo_latex.pdf) | [artigo.tex](../relatorio/artigo.tex) | 10 |

Autores: Joey Alan de Freitas Solis e Paulo Henrico; Universidade de Fortaleza
(Unifor), professor Tulio. O roteiro propõe doze minutos, com seis minutos por autor;
essa duração ainda precisa ser aferida em ensaio. Não foram criados slides.

O [ZIP para Overleaf](../output/overleaf-enem2023.zip) contém doze arquivos, com
`main.tex` na raiz, os três documentos, sete figuras e um README. Selecionar XeLaTeX;
`main.tex` compila o pitch. Para os demais documentos, selecionar `artigo.tex` ou
`acompanhamento.tex`. O pacote dispensa Python e arquivos externos ao ZIP.

Os três documentos foram compilados com Tectonic 0.17.0 (motor XeTeX). Todas as 21
páginas foram renderizadas e inspecionadas. Não há caixas excedentes nem glifos
ausentes nos logs. Tamanho A4, limites do texto, nomes e métricas foram conferidos.
O ZIP passou por CRC; seus arquivos extraídos coincidem com as fontes e seu
`main.tex` foi compilado de forma independente, produzindo o mesmo texto do pitch.
A compilação dentro de uma conta Overleaf não foi executada.

O artigo histórico do Checkpoint 6 foi preservado. A nova edição usa Times portável
via `mathptmx`, mantendo resultados e o limite de dez páginas. O guia completo está
em [relatorio/README.md](../relatorio/README.md).

## O que realmente foi executado e conferido

| Experimento | Cobertura confirmada |
|---|---|
| Sete algoritmos solicitados | 7 modelos × 3 dobras nacionais = 21 avaliações |
| Referências iniciais | Média, linear, Ridge e árvore; 12 avaliações |
| Representações e hipóteses | 21 avaliações: engenharia, seleção, PCA em dois modelos, ponderação e duas ablações |
| Buscas | 5 modelos × 12 configurações × 3 dobras = 180 avaliações |
| Curvas iniciais | 3 modelos × 5 tamanhos × 3 dobras = 45 pontos |
| Curvas finais | 45 pontos com identidade e origem verificadas; incluem reaproveitamento compatível |
| Teste reservado | Cinco modelos nos mesmos 538.486 participantes; métricas e 260 registros por grupo recompostos |

**Todos os sete algoritmos têm validação cruzada concluída. Isso não significa que
todos tenham sido aplicados ao teste reservado.**

| Modelo | Validação cruzada | Teste reservado |
|---|---|---|
| SVM linear | Sim, três dobras | Sim |
| KNN | Sim, três dobras | Não previsto após a seleção |
| Bagging | Sim, três dobras | Não previsto após a seleção |
| Pasting | Sim, três dobras | Não previsto após a seleção |
| Random Forest | Sim, três dobras | Sim |
| Gradient Boosting | Sim, três dobras | Não previsto após a seleção |
| Stacking | Sim, três dobras | Sim |
| Média e linear de referência | Sim, três dobras cada | Sim |
| Ridge e árvore isolada | Sim, três dobras cada | Não |

As curvas finais têm 30 pontos com configurações idênticas às iniciais, 12 pontos
com bases reaproveitadas e novo combinador Stacking, e três pontos provenientes do
treino completo das dobras nas buscas. Não são 45 treinamentos inteiramente novos.
A revisão desta entrega não treinou modelos nem produziu novas previsões de teste.
Como o alvo é contínuo, os gráficos adequados são resíduos, observado versus previsto
e erros por grupos; matrizes de confusão não se aplicam a esta regressão.

Stacking obteve RMSE de 76,189590, MAE de 55,325018 e R² de 0,249711 no teste,
reduzindo o RMSE da média em 13,38%. A linear obteve RMSE de 76,516794; SVM,
76,622171; Random Forest, 76,657930; média, 87,959294. A vantagem sobre a linear
é pequena e não foi submetida a teste de significância. Os erros crescem nos
extremos das notas. Não há validação em outra edição do ENEM nem conclusão causal.

## Testes de software e evidências

A suíte existente foi executada: **81 testes aprovados, zero falhas, em 11,44 s**.
São testes técnicos com fixtures, distintos dos experimentos nacionais acima:
ingestão (19), pré-processamento (13), dashboard (11), estudo/modelos (9),
configuração/CLI (7), partições (7), aquisição/integração (6), relações (5) e
download oficial (4). O relatório JUnit está em `pytest.xml`.

Lint, formatação e compatibilidade das dependências locais foram aprovados. Cópias
históricas de código em `resultados/**/codigo` e `historico` são excluídas do Ruff;
o código ativo é verificado integralmente. Não foram criados novos testes para
as alterações documentais. Não se declara nova execução Windows, nova inspeção
interativa completa do dashboard, ensaio oral, teste temporal, validação externa,
inferência causal ou teste de significância. A automação remota tem histórico próprio.

Evidências em
[`resultados/ciencias_natureza/checkpoint-7-2026-11-07/`](../resultados/ciencias_natureza/checkpoint-7-2026-11-07/):

- `auditoria_experimentos.json` e `cobertura_execucoes.csv`: cobertura por etapa/modelo;
- `validacao_buscas.json` e `validacao_teste.json`: recomposição de métricas reais;
- `pytest.xml`: testes de software efetivamente executados;
- `fontes_latex.json` e `compilacao_latex.json`: fontes e compilação;
- `validacao_documentos.json` e `validacao_overleaf.json`: inspeção e pacote independente;
- `limpeza.json`: inventário e hashes dos arquivos retirados da área ativa;
- `qualidade_final.json` e `checkpoint.json`: conferência final e fechamento da entrega.

## Dados, limpeza e reprodução

O Checkpoint 6 incorporou os dois ZIPs originais e validou seu CRC. O CSV nacional
contém 3.933.955 linhas e 76 colunas; todas as células normalizadas coincidem com os
79 Parquets. Permanecem 2.692.427 alvos observados, incluindo 16.547 zeros. O
complemento de redação está preservado sem entrar nos preditores. Esses dados e
os modelos/previsões individuais continuam locais e fora do Git.

A limpeza retirou **44 arquivos preliminares ou duplicados da área ativa**,
preservando-os em `historico/2026-11-07/limpeza-pre-entrega.zip` e
`templates-pre-entrega.zip`, ambos com inventário e hashes. Foram substituídos
pacotes antigos de relatório, fontes obsoletas, figuras/tabelas antigas, templates
e dois scripts antigos de compilação. Os artefatos necessários à rastreabilidade
dos checkpoints foram mantidos. A limpeza não removeu entradas científicas.

```bash
.venv/bin/python scripts/auditar_entrega.py
.venv/bin/python scripts/publicar_latex.py
.venv/bin/python scripts/compilar_latex.py --tectonic /caminho/para/tectonic
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
```

O auditor requer os dados e caches locais preservados; não basta clonar apenas os
resultados agregados. A compilação dos TEX, por outro lado, é independente dos
microdados. Regenerar as fontes sobrescreve os TEX; preservar antes alterações
feitas diretamente no Overleaf. O commit e sua publicação são verificáveis no
histórico Git e na mensagem final da entrega, sem antecipar sucesso neste relatório.
