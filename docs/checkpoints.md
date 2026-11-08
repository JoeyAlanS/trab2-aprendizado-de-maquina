# Desenvolvimento por checkpoints

Protocolo iniciado em 06/11/2026. Cada checkpoint precisa de execução, validação e
apresentação de resultados antes de iniciar o seguinte. O alvo é NU_NOTA_CN, uma
regressão: usam-se RMSE, MAE, R² e análises de resíduos, não matrizes de confusão.

| Checkpoint | Estado | Critério de conclusão |
|---|---|---|
| 1. Sete algoritmos | Concluído e validado | 21 avaliações nacionais; métricas, contagens, hashes e três figuras conferidos; [resultados](checkpoint-1-resultados.md) |
| 2. Três melhores | Concluído e validado | Stacking, SVM linear e Random Forest entre os sete; ranking, métricas, dobras e gráficos conferidos; [resultados](checkpoint-2-resultados.md) |
| 3. Curvas dos três | Concluído e validado em 07/11/2026 | 45 pontos, nove reproduções do CP1, três figuras e análise; [resultados](checkpoint-3-resultados.md) |
| 4. Teste final | Concluído e validado em 07/11/2026 | 60 configurações, 180 avaliações CV, 45 pontos finais, cinco reajustes e teste em 538.486 participantes; nove gráficos; [resultados](checkpoint-4-resultados.md) |
| 5. Visualizações finais | Concluído e validado em 07/11/2026 | 17 figuras PNG/SVG, 14 tabelas, galeria com filtros e pacote ZIP; [resultados](checkpoint-5-resultados.md) |
| 6. Artigo ABNT | Concluído e validado em 07/11/2026 | Originais incorporados e conferidos integralmente; artigo de dez páginas com sete figuras, três tabelas, autores e referências; [resultados](checkpoint-6-resultados.md) |
| 7. Documentos finais | Entregas locais concluídas; apresentação pendente | Pitch sem slides, acompanhamento e artigo LaTeX; auditoria e PDFs conferidos; [resultados](checkpoint-7-resultados.md) |

## Checkpoint 1: critérios registrados

- Fonte nacional completa; desenvolvimento de 2.153.941 participantes.
- Teste de 538.486 participantes permaneceu reservado até a avaliação final do Checkpoint 4.
- Três dobras persistidas, KFold com shuffle e semente 42; cada transformação aprende
  apenas no treino da dobra. Identificadores controlam os conjuntos e não entram em X.
- Mesmas 40 entradas originais e regras de imputação, escala e one-hot para os sete modelos.
- RMSE principal; MAE e R² complementares; média e DP populacional entre as três dobras.
- SVM linear, KNN, bagging/pasting de árvores, Random Forest, GradientBoosting e stacking
  de linear/árvore com Ridge combinador. Configurações completas nos manifestos.
- Preservar os resultados anteriores; cada modelo tem pasta própria em
  `resultados/ciencias_natureza/checkpoint-1-2026-11-06/`.

O script `scripts/executar_checkpoint1.py` executa somente o checkpoint 1, verifica e
reutiliza rodadas completas sem sobrescrever arquivos. Cada nova família roda em processo
próprio para liberar memória ao terminar. Uma pasta incompleta é recusada sem `--resume`;
a retomada explícita verifica fonte, partições, parâmetros e dependências. O status do orquestrador não substitui a conferência
dos sete manifestos e suas 21 avaliações.

```bash
.venv/bin/python -u scripts/executar_checkpoint1.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-1-2026-11-06
```

Os checkpoints 1–6 estão concluídos e validados; as entregas locais do Checkpoint 7
também foram concluídas. Ensaio, apresentação e submissão permanecem com a equipe.
As configurações foram escolhidas no desenvolvimento e fixadas antes do teste.

O Checkpoint 3 agora possui um fluxo próprio para o trio selecionado, com protocolo,
subconjuntos comuns e retomada verificável em `learning_curves.py`. O fluxo legado de
`freeze-solution`, `learning-curve` e `evaluate-final` trabalha com uma solução final;
o teste acrescenta baseline e regressão linear como referências. A solicitação atual
exige curvas e teste para três modelos selecionados. A ampliação foi implementada e validada no Checkpoint 4 em
`final_evaluation.py`: trio, baseline e linear nos mesmos IDs, com pesos e trava persistidos.

## Checkpoint 2: seleção concluída

O ranking dos sete algoritmos pelo RMSE médio, sem arredondamento prévio, selecionou
**Stacking (76,175), SVM linear (76,577) e Random Forest (76,643)**. MAE e R² confirmam
o mesmo trio e a mesma ordem. Os três também ocuparam essas posições em cada dobra.
O desvio entre dobras é descritivo; não foi realizado teste de significância.

