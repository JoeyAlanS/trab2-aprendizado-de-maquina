# Estimativa da Nota de Ciências da Natureza no ENEM 2023 a partir do Perfil dos Participantes: Uma Abordagem Reproduzível de Aprendizado de Máquina

**Autores:** Equipe de Ciência de Dados  
**Vínculo:** Unidade II — Aprendizado de Máquina | Projeto Aplicado  
**Alvo Numérico Atribuído:** `NU_NOTA_CN` (Ciências da Natureza e suas Tecnologias)  
**Repositório do Projeto:** [https://github.com/joey/trab2-aprendizado-de-maquina](https://github.com/joey/trab2-aprendizado-de-maquina)  
**Data de Conclusão:** Outubro de 2026  

---

## Resumo

Este artigo investiga em que medida o perfil socioeconômico, escolar e demográfico dos participantes permite estimar o desempenho na prova de Ciências da Natureza e suas Tecnologias (`NU_NOTA_CN`) no Exame Nacional do Ensino Médio (ENEM) de 2023. Utilizou-se a base de dados nacional integral divulgada pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep), composta por 3.933.955 registros e 76 variáveis originais. A população elegível à modelagem supervisionada reuniu 2.692.427 participantes com nota observada na referida área, preservando-se treineiros, todas as faixas etárias e as 16.547 notas zero verificadas. O protocolo experimental adotou particionamento estático aleatório (80% desenvolvimento, $n=2.153.941$; 20% teste reservado, $n=538.486$, semente fixa 42) e validação cruzada em 3 dobras no conjunto de desenvolvimento. Implementou-se um *pipeline* rígido contra vazamento de informação (*data leakage*), no qual toda imputação, padronização e codificação categórica foram ajustadas exclusivamente dentro dos dados de treino de cada dobra. Foram avaliadas 11 famílias de regressores: Baseline pela média, Regressão Linear sem regularização, Ridge, LinearSVR, Árvore de Decisão, KNN, Bagging, Pasting, Random Forest, HistGradientBoosting e Stacking. Investigou-se engenharia de atributos (3 novas variáveis compostas), seleção de features, redução de dimensionalidade por PCA ($\ge 80\%$ de variância explicada), estratégia de balanceamento por ponderação inversa das frequências de notas, busca de hiperparâmetros com $\ge 10$ configurações nos três melhores modelos e curva de aprendizado em 5 frações progressivas de treino (10% a 100%). O modelo final (*HistGradientBoosting* otimizado) alcançou no teste reservado um $\text{RMSE} = 75,84$, $\text{MAE} = 55,08$ e $R^2 = 0,2562$, superando o Baseline ($\text{RMSE} = 87,94$, $R^2 = -0,0000$) e a Regressão Linear ($\text{RMSE} = 76,51$, $R^2 = 0,2431$). A curva de aprendizado demonstrou estabilidade assintótica a partir de 50% dos dados e um hiato treino-validação de apenas 0,03 pontos, descartando sobreajuste (*overfitting*). Conclui-se que os atributos de perfil impõem um teto estrutural de explicação ($\approx 25,6\%$ da variância), sendo a variância residual decorrente de dimensões não mensuradas nos questionários tabulares (qualidade pedagógica escolar, dedicação individual de estudo e fatores socioemocionais no dia da prova).

**Palavras-chave:** ENEM 2023; Ciências da Natureza; Aprendizado de Máquina; Regressão; Avaliação Sem Vazamento; Curva de Aprendizado.

---

## Abstract

This paper investigates to what extent participants' socioeconomic, school, and demographic profiles predict performance on the Natural Sciences exam (`NU_NOTA_CN`) in the 2023 Brazilian National High School Exam (ENEM). The study leverages the full national dataset published by Inep, comprising 3,933,955 rows and 76 original variables. The supervised population consists of 2,692,427 candidates with observed scores in the target domain, preserving high school trainees, all age groups, and 16,547 verified zero scores. The experimental protocol enforces an 80/20 train-test partition ($n=2,153,941$ development; $n=538,486$ test; seed 42) and 3-fold cross-validation on development. Strict data leakage prevention guarantees that all imputations, scalers, and categorical encoders are fitted solely on training folds. Eleven regression families were systematically evaluated: Mean Baseline, Ordinary Least Squares, Ridge, LinearSVR, Decision Trees, KNN, Bagging, Pasting, Random Forest, HistGradientBoosting, and Stacking. Furthermore, we conducted feature engineering (3 composite domain features), supervised feature selection, PCA dimensionality reduction ($\ge 80\%$ variance), regression balancing via sample weighting, extensive hyperparameter tuning on top-3 models, and a 5-point learning curve. The final tuned model (*HistGradientBoosting*) achieved on the unseen test set an $\text{RMSE} = 75.84$, $\text{MAE} = 55.08$, and $R^2 = 0.2562$, substantially outperforming the mean baseline ($\text{RMSE} = 87.94$) and unregularized linear regression ($\text{RMSE} = 76.51$). Learning curves revealed asymptotic convergence beyond 50% sample size with a negligible train-val gap (0.03 points), refuting overfitting. We conclude that demographic and socioeconomic features encounter an empirical ceiling around 25.6% explained variance, leaving remaining score disparities to unobserved pedagogical, cognitive, and emotional factors.

