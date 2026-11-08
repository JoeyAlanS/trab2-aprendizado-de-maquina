# Resultados reais e estado das entregas

Atualizado em 07/11/2026. `experimentos.csv` contém **72 linhas reais**: 54 avaliações
por dobra e 18 resumos, das onze entradas do catálogo original e sete combinações de modelo/variante.
As sete famílias solicitadas no Checkpoint 1 concluíram suas 21 avaliações nacionais.
O arquivo é cópia de `publicacao-checkpoint-1-2026-11-06/experimentos.csv`; sua proveniência e seu
hash estão em `manifesto_publicacao.json` e no manifesto da publicação.

| Diretório em `ciencias_natureza/` | Evidência |
|---|---|
| `cv-inicial-v1` | Comparação histórica válida, preservada |
| `cv-recuperado-v2` | Reexecução nacional de baseline, linear, Ridge e árvore; métricas idênticas ao histórico |
| `checkpoint-1-2026-11-06` | Sete algoritmos completos; `publicacao-v2` contém a comparação, três figuras PNG/SVG e a validação das 21 avaliações |
| `checkpoint-2-2026-11-06` | Seleção entre os sete: Stacking, SVM linear e Random Forest; ranking completo, configurações, margens, dois gráficos PNG/SVG e validação |
| `checkpoint-3-2026-11-06` | Concluído e validado: 45 pontos das curvas do trio, 15 resumos, três figuras PNG/SVG, reprodução dos nove pontos em 100% e relatório |
| `checkpoint-4-2026-11-07` | Concluído: 60 configurações, 180 avaliações CV, 45 pontos finais e cinco modelos no teste; gráficos aprovados em `publicacao_buscas-v2`, `publicacao_curvas_finais` e `publicacao-v2` |
| `checkpoint-5-2026-11-07` | Coleção final validada: 17 PNGs de 300 dpi, 17 SVGs, 14 tabelas e galeria HTML com filtros; sem novos treinamentos |
| `engineered-v2`, `selected-v2` | Três features criadas e seleção, ambas com Ridge |
| `pca-v2` | PCA com Ridge e árvore, 45 componentes em cada dobra |
| `weighted-v2` | Ridge ponderado por faixas aprendidas somente no treino |
| `without_socio-v2`, `without_uf-v2` | Duas ablações com Ridge |
| `figuras-corrigidas-v4` | Distribuição real, comparação das rodadas concluídas e variância PCA |
| `evidencias` | Integridade, recuperação, reexecução, interface e bloqueios de protocolo |
| `eda-v1`, `dashboard-v1`, `relacoes-v1` | EDA, agregados e relações históricos reais; painel mantém a comparação inicial |

`row_type=fold` identifica dobra; `summary`, resumo de três dobras com desvio populacional
(`ddof=0`); `test_final` é reservado à avaliação final. Não misturar teste com média CV.
Cada execução mantém parâmetros, features, fonte, partições e hashes de seus resultados.
O código-fonte Python também é identificado por hashes nos manifestos das novas rodadas.

**As previsões reais dos cinco modelos para os 538.486 participantes estão em**
`ciencias_natureza/checkpoint-4-2026-11-07/avaliacao_final/previsoes_teste.csv`.
Esse CSV individual permanece local e é ignorado pelo Git; os agregados e a
recomposição das métricas ficam versionados. As cinco linhas `test_final` estão em `avaliacao_final/experimentos.csv`, separadas
das 72 linhas de desenvolvimento do consolidado inicial. O antigo
arquivo com 50 mil previsões sintéticas, os resultados fixos e as imagens correspondentes
foram preservados no ZIP de `historico/2026-11-05/` e retirados das entregas ativas.
O gerador atual só publica previsões reais após validar uma avaliação final concluída.

A seleção dos três entre os sete foi concluída no Checkpoint 2, sem novos treinamentos
ou acréscimo de avaliações ao consolidado. O diagnóstico do catálogo ampliado foi
registrado separadamente, pois nele linear e Ridge alteram as primeiras posições.
As curvas das configurações iniciais dos três foram concluídas no Checkpoint 3. Seus
45 pontos ficam separados do consolidado anterior de 72 linhas. O Checkpoint 4
concluiu buscas, congelamento, curvas finais, reajustes e teste do trio com referências.
A organização final das visualizações foi concluída no Checkpoint 5. O artigo foi concluído no Checkpoint 6. O Checkpoint 7 reúne roteiro do pitch,
acompanhamento e artigo LaTeX, PDFs e auditoria final das execuções.
Versões anteriores de publicação
e figuras permanecem como registro das verificações; utilizar a versão indicada acima.

Consulte `docs/checkpoint-5-resultados.md`, `docs/checkpoint-4-resultados.md`, `docs/checkpoint-3-resultados.md`, `docs/checkpoint-2-resultados.md`, `docs/checkpoints.md` e `docs/validacao-manual.md`.

A revisão final confirmou 54 avaliações iniciais/variantes, 180 avaliações de busca,
45 pontos iniciais e 45 finais de curvas e cinco modelos no teste. Ver
`checkpoint-7-2026-11-07/auditoria_experimentos.json` e
`checkpoint-7-2026-11-07/cobertura_execucoes.csv`. Os pontos finais incluem reutilização
de cálculos compatíveis, não 45 novos treinamentos. Nenhuma nova seleção usou o teste.