O módulo `src/enem_base/selection.py` valida a conclusão do Checkpoint 1, seus hashes,
parâmetros, entradas e 21 avaliações. Produz ranking, margens por dobra, gráficos e
`selecionados.json`, com as configurações iniciais para as próximas etapas.
`load_selection` fornece esse contrato sem consultar o teste. Comando executado:

```bash
.venv/bin/python scripts/selecionar_checkpoint2.py \
  --study configs/ciencias_natureza.toml \
  --checkpoint1 resultados/ciencias_natureza/checkpoint-1-2026-11-06 \
  --references resultados/ciencias_natureza/cv-recuperado-v2 \
  --output resultados/ciencias_natureza/checkpoint-2-2026-11-06
```

Saídas existentes são recusadas; para reproduzir, escolher outro diretório. As métricas
foram derivadas das rodadas reais, sem novo treinamento. Gráficos PNG/SVG, justificativa,
tabela completa e verificações estão em [checkpoint-2-resultados.md](checkpoint-2-resultados.md).

O escopo é o dos sete algoritmos solicitados. No catálogo ampliado, incluindo linear,
Ridge e árvore simples, os três menores RMSE seriam Stacking, Ridge e linear.
O comando legado de busca usa esse catálogo ampliado; ele não consome a seleção deste
checkpoint. As buscas do Checkpoint 4 cobriram a união dos dois escopos,
preservando o trio solicitado e as referências.

## Checkpoint 3: curvas concluídas

Foram concluídos 45 ajustes nacionais em 06/11/2026 e a etapa foi encerrada após
validação numérica e visual em 07/11/2026. Stacking, SVM linear e Random Forest usam
os mesmos subconjuntos cumulativos de 10%, 25%, 50%, 75% e 100%, nas três dobras.
Cada transformação é reajustada no treino correspondente. Nessa etapa, o teste permaneceu reservado.

O Stacking teve o menor RMSE médio nos cinco tamanhos. Em 100%, RMSE de validação:
76,175 (Stacking), 76,577 (SVM) e 76,643 (Random Forest). As diferenças médias entre
validação e treino foram 0,193, 0,007 e 0,400 ponto, respectivamente. As nove avaliações
em 100% reproduziram o Checkpoint 1; os 45 pontos não geraram avisos.

[Resultados, gráficos e interpretação](checkpoint-3-resultados.md),
[protocolo e reprodução](checkpoint-3-protocolo.md). O executor é
`scripts/executar_checkpoint3.py`; o publicador é `scripts/publicar_checkpoint3.py`.
A publicação está em `resultados/ciencias_natureza/checkpoint-3-2026-11-06/publicacao/`;
o encerramento e seus hashes estão no `checkpoint.json` da pasta do checkpoint.

Estas curvas usam as configurações iniciais do Checkpoint 2. No Checkpoint 4,
as buscas foram concluídas e as curvas das receitas finais foram validadas antes do teste.

## Checkpoint 4: concluído

O protocolo registrado compara 12 configurações em cada um de cinco modelos:
Stacking, SVM, Random Forest, Ridge e linear. São 180 avaliações nas três dobras
nacionais, realizadas antes de abrir o teste. O cache foi validado com dados reais,
incluindo equivalência com ajustes diretos e com GridSearchCV sem cache.
As novas rotinas `final_selection.py`, `frozen_curves.py` e `final_evaluation.py`
implementam congelamento, curvas das receitas finais e avaliação retomável do trio
com referências. As execuções finais foram concluídas e verificadas. O bloqueio de uma
tentativa prematura de avaliação foi conferido sem abrir o teste.

[Protocolo, escopos e reprodução](checkpoint-4-protocolo.md).

As cinco buscas terminaram, e a conferência independente das 180 avaliações foi
aprovada sem avisos. As cinco receitas estão congeladas; Stacking é a solução
acadêmica escolhida. SVM e Random Forest mantiveram os parâmetros iniciais. O novo
alpha do Stacking mudou seu RMSE em apenas 3,2 × 10⁻⁸ ponto, sem demonstração de ganho
prático. [Tabelas, gráficos e interpretação das buscas](checkpoint-4-buscas.md).
As curvas finais foram concluídas: 45 pontos, zero avisos e reprodução das métricas
congeladas em 100%. [Análise das curvas finais](checkpoint-4-curvas.md).