**Keywords:** ENEM 2023; Natural Sciences; Machine Learning; Regression; Leakage-Free Protocol; Learning Curves.

---

## 1. Introdução e Contextualização

O Exame Nacional do Ensino Médio (ENEM) constitui o principal mecanismo de acesso à educação superior pública e privada no Brasil, sendo amplamente utilizado pelo Sistema de Seleção Unificada (Sisu), pelo Programa Universidade para Todos (Prouni) e pelo Fundo de Financiamento Estudantil (Fies). Compreender os determinantes do desempenho nas provas do ENEM é um desafio fundamental para a formulação e avaliação de políticas públicas de equidade educacional (INEP, 2024).

Em Ciência de Dados e Aprendizado de Máquina, a literatura frequentemente explora microdados educacionais para predição de desempenho. No entanto, muitos estudos pecam pela ocorrência de vazamento de dados (*data leakage*), pelo uso de recortes amostrais arbitrários de conveniência que distorcem a representatividade nacional, ou por interpretações inadequadas que atribuem causalidade a correlações observacionais ou supõem que algoritmos mais complexos necessariamente eliminariam todo o erro de predição (HASTIE; TIBSHIRANI; FRIEDMAN, 2009; SCIKIT-LEARN, 2024).

Neste trabalho, aborda-se a seguinte questão de pesquisa: **em que medida o perfil socioeconômico, escolar e demográfico permite estimar a nota de Ciências da Natureza e suas Tecnologias (`NU_NOTA_CN`) no ENEM 2023?**

O objetivo geral consiste em construir um *pipeline* metodológico integral e rigorosamente reproduzível, comparando o desempenho de onze famílias de regressores, avaliando técnicas de redução de dimensionalidade (PCA), balanceamento na regressão, busca de hiperparâmetros e diagnóstico de subajuste (*underfitting*) via curvas de aprendizado. Ressalta-se que o foco reside na transparência dos métodos, na análise meticulosa dos erros residuais e na discussão dos limites estruturais dos dados tabulares de perfil.

---

## 2. Metodologia

### 2.1 Dados, População Elegível e Rastreabilidade

Utilizou-se o arquivo nacional completo dos microdados do ENEM 2023, obtido no portal oficial de dados abertos do Inep. O arquivo `MICRODADOS_ENEM_2023.csv` totaliza 3.933.955 registros brutos e 76 colunas, com integridade criptográfica verificada via SHA-256 (`c8b1fae0a97b6ac826d950d16696efa3d89c133b0165128aadd2997c2315b666`).

A unidade de observação é o participante individual. Para a tarefa de regressão supervisionada, definiu-se a população elegível como todos os candidatos que obtiveram nota observada no componente `NU_NOTA_CN`, perfazendo 2.692.427 participantes. Os 1.241.528 participantes sem nota em Ciências da Natureza (em sua grande maioria decorrentes de ausência ou eliminação no primeiro ou segundo dia de provas) foram contabilizados no diagnóstico da fonte, mas devidamente excluídos da modelagem preditiva, sem qualquer imputação arbitrária de notas ausentes.

Seguindo estritamente as diretrizes do edital, as 16.547 notas zero verificadas na população elegível foram rigorosamente mantidas. Participantes de todas as faixas etárias e treineiros (`IN_TREINEIRO = 1`) foram preservados.

A Tabela 1 sintetiza a caracterização volumétrica da base:

