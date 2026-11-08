# Checkpoint 4 — buscas, congelamento e avaliação final

Etapa iniciada em 07/11/2026. Este documento descreve o protocolo e as decisões
anteriores ao teste; não comprova sua conclusão. Na elaboração deste protocolo, o teste permanecia reservado. A execução foi
posteriormente concluída e validada: consultar o [relatório final](checkpoint-4-resultados.md).

## Pendências resolvidas no protocolo

O trio solicitado entre sete algoritmos é Stacking, SVM linear e Random Forest.
O trio do catálogo completo do enunciado é Stacking, Ridge e regressão linear.
Serão executadas buscas **nos cinco modelos da união dos dois escopos**, preservando
as duas classificações. Assim, a avaliação do trio solicitado não elimina as buscas
exigidas pelo enunciado. Baseline e linear sem regularização continuam referências.

As buscas usam `GridSearchCV` real, `PredefinedSplit` com as três dobras persistidas,
RMSE como métrica principal, MAE e R² complementares e desvio populacional entre
dobras. São doze configurações por modelo, totalizando 180 avaliações por dobra.
Todas usam os 2.153.941 participantes do desenvolvimento e as 40 entradas originais.
Nenhum resultado do teste participa de escolha, desempate ou ajuste.

| Modelo | Espaço registrado |
|---|---|
| SVM linear | C = 0,01; 0,1; 1; 10 × epsilon = 0; 0,1; 1 |
| Linear | fit_intercept = verdadeiro/falso × tol = 10⁻³, 10⁻⁴, 10⁻⁵, 10⁻⁶, 10⁻⁷, 10⁻⁸ |
| Ridge | alpha = 0,001; 0,003; 0,01; 0,03; 0,1; 0,3; 1; 3; 10; 30; 100; 1.000 |
| Random Forest | profundidade = 8 ou 12 × árvores = 5, 10, 15, 20, 25, 30 |
| Stacking | mesmos doze valores de alpha para o Ridge combinador |

Na SVM, o teto numérico de iterações passa de 5.000 para 50.000 em todas as
configurações da busca, mantendo tol=0,001. Uma configuração com aviso de
não convergência não é aceita silenciosamente. Na regressão linear, tol controla
a precisão do solucionador; não representa uma nova família de modelos. O espaço
da floresta compara quantidade de árvores e profundidade dentro de limites compatíveis
com a execução nacional local; não demonstra ótimo global fora desses intervalos.
Os demais parâmetros, sementes e regras de preparação permanecem registrados.

As configurações iniciais continuam elegíveis. Uma melhoria de RMSE de até 10⁻⁸
é tratada como equivalência numérica, preservando a configuração inicial. Essa
tolerância não é um teste de significância nem uma margem de relevância prática.
Fora dessa tolerância, o menor RMSE médio decide; empates exatos usam MAE, R² e
identificador da configuração, sem arredondar previamente os resultados.

## Reaproveitamento de cálculos e validação

O `GridSearchCV` recebe um estimador compatível com o scikit-learn que verifica
os hashes dos dados, alvos, IDs e parâmetros de cada ajuste. O ID é uma coluna de
controle e é removido antes de qualquer modelo ou transformação ser ajustado.
Cada pipeline aprende somente no treino de sua dobra.

Na Random Forest, configurações que diferem apenas no número de árvores usam os
prefixos da mesma floresta de 30 árvores, com semente inteira 42 e demais parâmetros
idênticos. A floresta de profundidade 12 pode reutilizar os ajustes verificados do
Checkpoint 3; a de profundidade 8 é ajustada no mesmo treino da dobra. A equivalência
foi conferida contra ajustes diretos em dados reais, incluindo os arrays das árvores.

No Stacking, as bases são fixas. As previsões internas fora da dobra (OOF) são
calculadas uma vez por treino externo, com três dobras internas e pipelines próprios.
Cada alpha ajusta um novo combinador Ridge sobre essas mesmas previsões OOF. As bases
ajustadas no treino externo completo podem ser reutilizadas do Checkpoint 3. O cache
não usa previsões ajustadas no próprio treino como substituto das previsões OOF.
O combinador com alpha=1 precisa reproduzir o original antes de utilizar outros valores.

A sondagem técnica utilizou exclusivamente participantes reais: 10.000 de treino
e 2.048 de validação para equivalência dos ensembles, além de 12.000 registros de
desenvolvimento para comparar o `GridSearchCV` com e sem cache e conferir a retomada.
Ela não substitui as 180 avaliações nacionais. Evidência: `validacao_cache.json`.

Modelos e previsões intermediários ficam locais, fora do Git, em `modelos_ajustados/`
e `cache_buscas/`. O espaço disponível foi conferido. Trabalhos compartilhados e
execuções concorrentes impedem interpretar os tempos como benchmark isolado de
velocidade; registrar tempo total observado e origem dos ajustes reutilizados.

## Sequência até abrir o teste

1. Concluir e validar as cinco buscas, seus 60 candidatos e 180 avaliações, mostrando
   resultados antes/depois e preservando configurações sem melhoria.
2. Escolher a configuração de cada um dos três algoritmos solicitados apenas pelo
   desenvolvimento. Confrontar também buscas, modelos originais e variantes já
   executadas para fixar a solução acadêmica do catálogo ampliado.
3. Registrar receitas, parâmetros, entradas, critérios, evidências e hashes em um
   congelamento verificável. A solução acadêmica deve permanecer identificada mesmo
   se outro modelo tiver menor erro no teste.