Os cinco modelos foram reajustados nos 2.153.941 participantes de desenvolvimento
e avaliados nos mesmos 538.486 participantes de teste. RMSE: Stacking 76,190;
linear de referência 76,517; SVM 76,622; Random Forest 76,658; baseline 87,959.
As métricas e os 260 registros de erros por grupo foram recompostos das previsões
exportadas. Nove gráficos PNG/SVG foram conferidos em `publicacao-v2/`.
Stacking teve o menor RMSE, mas os erros aumentam nos extremos das notas.
[Relatório completo e limitações](checkpoint-4-resultados.md). A organização visual foi concluída no Checkpoint 5 e o artigo no Checkpoint 6; os documentos do Checkpoint 7 foram preparados posteriormente.

## Custo e armazenamento do KNN

O benchmark técnico usou o treino completo da dobra 0 (1.435.960 participantes) e 64
consultas reais de sua validação. A matriz codificada tem 235 colunas. A busca esparsa
levou 7,390 s e a densa float64, 0,589 s nesse diagnóstico. Esses tempos não são o tempo
da comparação nacional nem métricas de desempenho preditivo. Evidência: `knn_preflight.json`.

As distâncias dos 25 vizinhos foram iguais entre os dois backends. Índices diferiram
em empates, uma ambiguidade do KNN; por isso o armazenamento, a ordem das linhas e o
tamanho dos blocos serão fixos. Não se declara que as previsões dos dois backends sejam
sempre idênticas. A primeira alternativa avaliada usa KNeighborsRegressor e busca euclidiana exata,
com a mesma imputação, escala e one-hot, armazenamento contíguo float64 e blocos de 2.048
previsões. Não utiliza vizinhos aproximados nem amostragem. A conversão tem limite de
4 GiB por matriz, e os demais buffers também consomem memória.

Uma verificação adicional com 10.000 participantes reais de treino e 1.024 de validação
confirmou valores idênticos após a conversão e previsões iguais entre chamada única e
blocos de 512 linhas naquele diagnóstico. Isso verifica o mecanismo, não substitui as
três avaliações nacionais. Evidência: `knn_storage_validation.json`.