| Etapa / Condição | Quantidade de Registros | Percentual |
| :--- | :---: | :---: |
| Base Nacional Bruta (Inep 2023) | 3.933.955 | 100,00% |
| Alvo `NU_NOTA_CN` Ausente (mantidos no diagnóstico) | 1.241.528 | 31,56% |
| **População Elegível com `NU_NOTA_CN` Observada** | **2.692.427** | **68,44%** |
| Notas Zero Observadas na População Elegível | 16.547 | 0,61% |
| Partição de Desenvolvimento (80%, semente 42) | 2.153.941 | 54,75% (80,00% dos elegíveis) |
| Partição de Teste Reservado (20%, semente 42) | 538.486 | 13,69% (20,00% dos elegíveis) |
| Validação Dobra 0 / Dobra 1 / Dobra 2 (KFold) | 717.981 / 717.980 / 717.980 | 33,33% cada no desenvolvimento |

### 2.2 Prevenção de Vazamento de Informação (*Data Leakage*)

Para garantir que os modelos operem estritamente sob as informações contextuais disponíveis a priori pelo perfil do candidato, impuseram-se barreiras de prevenção de vazamento:
1. **Exclusão de Resultados do Exame:** Foram excluídas da matriz de entrada $X$ todas as notas das demais áreas (`NU_NOTA_MT`, `NU_NOTA_CH`, `NU_NOTA_LC`, `NU_NOTA_REDACAO`), notas de competências da redação, vetores de respostas e gabaritos (`TX_RESPOSTAS_*`, `TX_GABARITO_*`) e códigos de prova.
2. **Exclusão de Variáveis Administrativas Posteriores:** Campos de presença (`TP_PRESENCA_*`) e situação da redação (`TP_STATUS_REDACAO`) não foram utilizados como preditores, pois revelam o comparecimento aos dias de aplicação.
3. **Controle de Identificadores:** `NU_INSCRICAO` foi empregado exclusivamente para particionamento e auditoria; `NU_ANO` é constante nesta edição e foi descartado.
4. **Isolamento no Pipeline:** Todas as transformações de dados — imputação pela mediana de atributos contínuos, codificação categórica *one-hot* com tratamento de categorias não vistas e padronização — foram encapsuladas em objetos `sklearn.pipeline.Pipeline`, sendo ajustadas (`fit`) unicamente no conjunto de treinamento de cada dobra e aplicadas (`transform`) na validação e no teste.

### 2.3 Representação Inicial e Engenharia de Features

A representação inicial contou com 40 variáveis candidatas: a variável numérica `Q005` (número de moradores na residência) e 39 variáveis categóricas (abrangendo dados demográficos, trajetória escolar, UF de realização da prova, opção de língua estrangeira e as questões socioeconômicas `Q001` a `Q025`).

Em atendimento ao requisito de engenharia de atributos (Seção 4 e 6 do edital), criaram-se três variáveis com justificativas pedagógicas e contextuais explícitas:
1. **Renda Familiar Per Capita Estimada (`RENDA_PER_CAPITA`):** Calculada dividindo-se o valor monetário do ponto médio do intervalo da faixa de renda familiar (`Q006`) pelo número de moradores no domicílio (`Q005`). Participantes sem renda declarada recebem zero; para denominadores nulos ou ausentes, imputa-se 1.
2. **Índice de Acesso Digital Doméstico (`ACESSO_DIGITAL`):** Variável ordinal combinando a disponibilidade de computadores (`Q024`: de 0 para nenhum a 4 para quatro ou mais) com a posse de acesso à internet (`Q025`: 0 para não, 1 para sim), refletindo a infraestrutura tecnológica disponível para estudo extraclasse.
3. **Composição da Escolaridade Parental (`ESCOLARIDADE_PAIS`):** Escala que consolida os níveis educacionais do pai (`Q001`) e da mãe (`Q002`), mapeando o capital cultural e a escolaridade acumulada no ambiente doméstico (categorizando desconhecimento como nível neutro intermediário).

Adicionalmente, aplicou-se seleção supervisionada de atributos via teste univariado de regressão linear (`SelectPercentile` mantendo os 75% atributos com maior valor $F$).

### 2.4 Redução de Dimensionalidade (PCA)

A análise de componentes principais (*Principal Component Analysis* - PCA) foi ajustada exclusivamente após o tratamento das variáveis contínuas e a expansão *one-hot* dos atributos categóricos (gerando 110 dimensões binárias e contínuas). Avaliou-se a variância explicada acumulada em função do número de componentes, identificando-se o limiar mínimo de 80% de variância amostral exigido pelo edital.

O PCA foi avaliado acoplado a dois regressores distintos: **Ridge** e **Árvore de Decisão**, comparando-se seu impacto preditivo contra as versões sem redução dimensional.

### 2.5 Estratégia de Balanceamento na Regressão

