# Rastreabilidade dos requisitos — revisão de 07/11/2026

Fontes: enunciado Markdown fornecido e `referencias/enunciado-projeto2.pdf`.
O enunciado define os critérios acadêmicos; não comprova que as entregas ocorreram.
“Implementado” não significa “executado”. A conclusão depende das evidências indicadas.

| Exigência | Estado verificável | Evidência ou pendência |
|---|---|---|
| Alvo de regressão definido | Atendido: NU_NOTA_CN | `configs/ciencias_natureza.toml` |
| Fonte nacional integral, 3.933.955 linhas e 76 colunas | Originais incorporados e base integral conferida | CRC dos ZIPs; hashes históricos; todas as células normalizadas do CSV iguais aos 79 Parquets (Checkpoint 6) |
| Diagnóstico de todos; supervisão apenas com alvo observado | Atendido | 2.692.427 elegíveis; 1.241.528 sem alvo; qualidade e partições |
| Preservar zeros, treineiros e faixas etárias; não exigir outras notas | Atendido | 16.547 zeros nacionais, sem filtros por perfil ou por notas de outras áreas |
| Entradas sem notas, respostas, gabaritos, presença, resultados ou IDs | Implementado e usado nas execuções | `features.py`, `preprocessing.py`, lista de 40 entradas no TOML |
| Dicionário, categorias, ausências, duplicatas e distribuição | Evidências existentes | `eda-v1`, `dashboard-v1`, `relacoes-v1`; limitações de códigos documentadas |
| Integração externa, quando utilizada | Não utilizada; opcional | Não alegar indicadores externos no artigo |
| 80/20, semente 42, IDs persistidos | Atendido | 2.153.941 desenvolvimento; 538.486 teste; recuperação comparou cada ID/dobra com o banco |
| KFold de três dobras, mesmas partições, sem validação fixa adicional | Atendido nas execuções concluídas | `validation_fold`, manifestos e contagens das dobras |
| Transformações ajustadas somente no treino | Implementado e aplicado | Pipelines de engenharia, seleção, PCA e regressores; pesos usam apenas y do treino |
| Baseline, linear sem/com regularização e árvore | Executados e reproduzidos | `cv-recuperado-v2`, 12 avaliações; métricas idênticas ao histórico |
| SVM, KNN, bagging, pasting, Random Forest, boosting e stacking | Concluído e validado no Checkpoint 1 | 21 avaliações nacionais; `checkpoint-1-2026-11-06/publicacao-v2/checkpoint_validado.json` |
| Seleção dos três entre os sete algoritmos solicitados | Concluído e validado no Checkpoint 2 | Stacking, SVM linear e Random Forest; escopo explícito, tabela, justificativa e configurações em `checkpoint-2-2026-11-06` |
| Três features criadas, justificadas e comparadas | Executado | `engineered-v2`; recursos por morador, acesso digital e escolaridade parental |
| Método de seleção comparado | Executado | `selected-v2`; F-regression, 75% das colunas codificadas |
| PCA em pelo menos dois regressores | Executado | `pca-v2`: Ridge e árvore; 45 componentes em cada dobra, critério ≥80% |
| Balanceamento adequado à regressão, somente no treino | Executado, com piora global | `weighted-v2`: Ridge ponderado; métricas gerais e por faixa registradas |
| Busca nos três melhores distintos, ≥10 configurações por modelo | Concluída e validada no Checkpoint 4 | GridSearchCV: 60 configurações, 180 avaliações nacionais, zero avisos; métricas recalculadas das previsões; união dos escopos |
| RMSE, MAE, R², tempo, média e desvio | Atendido nas comparações executadas | `resultados/experimentos.csv`: 54 dobras e 18 resumos; 11 entradas originais e sete combinações de modelo/variante |
| Duas hipóteses adicionais | Executadas; interpretação inicial documentada | `without_socio-v2` e `without_uf-v2`; mesma configuração Ridge |
| Curvas dos três selecionados: cinco tamanhos e três dobras | Concluído e validado no Checkpoint 3 | 45 pontos, 15 resumos, três figuras PNG/SVG, análise de ajuste e generalização; configurações iniciais |
| Curva da solução final após buscas e congelamento | Concluída e validada no Checkpoint 4 | 45 pontos das três receitas finais, incluindo Stacking alpha=1.000; reprodução da CV e gráficos conferidos antes do teste |
| Avaliação final: baseline, linear e solução nos mesmos IDs | Concluída e validada no Checkpoint 4 | Trio, baseline e linear em 538.486 IDs; cinco reajustes completos, métricas recompostas das previsões e trava persistente |
| Resíduos, erros por faixa e por grupo com n | Concluído no Checkpoint 4 | Resíduos e 260 registros por faixa, escola, UF e renda; métricas e contagens recompostas; nove gráficos finais revisados |
| Seis figuras e tabela obrigatórias do artigo | Integrado e validado | Artigo do Checkpoint 6: sete figuras, três tabelas e quadro de configurações; coleção completa preservada no Checkpoint 5 |
| Código, ambiente, partições, experimentos e reprodução | Código e evidências preparados para publicação | README/locks/manifestos; dados e previsões individuais ignorados no Git; commit/push registrados no histórico Git |
| Acompanhamento: slides PDF e participação de todos | Documento concluído; apresentação não realizada | `output/pdf/acompanhamento.pdf`, fonte LaTeX; slides dispensados pelo pedido atual |
| Artigo ABNT, até dez páginas incluindo referências | Concluído no Checkpoint 6 | Versão atual: `output/pdf/artigo_latex.pdf`, fonte `relatorio/artigo.tex`; original do CP6 preservado |
| Pitch de 10–15 min, slides PDF, todos participam | Roteiro concluído; ensaio e apresentação pendentes | `output/pdf/pitch.pdf`, fonte LaTeX e pacote Overleaf; sem slides conforme pedido |
| Prazos no AVA | Não verificável no ambiente | Equipe precisa consultar e registrar |

Os 28 arquivos invalidados foram preservados com hashes em
`historico/2026-11-05/artefatos-nao-validados.zip`. Não usar esses números ou figuras.
Resultados sem melhoria são válidos e devem ser discutidos; o enunciado não exige R² mínimo.
Relatório detalhado: [correção](relatorio-correcao-2026-11-05.md).
Atualização dos sete algoritmos: [Checkpoint 1](checkpoint-1-resultados.md).
Seleção entre os sete e diagnóstico de escopo: [Checkpoint 2](checkpoint-2-resultados.md).

Curvas iniciais do trio e sua validação: [Checkpoint 3](checkpoint-3-resultados.md).