Fundamentação: [vizinhos mais próximos no scikit-learn](https://scikit-learn.org/stable/modules/neighbors.html).


### Backend exato adotado após a conferência

A implementação nacional usa `ExactProfileKNeighborsRegressor`, uma subclasse de
`KNeighborsRegressor` que preserva a predição e os pesos do scikit-learn. A busca dos
vizinhos usa `faiss-cpu==1.15.1`, adicionado ao ambiente local e aos arquivos de dependências.
O índice é **IndexBinaryFlat**, que examina todas as linhas, sem vizinhos aproximados.
Não são utilizados IVF, HNSW ou quantização de valores contínuos.

A equivalência vem de uma identidade: para uma coluna numérica z e um vetor binário b,
a distância euclidiana ao quadrado é `(z1-z2)² + Hamming(b1,b2)`. Dentro de cada valor
numérico distinto do treino, a primeira parcela é constante para uma consulta. Assim,
os 25 vizinhos globais pertencem à união dos 25 mais próximos de cada grupo. Foram
observados 20 valores distintos de Q005 padronizada; todos os registros são indexados.
A coluna numérica é mantida em float64 e apenas os indicadores já binários são empacotados.
Representações incompatíveis utilizam o backend denso do scikit-learn.

Na validação com o treino completo da dobra 0, a busca de 512 consultas reais levou
0,477 s. Nas 64 consultas conferidas contra o scikit-learn, o maior desvio das distâncias
foi 2,665 × 10⁻¹⁵; a conferência direta dos índices devolvidos diferiu em até 4,441 × 10⁻¹⁶.
As previsões foram iguais entre os blocos verificados, e consultas de registros reais
presentes no treino recuperaram distância zero. Isso validou o mecanismo. As três
avaliações nacionais foram posteriormente concluídas; RMSE médio do KNN: 77,896.
A recomposição das métricas a partir dos 1.053 blocos reais também foi aprovada.

A primeira sondagem dessa conferência parou por uma operação inválida de broadcasting
entre matrizes esparsas no código diagnóstico. O problema foi corrigido e a sondagem
completa foi executada novamente. Os logs foram preservados; a evidência aprovada é
`knn_binary_preflight-v2.json`. Não houve resultado científico inventado para preencher a falha.

Referência da busca exaustiva:
[documentação oficial do Faiss](https://github.com/facebookresearch/faiss/wiki/Binary-indexes).

| Modelo | Configuração inicial |
|---|---|
| SVM | LinearSVR, C=1, epsilon=0, tol=0,001, max_iter=5.000 |
| KNN | 25 vizinhos, pesos inversos à distância, métrica euclidiana exata |
| Bagging | 20 árvores, profundidade 8, folha mínima 100, 70% com reposição |
| Pasting | 20 árvores, profundidade 8, folha mínima 100, 70% sem reposição |
| Random Forest | 30 árvores, profundidade 12, folha mínima 100, max_features=0,8 |
| Boosting | GradientBoosting, 60 estágios, profundidade 2, folha mínima 100, learning_rate=0,1 |
| Stacking | Linear + árvore de profundidade 12; Ridge combinador; três dobras internas com pipelines próprios |

As escolhas iniciais foram registradas antes da comparação nacional. SVM linear limita
o custo frente a kernels não lineares; limites de profundidade e folha restringem a
complexidade das árvores; bagging e pasting diferem apenas na reposição. Os parâmetros
não foram escolhidos pelo teste nem ajustados para favorecer um resultado observado.

O KNN compacto iniciou junto a uma família de árvores. Após concluir Pasting e observar
5.177 MiB de memória disponível, a execução passou a admitir três modelos concorrentes,
ainda dentro do checkpoint 1, com limite de dois threads por modelo. As métricas continuam usando exatamente as mesmas dobras
e participantes. Os tempos são os tempos de parede observados sob esse compartilhamento
de recursos; não devem ser interpretados como benchmark isolado de velocidade. Registro:
`recursos.json`. Ao encerrar o Checkpoint 1, os checkpoints 2–7 ainda não haviam iniciado.

## Retomada após interrupções

Os processos foram interrompidos após SVM/Bagging completos, uma dobra de Pasting e
parte das previsões da primeira dobra do KNN. O estado anterior foi preservado com hashes
em `antes-retomada-2026-11-06.zip`. A dobra de Pasting foi recuperada dos resultados reais
persistidos. As previsões antigas do KNN que existiam apenas em memória precisam ser
recalculadas; elas não foram apresentadas como resultados concluídos.

Agora cada dobra concluída tem um registro atômico com métricas e erros por grupo.
O KNN salva cada bloco de 2.048 previsões reais, com IDs, hash e contexto de treinamento.
Não são gravadas linhas para previsões ainda inexistentes. A retomada confere esses
registros, reutiliza o que foi concluído e calcula apenas os blocos faltantes. A trava
do sistema operacional impede dois processos de escreverem na mesma comparação.

```bash
.venv/bin/python -u scripts/executar_checkpoint1.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-1-2026-11-06 --resume
```

Verificação executada: 10.000 participantes reais de treino e 512 de validação, com
interrupção do gerador após dois blocos de 128. A retomada reutilizou dois blocos e
calculou os outros dois; diferença máxima frente à predição contínua: zero. Evidência:
`validacao_retomada_blocos.json`. Essa verificação técnica não substitui a comparação nacional.

Os tempos de execuções retomadas incluem os ajustes e blocos persistidos, além da
retomada atual. Trabalho perdido antes da implantação dos checkpoints, ou interrompido
antes de ser registrado, não entra nesses tempos. Os blocos individuais permanecem
locais em `predicoes_parciais/`; os resultados científicos agregados são versionáveis.

## Checkpoint 5: coleção visual concluída

Foram organizadas 17 figuras (PNG 300 dpi e SVG), 14 tabelas e uma galeria HTML local.
O histograma usa todos os participantes do desenvolvimento; o gráfico adicional de
resíduos usa todas as previsões persistidas do Stacking. Não houve novos treinamentos
ou avaliação do teste. A coleção cobre a comparação dos sete, o trio, buscas, curvas,
PCA, baseline, variantes e erros por grupos.
[Relatório e reprodução](checkpoint-5-resultados.md). O artigo foi concluído posteriormente no Checkpoint 6.

## Checkpoint 6: artigo e fonte original validados

Os ZIPs fornecidos em Downloads foram movidos para `dados/raw/`, conferidos por CRC
e hashes. O CSV normalizado reproduz integralmente os 79 Parquets existentes. O
complemento de redação permanece preservado, sem uso como preditor. O artigo inclui
os resultados finais, autores informados, referências e discussão crítica, em dez
páginas renderizadas e conferidas. [Relatório, arquivos e reprodução](checkpoint-6-resultados.md).
O Checkpoint 7 foi desenvolvido posteriormente, com roteiro sem slides conforme o novo pedido.

## Checkpoint 7: roteiro, LaTeX e conferência final

O pedido atual dispensa slides. Foram preparados o roteiro oral, o acompanhamento
e uma versão LaTeX do artigo, com PDFs compilados localmente e pacote Overleaf.
A revisão confirmou 54 avaliações iniciais/variantes, 180 avaliações de busca,
45 pontos de curvas iniciais e 45 finais; cinco modelos no teste reservado.
A suíte de software existente teve 81 testes aprovados. Ensaio, apresentação e AVA
permanecem externos à entrega local. [Relatório final](checkpoint-7-resultados.md).