Na regressão contínua, faixas extremas de notas (candidatos com notas $< 400$ ou $> 700$) apresentam frequência relativamente baixa, o que induz os modelos treinados por erro quadrático a concentrar seus ajustes na região central da distribuição (em torno de 450 a 550 pontos).

Para investigar esse comportamento, testou-se uma estratégia de ponderação amostral (*sample weighting*) no treinamento das dobras: atribuíram-se pesos inversamente proporcionais à densidade empírica da faixa de nota observada do candidato. A validação e o teste mantiveram a distribuição e as métricas sem ponderação, permitindo mensurar se a redução do erro nas caudas justifica eventuais perdas na região central.

### 2.6 Catálogo de Regressores e Otimização de Hiperparâmetros

Avaliou-se o catálogo completo de 11 modelos:
- **Baseline:** `DummyRegressor(strategy='mean')`
- **Linear:** `LinearRegression()` sem regularização
- **Ridge:** `Ridge(alpha=1.0)`
- **LinearSVR:** `LinearSVR(C=1.0, epsilon=0.1, max_iter=5000)`
- **Árvore de Decisão:** `DecisionTreeRegressor(max_depth=12, min_samples_leaf=100)`
- **KNN:** `KNeighborsRegressor(n_neighbors=25, weights='distance')`
- **Bagging:** `BaggingRegressor(estimator=tree, n_estimators=20, bootstrap=True)`
- **Pasting:** `BaggingRegressor(estimator=tree, n_estimators=20, bootstrap=False, max_samples=0.7)`
- **Random Forest:** `RandomForestRegressor(n_estimators=30, max_depth=12, max_features=0.8)`
- **Boosting:** `HistGradientBoostingRegressor(learning_rate=0.1, max_iter=100, max_leaf_nodes=31)`
- **Stacking:** `StackingRegressor` combinando previsões fora da dobra (*out-of-fold*) de Regressão Linear e Árvore de Decisão, com meta-estimador Ridge.

A partir do desempenho médio do RMSE nas 3 dobras, selecionaram-se os três melhores regressores de famílias distintas (**HistGradientBoosting**, **Random Forest** e **Ridge**) para busca sistemática de hiperparâmetros (`GridSearchCV` e `RandomizedSearchCV`), explorando $\ge 10$ configurações válidas por estimador.

### 2.7 Curva de Aprendizado e Protocolo de Avaliação Final

Para o modelo final escolhido, gerou-se obrigatoriamente a curva de aprendizado avaliando cinco tamanhos de partição de treino dentro de cada dobra: 10% ($n=143.596$), 25% ($n=358.990$), 50% ($n=717.980$), 75% ($n=1.076.970$) e 100% ($n=1.435.961$). Toda a sequência de pré-processamento foi reajustada para cada fração, mantendo a validação da dobra intacta ($n=717.980$).

Somente após fixada e congelada a solução no desenvolvimento, realizou-se a avaliação única e definitiva no conjunto de teste reservado ($n=538.486$), confrontando o Baseline, a Regressão Linear sem regularização e o Modelo Final.

### 2.8 Hipóteses de Aprofundamento

Para atender ao critério de aprofundamento investigativo (Seção 6 e 9 do edital), formularam-se duas hipóteses adicionais:
- **Hipótese 1 (Ablação de Blocos de Informação):** Avaliar em que medida o bloco estritamente socioeconômico (`Q001` a `Q025`) contribui para o poder preditivo quando comparado ao bloco de contexto escolar e demográfico (sexo, idade, cor, tipo de escola, UF). Mensura-se a variação no RMSE ao retirar cada bloco isoladamente.
- **Hipótese 2 (Parcimônia e Simplificação Estrutural):** Avaliar se um modelo regularizado alimentado com um conjunto compacto de apenas 10 atributos de maior relevância preserva pelo menos 98% da capacidade preditiva ($R^2$) do modelo completo, viabilizando uma redução drástica no tempo de processamento e na complexidade operacional.

---

## 3. Resultados

### 3.1 Tabela Comparativa Consolidada

A Tabela 2 consolida os resultados de todos os experimentos conduzidos no projeto. Apresentam-se as métricas de validação cruzada em 3 dobras no conjunto de desenvolvimento (média e desvio padrão, divisor $N$ com $\text{ddof}=0$), bem como os resultados finais no conjunto de teste reservado ($n=538.486$).

**Tabela 2:** Comparativo geral de desempenho preditivo e tempo computacional.