4. Produzir as curvas correspondentes às configurações escolhidas. Reutilizar curvas
   anteriores somente quando os parâmetros e contextos forem compatíveis; configurações
   alteradas precisam de seus próprios resultados. Nenhuma busca usa o teste.
5. Reajustar os modelos congelados no desenvolvimento completo. Só depois liberar a
   avaliação dos mesmos 538.486 IDs reservados, em uma execução persistente e retomável.
   Avaliar o trio, o baseline, a linear de referência e, se distinta, a solução acadêmica.
6. Reportar métricas, resíduos, observado versus previsto e erros por faixa/escola/UF/renda
   com contagens. Ordenar o trio pelo RMSE de teste apenas para descrever a comparação
   final; não retomar buscas ou alterar configurações com base nesse resultado.

O alvo é contínuo. As visualizações finais usam erros e resíduos adequados à regressão.
As faixas de nota seguem os limites previamente registrados: 0, 400, 500, 600 e 700.
O estado do Checkpoint 4 só será marcado como concluído após executar, validar e
apresentar essa sequência. Artigo e PDFs continuam nos checkpoints seguintes.

## Execução das buscas

Na raiz do repositório:

```bash
.venv/bin/python scripts/executar_buscas_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --checkpoint2 resultados/ciencias_natureza/checkpoint-2-2026-11-06 \
  --checkpoint3 resultados/ciencias_natureza/checkpoint-3-2026-11-06 \
  --references resultados/ciencias_natureza/cv-recuperado-v2 \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07 --prepare-only

.venv/bin/python -u scripts/executar_buscas_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07 \
  --models svm linear ridge random_forest stacking --resume
```

Uma nova reprodução deve usar outra saída. A retomada confere contexto e hashes antes
de reutilizar ajustes e previsões; uma trava impede duas buscas simultâneas da mesma
família. A validação do cache deve estar registrada antes de iniciar as buscas.
O arquivo `validacao_cache.json` desta execução pode acompanhar uma reprodução com
a mesma fonte, código e ambiente; a busca verifica seu hash de código. Se o mecanismo
for alterado, sua equivalência deve ser novamente conferida em dados reais.

## Comandos das etapas seguintes

Os comandos abaixo já estão implementados, mas só serão executados quando seus
pré-requisitos forem concluídos. A execução de um comando não equivale à aprovação
de todo o checkpoint.

```bash
.venv/bin/python -u scripts/executar_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07 --stage freeze \
  --variants resultados/ciencias_natureza/engineered-v2 \
  resultados/ciencias_natureza/selected-v2 resultados/ciencias_natureza/pca-v2 \
  resultados/ciencias_natureza/weighted-v2 resultados/ciencias_natureza/without_socio-v2 \
  resultados/ciencias_natureza/without_uf-v2

.venv/bin/python -u scripts/executar_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07 --stage curves

.venv/bin/python -u scripts/executar_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07 --stage fit

.venv/bin/python -u scripts/executar_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07 --stage test

.venv/bin/python scripts/executar_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07 --stage validate

.venv/bin/python scripts/publicar_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --checkpoint resultados/ciencias_natureza/checkpoint-4-2026-11-07 \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07/publicacao-reproducao
```

Curvas e ajustes finais aceitam `--models` para executar uma família por processo.
Etapas concluídas são verificadas e reutilizadas; a avaliação do teste só retoma os
mesmos pesos e protocolo. A trava persistente `dados/splits/ciencias-natureza-v1/avaliacao_final.json`
não deve ser apagada para executar outra escolha de modelos. As métricas são calculadas
sem limitar as previsões à faixa observada; os gráficos incluem todos os participantes.

## Critérios de validação

- **Buscas:** 60 configurações válidas, 180 pares configuração/dobra, parâmetros
  pertencentes às grades, contagens nacionais iguais e zero avisos. Recalcular RMSE,
  MAE e R² das previsões reais e confrontar os CSVs do `GridSearchCV`, médias e desvios.
- **Curvas finais:** 15 pontos por receita, IDs iguais ao plano cumulativo do CP3,
  parâmetros congelados, arquivos íntegros e reprodução da validação em 100%.
- **Ajustes finais:** todos os 2.153.941 IDs do desenvolvimento, mesmas receitas,
  pesos salvos antes de carregar o teste e nenhum aviso de convergência.
- **Teste:** exatamente os 538.486 IDs reservados, sem duplicações, previsões finitas
  para todos os modelos, métricas recalculadas e contagens de cada estratificação
  somando a população de teste. Conferir também as métricas de cada grupo após exportar.
- **Publicação:** todas as figuras derivadas dos CSVs validados, PNG de 300 dpi e SVG,
  títulos, eixos e legendas legíveis; conferência visual antes do encerramento.

Falhas de hash, parâmetros, cobertura ou convergência interrompem a etapa e exigem
investigação. Não substituir valores ausentes nem preencher resultados para avançar.
Não foram criados arquivos de testes automatizados; as verificações técnicas usam
dados reais e os validadores fazem parte do fluxo de produção dos resultados.

Fontes do mecanismo: [GridSearchCV](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html),
[StackingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingRegressor.html)
e [RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).

A publicação aprovada desta execução é `publicacao-v2/`; a versão anterior foi
preservada. Para reproduzir gráficos, usar um novo diretório de saída.