| Modelo / Configuração Experimental | Conjunto Avaliado | RMSE (média ± DP) | MAE (média ± DP) | $R^2$ (média ± DP) | Tempo Total (s) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Média do Treino)** | Validação CV (3 dobras) | $87,92 \pm 0,08$ | $66,24 \pm 0,04$ | $-0,0000 \pm 0,0000$ | 0,09 |
| **Regressão Linear (sem regularização)** | Validação CV (3 dobras) | $76,48 \pm 0,05$ | $55,62 \pm 0,04$ | $0,2432 \pm 0,0005$ | 118,26 |
| **Ridge ($\alpha = 1,0$)** | Validação CV (3 dobras) | $76,48 \pm 0,05$ | $55,62 \pm 0,04$ | $0,2433 \pm 0,0005$ | 89,33 |
| **LinearSVR** | Validação CV (3 dobras) | $76,55 \pm 0,06$ | $55,51 \pm 0,04$ | $0,2418 \pm 0,0006$ | 312,40 |
| **Árvore de Decisão (prof. 12)** | Validação CV (3 dobras) | $77,17 \pm 0,04$ | $56,29 \pm 0,02$ | $0,2297 \pm 0,0005$ | 556,22 |
| **KNN ($k=25$, ponderado)** | Validação CV (3 dobras) | $78,62 \pm 0,07$ | $57,14 \pm 0,05$ | $0,2012 \pm 0,0008$ | 1.420,50 |
| **Bagging (20 árvores, com reposição)** | Validação CV (3 dobras) | $76,85 \pm 0,05$ | $55,98 \pm 0,03$ | $0,2359 \pm 0,0005$ | 840,10 |
| **Pasting (20 árvores, sem reposição)** | Validação CV (3 dobras) | $76,88 \pm 0,05$ | $56,01 \pm 0,03$ | $0,2352 \pm 0,0005$ | 815,30 |
| **Random Forest (30 árvores, prof. 12)** | Validação CV (3 dobras) | $76,24 \pm 0,04$ | $55,41 \pm 0,03$ | $0,2480 \pm 0,0004$ | 1.120,40 |
| **HistGradientBoosting (default)** | Validação CV (3 dobras) | $75,98 \pm 0,04$ | $55,20 \pm 0,03$ | $0,2531 \pm 0,0004$ | 245,80 |
| **Stacking (Linear + Árvore $\to$ Ridge)** | Validação CV (3 dobras) | $76,46 \pm 0,05$ | $55,60 \pm 0,04$ | $0,2436 \pm 0,0005$ | 780,20 |
| *Com Engenharia de Features (3 novas)* | Validação CV (3 dobras) | $76,42 \pm 0,05$ | $55,57 \pm 0,04$ | $0,2444 \pm 0,0005$ | 98,40 |
| *Seleção de Atributos (SelectPercentile 75%)* | Validação CV (3 dobras) | $76,44 \pm 0,05$ | $55,59 \pm 0,04$ | $0,2440 \pm 0,0005$ | 92,10 |
| *PCA em Ridge ($k=38$ comp., 80,2% var)* | Validação CV (3 dobras) | $77,12 \pm 0,05$ | $56,12 \pm 0,04$ | $0,2305 \pm 0,0005$ | 64,20 |
| *PCA em Árvore ($k=38$ comp., 80,2% var)* | Validação CV (3 dobras) | $78,05 \pm 0,06$ | $57,01 \pm 0,05$ | $0,2118 \pm 0,0006$ | 185,30 |
| *Balanceamento por Pesos Amostrais* | Validação CV (3 dobras) | $77,89 \pm 0,06$ | $57,21 \pm 0,05$ | $0,2151 \pm 0,0006$ | 95,10 |
| **Ridge Otimizado ($\alpha = 10,0$)** | Validação CV (3 dobras) | $76,48 \pm 0,05$ | $55,62 \pm 0,04$ | $0,2433 \pm 0,0005$ | 185,40 |
| **Random Forest Otimizado ($n=100$)** | Validação CV (3 dobras) | $76,05 \pm 0,04$ | $55,24 \pm 0,03$ | $0,2518 \pm 0,0004$ | 3.420,00 |
| **HistGradientBoosting Otimizado (Solução)** | Validação CV (3 dobras) | **$75,82 \pm 0,04$** | **$55,06 \pm 0,03$** | **$0,2563 \pm 0,0004$** | 480,20 |
| *H1: Ablação Bloco Socioeconômico* | Validação CV (3 dobras) | $81,42 \pm 0,06$ | $60,12 \pm 0,05$ | $0,1425 \pm 0,0006$ | 42,10 |
| *H1: Ablação Bloco Demográfico/Escolar* | Validação CV (3 dobras) | $77,85 \pm 0,06$ | $56,89 \pm 0,04$ | $0,2158 \pm 0,0005$ | 58,40 |
| *H2: Modelo Parcimonioso (10 features)* | Validação CV (3 dobras) | $76,71 \pm 0,05$ | $55,81 \pm 0,04$ | $0,2387 \pm 0,0005$ | 22,30 |
| **Baseline (Média)** | **Teste Reservado ($n=538.486$)** | **87,94** | **66,25** | **-0,0000** | 0,05 |
| **Regressão Linear (sem regularização)** | **Teste Reservado ($n=538.486$)** | **76,51** | **55,65** | **0,2431** | 42,10 |
| **Modelo Final (HistGradientBoosting Otimizado)**| **Teste Reservado ($n=538.486$)** | **75,84** | **55,08** | **0,2562** | 18,50 |

---

### 3.2 Análise das Evidências Visuais Obrigatórias

#### Figura 1: Distribuição da Nota Alvo no Desenvolvimento
A Figura 1 apresenta o histograma detalhado de `NU_NOTA_CN` no conjunto de desenvolvimento ($n=2.153.941$). A distribuição aproxima-se de uma normal unimodal levemente assimétrica à direita, com média de 495,77 pontos, mediana de 493,90 pontos e desvio padrão amostral de 87,92 pontos. Destaca-se a preservação integral das 13.236 notas zero observadas (0,61% dos candidatos elegíveis no desenvolvimento). A distinção entre ausência de prova (excluída do supervisionado) e nota zero (resultado empírico avaliado) orientou a integridade de todas as métricas.

![Figura 1: Distribuição da nota de Ciências da Natureza](/home/joey/Documentos/GitHub/trab2-aprendizado-de-maquina/resultados/figuras/distribuicao_nota_cn.png)

#### Figura 2: Comparação de Modelos no Desenvolvimento e Busca nos Top 3
A Figura 2 ilustra o comportamento do erro quadrático médio (RMSE) nas três dobras para os modelos obrigatórios e os ajustes de hiperparâmetros. Observa-se que todos os modelos supervisionados superam a média de forma contundente (redução de $\approx 11$ a $12$ pontos de RMSE). O *HistGradientBoosting* otimizado obteve o menor erro médio ($75,82 \pm 0,04$), seguido pela *Random Forest* otimizada ($76,05 \pm 0,04$) e pelo *Ridge* ($76,48 \pm 0,05$). O ganho absoluto obtido com ensembles não lineares frente ao modelo linear simples foi modesto ($\approx 0,66$ ponto de RMSE), sinalizando que o sinal preditivo contido nos dados é essencialmente linear e aditivo.

![Figura 2: Comparação de Modelos e Busca de Hiperparâmetros](/home/joey/Documentos/GitHub/trab2-aprendizado-de-maquina/resultados/figuras/comparacao_modelos_busca.png)

#### Figura 3: Variância Explicada Acumulada do PCA
A Figura 3 demonstra a evolução da variância acumulada pelo método de PCA sobre os 110 atributos numéricos e binarizados. A curva atinge 80,2% da variância amostral com $k=38$ componentes principais (redução de 65,5% do espaço dimensional). Ao projetar o modelo *Ridge* sobre essas 38 componentes, o RMSE elevou-se sutilmente de 76,48 para 77,12 (+0,64 ponto), comprovando que uma representação comprimida preserva a quase totalidade do poder explicativo linear. No entanto, para a Árvore de Decisão, o PCA aumentou o erro em +0,88 ponto, uma vez que as componentes contínuas ortogonais rotacionadas dificultam os particionamentos ortogonais nos eixos originais.

![Figura 3: Variância Explicada Acumulada do PCA](/home/joey/Documentos/GitHub/trab2-aprendizado-de-maquina/resultados/figuras/pca_variancia_acumulada.png)

#### Figura 4: Curva de Aprendizado do Modelo Final
A Figura 4 retrata o diagnóstico definitivo do ajuste estrutural nas frações de 10%, 25%, 50%, 75% e 100% de dados de treinamento. As bandas de variância entre as dobras são extremamente estreitas. O gráfico evidencia dois fatos matemáticos cruciais:
1. **Ausência de Sobreajuste (*Overfitting*):** Em 100% dos dados, o RMSE de treino é 75,79 e o de validação é 75,82, revelando uma diferença ínfima de apenas $\Delta = 0,03$ pontos.
2. **Convergência Assintótica:** As curvas de treino e validação convergem e atingem um patamar a partir de 50% dos dados ($n \approx 718.000$). Adicionar centenas de milhares de candidatos não reduz substancialmente o erro, confirmando que o RMSE residual de $\approx 75,8$ pontos não se deve a escassez de dados, mas sim a um erro irredutível intrínseco aos preditores disponíveis.

![Figura 4: Curva de Aprendizado do Modelo Final](/home/joey/Documentos/GitHub/trab2-aprendizado-de-maquina/resultados/figuras/curva_aprendizado.png)

#### Figura 5: Notas Observadas vs Previstas e Gráfico de Resíduos no Teste
Avaliando o modelo final nos 538.486 participantes do teste reservado, a Figura 5(a) plota a densidade bidimensional de notas observadas versus previstas com a diagonal ideal ($y = \hat{y}$), enquanto a Figura 5(b) expõe os resíduos ($e = y - \hat{y}$). É notório o fenômeno da regressão à média: as notas previstas concentram-se no intervalo de 360 a 690 pontos. Participantes que obtiveram notas extremas superiores ($> 750$) têm notas subestimadas pelo modelo, enquanto aqueles com notas muito baixas ou zero têm notas superestimadas, gerando os resíduos negativos severos visíveis na base do gráfico.

![Figura 5: Observado vs Previsto e Resíduos no Teste](/home/joey/Documentos/GitHub/trab2-aprendizado-de-maquina/resultados/figuras/observado_vs_previsto_residuos.png)

#### Figura 6: Análise de Erros por Faixa de Nota e Grupos Sociodemográficos
A Figura 6(a) decompõe o RMSE por faixa de nota observada: na região central (400 a 600 pontos, onde reside mais de 80% da amostra), o RMSE varia entre 54,1 e 58,7 pontos. Por outro lado, nas notas $< 400$ (que abrigam as notas zero), o RMSE sobe para 104,2 pontos, e para notas $\ge 700$, para 98,4 pontos. A Figura 6(b) analisa o erro por tipo de escola e faixas de renda: candidatos de escolas privadas apresentam RMSE maior ($82,4$ pontos, $n=44.356$) do que candidatos de escolas públicas ($73,8$ pontos, $n=166.655$), reflexo da maior heterogeneidade de trajetórias e dispersão intrínseca de notas no segmento privado.

![Figura 6: Erros por Faixa de Nota e Grupos](/home/joey/Documentos/GitHub/trab2-aprendizado-de-maquina/resultados/figuras/erros_faixa_e_grupos.png)

---

## 4. Discussão

### 4.1 Subajuste Estrutural vs. Sobreajuste

O diagnóstico empírico refuta qualquer hipótese de sobreajuste (*overfitting*): a concordância quase perfeita entre os erros de treino e teste e a estabilização da curva de aprendizado confirmam a generalização perfeita dos padrões aprendidos. 

Por outro lado, o valor de $R^2 \approx 0,256$ não deve ser interpretado levianamente como "mau funcionamento do algoritmo". Trata-se de um **subajuste estrutural decorrente da ausência de variáveis latentes essenciais**. O questionário socioeconômico do ENEM capta aspectos estruturais e patrimoniais da família do candidato (renda, posse de bens, escolaridade dos pais), mas é completamente omisso quanto a determinantes pedagógicos diretos:
- Carga horária líquida dedicada aos estudos ao longo do ensino médio;
- Metodologia de ensino, infraestrutura de laboratórios de ciências e formação do corpo docente;
- Nível de engajamento individual, motivação vocacional e hábitos de leitura;
- Fatores emocionais e fisiológicos circunstanciais (ansiedade, qualidade do sono, estresse no dia do exame);
- Comportamento de chute e adivinhação em itens de múltipla escolha sob Teoria de Resposta ao Item (TRI).

Portanto, cerca de 74,4% da variância das notas de Ciências da Natureza permanece associada à heterogeneidade individual e escolar não documentada nas variáveis cadastrais.

### 4.2 Ausência de Causalidade

As associações observadas entre nível de renda, posse de computador, escolaridade materna e nota de Ciências da Natureza têm caráter estritamente observacional e correlacional. Seria cientificamente incorreto e desprovido de rigor inferir relações causais — por exemplo, presumir que a simples concessão material de um computador elevaria mecanicamente a nota de um candidato em determinado número de pontos (PEARL, 2009). A posse de recursos digitais atua como um marcador indireto (*proxy*) de um complexo arranjo socioeconômico e cultural favorável que historicamente acompanha o desenvolvimento cognitivo e as oportunidades de aprendizagem.

### 4.3 Complexidade Algorítmica versus Parcimônia

A comparação entre a Regressão Linear sem regularização ($\text{RMSE} = 76,51$) e o modelo vencedor *HistGradientBoosting* ($\text{RMSE} = 75,84$) revela um ganho incremental modesto de apenas 0,67 ponto de nota (menos de 0,9% de melhoria relativa). Em contrapartida, modelos como *Random Forest* demandaram mais de 3.400 segundos de processamento e dezenas de gigabytes de memória operacional, enquanto o modelo *Ridge* executou em 89 segundos.

Esse achado corrobora a Hipótese de Aprofundamento 2: o modelo parcimonioso baseado em 10 variáveis selecionadas reteve 98,1% do $R^2$ com uma fração do custo computacional. Em aplicações de políticas públicas ou triagem educacional em larga escala, a interpretabilidade e o baixo custo de modelos lineares regularizados justificam plenamente sua adoção em detrimento de modelos *black-box* computacionalmente proibitivos.

### 4.4 Impactos do Balanceamento na Regressão

A tentativa de balancear a distribuição das notas via ponderação amostral de faixas raras evidenciou um clássico *trade-off* estatístico: embora tenha atenuado o erro médio em candidatos das caudas extremas ($<400$ e $>700$), provocou uma elevação substancial no RMSE geral (de 76,48 para 77,89 pontos). Como a densidade de candidatos é majoritariamente concentrada na faixa central, distorcer a função de perda em favor das caudas prejudica a predição para mais de 80% da população estudantil.

---

## 5. Conclusão

Este estudo investigou os limites e as potencialidades da previsão da nota de Ciências da Natureza no ENEM 2023 com base nos microdados nacionais do Inep.

As principais conclusões da pesquisa são:
1. **Poder Preditivo Realista:** O perfil socioeconômico, escolar e demográfico permite estimar a nota de Ciências da Natureza com um erro médio absoluto ($\text{MAE}$) em torno de 55,08 pontos e um coeficiente de determinação $R^2 \approx 0,2562$.
2. **Primazia das Condições Socioeconômicas:** Conforme atestado pela análise de ablação (Hipótese 1), o bloco socioeconômico familiar (especialmente renda familiar per capita e escolaridade dos pais) é o principal responsável pela capacidade explicativa dos modelos; sua supressão faz o erro quadrático médio saltar substancialmente.
3. **Parcimônia:** Modelos lineares regularizados aproximam-se muito da precisão de algoritmos de *boosting* e florestas aleatórias com uma fração ínfima do tempo de execução, recomendando-se seu uso para aplicações com restrição de recursos.
4. **Implicações Sociais:** Modelos preditivos de notas a partir do perfil não devem ser utilizados de forma determinística ou punitiva para rotular participantes ou escolas. A ampla variância não explicada ($\approx 74,4\%$) atesta que trajetórias individuais, dedicação e iniciativas educacionais de qualidade superam as condicionantes socioeconômicas de origem.

---

## Referências

BRASIL. Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (Inep). **Microdados do Enem 2023**. Brasília: Inep, 2024. Disponível em: <https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem>. Acesso em: 21 out. 2026.

HASTIE, Trevor; TIBSHIRANI, Robert; FRIEDMAN, Jerome. **The Elements of Statistical Learning**: Data Mining, Inference, and Prediction. 2. ed. New York: Springer, 2009.

INEP. **Relatório Pedagógico do Exame Nacional do Ensino Médio - Edição 2023**. Brasília: Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira, 2024.

LUNDBERG, Scott M.; LEE, Su-In. A unified approach to interpreting model predictions. In: **Advances in Neural Information Processing Systems (NeurIPS 2017)**, v. 30, 2017.

PEARL, Judea. **Causality**: Models, Reasoning, and Inference. 2. ed. Cambridge: Cambridge University Press, 2009.

PEDREGOSA, Fabian et al. Scikit-learn: Machine Learning in Python. **Journal of Machine Learning Research**, v. 12, p. 2825-2830, 2011.

SCIKIT-LEARN DEVELOPERS. **User Guide and Common Pitfalls in Machine Learning Evaluation**. Versão 1.9.1. Disponível em: <https://scikit-learn.org/stable/>. Acesso em: 23 out. 2026.

UNIVERSIDADE DE FORTALEZA. Biblioteca Central. **Guia de Normalização de Trabalhos Acadêmicos da Universidade de Fortaleza segundo as Normas da ABNT**. Fortaleza: Unifor, 2024.
