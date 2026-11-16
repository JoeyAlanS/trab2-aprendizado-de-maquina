# Apresentação ENEM 2023: roteiro de 20 slides

Duração planejada: 12 minutos, a confirmar em ensaio. Joey apresenta slides 1–10 (6 minutos); Paulo apresenta slides 11–20 (6 minutos). As falas são o roteiro principal. Os aprofundamentos servem para estudar e responder perguntas, sem precisar lê-los integralmente na apresentação.

## Slide 1 — Predição da nota de Ciências da Natureza
**Autor:** Joey · **Tempo planejado:** 15s

**Fala sugerida**
Comparamos modelos para estimar a nota de Ciências da Natureza usando o perfil dos participantes. Todos os resultados científicos desta apresentação usam microdados reais do ENEM 2023.

**Imagem / diagrama**
Capa com identidade visual azul-clara, título do ENEM e escopo de dez regressores. A média é uma referência adicional.

**Aprofundamento para perguntas**


**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** Código e dados reais do projeto.

## Slide 2 — Pergunta de pesquisa e objetivos
**Autor:** Joey · **Tempo planejado:** 25s

**Fala sugerida**
A saída é uma nota contínua, então o problema é de regressão. Queremos comparar os algoritmos com uma metodologia comum e entender onde os erros aumentam. As relações observadas não demonstram que renda ou escola causem uma nota.

**Imagem / diagrama**
Pergunta em destaque e três blocos com tarefa, comparação e análise.

**Aprofundamento para perguntas**


**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** Código e dados reais do projeto.

## Slide 3 — População e divisão dos dados
**Autor:** Joey · **Tempo planejado:** 40s

**Fala sugerida**
A base original tem quase quatro milhões de participantes. Para aprender e avaliar uma previsão, precisamos conhecer a nota real, então usamos os que têm o alvo observado. Nota ausente não significa zero. Os elegíveis foram divididos em desenvolvimento e teste.

**Imagem / diagrama**
Fluxo da população original aos elegíveis e dois ramos: desenvolvimento e teste. Explique a diferença entre ausência e zero.

**Aprofundamento para perguntas**
Os ZIPs locais passaram por CRC. A comparação integral do CSV normalizado com 79 Parquets confirmou igualdade em 3.933.955 linhas e 76 colunas. O complemento de competências da redação foi preservado sem entrar como preditor. O histograma da galeria usa apenas o desenvolvimento e contém 13.236 zeros.

**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** Código e dados reais do projeto.

## Slide 4 — 40 atributos originais de perfil
**Autor:** Joey · **Tempo planejado:** 40s

**Fala sugerida**
Os quarenta atributos representam o perfil demográfico, o histórico escolar e o questionário socioeconômico. Esta tabela traz exemplos reais. Q005 é a única entrada numérica original. Renda e escolaridade entram como categorias. O identificador serve para controlar os conjuntos, sem entrar no modelo.

**Imagem / diagrama**
Tabela de nome, significado e transformação. A lista integral fica nas notas para consulta.

**Aprofundamento para perguntas**
Lista integral dos 40 atributos, conforme a configuração:
Q005, TP_FAIXA_ETARIA, TP_SEXO, TP_ESTADO_CIVIL, TP_COR_RACA, TP_NACIONALIDADE, TP_ST_CONCLUSAO, TP_ANO_CONCLUIU, TP_ESCOLA, TP_ENSINO, IN_TREINEIRO, TP_DEPENDENCIA_ADM_ESC, TP_LOCALIZACAO_ESC, TP_SIT_FUNC_ESC, SG_UF_PROVA, TP_LINGUA, Q001, Q002, Q003, Q004, Q006, Q007, Q008, Q009, Q010, Q011, Q012, Q013, Q014, Q015, Q016, Q017, Q018, Q019, Q020, Q021, Q022, Q023, Q024, Q025.
Grupos: demográficos (5), escolares (8), localização/língua (2) e 24 respostas categóricas do questionário, além de Q005. Não confundir códigos de desconhecimento previstos no dicionário com valores ausentes.

**Trechos exatos de código**
```python
configs/ciencias_natureza.toml, linhas 23–35:
# A lista efetiva será confrontada com o dicionário oficial antes de modelar.
[features]
numeric = ["Q005"]
categorical = [
  "TP_FAIXA_ETARIA", "TP_SEXO", "TP_ESTADO_CIVIL", "TP_COR_RACA", "TP_NACIONALIDADE",
  "TP_ST_CONCLUSAO", "TP_ANO_CONCLUIU", "TP_ESCOLA", "TP_ENSINO", "IN_TREINEIRO",
  "TP_DEPENDENCIA_ADM_ESC", "TP_LOCALIZACAO_ESC", "TP_SIT_FUNC_ESC", "SG_UF_PROVA",
  "TP_LINGUA", "Q001", "Q002", "Q003", "Q004", "Q006", "Q007", "Q008", "Q009",
  "Q010", "Q011", "Q012", "Q013", "Q014", "Q015", "Q016", "Q017", "Q018",
  "Q019", "Q020", "Q021", "Q022", "Q023", "Q024", "Q025",
]
```

**Fonte:** Código e dados reais do projeto.

## Slide 5 — Pré-processamento e prevenção de vazamento
**Autor:** Joey · **Tempo planejado:** 45s

**Fala sugerida**
Cada etapa aprende somente na parte de treino da rodada. Q005 recebe mediana quando está ausente e é padronizada. As categorias recebem indicadores zero ou um, como neste exemplo didático. Ausências têm uma categoria própria, preservando os códigos oficiais de desconhecimento.

**Imagem / diagrama**
Fluxo de preparação e tabela binária A/B/C. O exemplo é didático e não é um resultado experimental.

**Aprofundamento para perguntas**
SimpleImputer usa add_indicator=True e keep_empty_features=True no ramo numérico. Indicadores de ausência só surgem quando aplicáveis ao treino. StandardScaler vem depois da imputação. OneHotEncoder conserva categorias e ignora categorias inéditas, deixando zeros nos indicadores daquele atributo. Identificadores, presença, outras notas, respostas às provas, gabaritos e resultados da redação ficam fora dos preditores. Cada base do Stacking tem Pipeline próprio, inclusive nas dobras internas.

**Trechos exatos de código**
```python
src/enem_base/preprocessing.py, linhas 58–67:
                        (
                            "imputer",
                            SimpleImputer(
                                strategy=numeric_strategy,
                                add_indicator=True,
                                keep_empty_features=True,
                            ),
                        ),
                        ("scaler", StandardScaler()),
                    ]
```
```python
src/enem_base/preprocessing.py, linhas 81–91:
                        ),
                        (
                            "imputer",
                            SimpleImputer(
                                strategy="constant",
                                fill_value="__MISSING__",
                                keep_empty_features=True,
                            ),
                        ),
                        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
                    ]
```

**Fonte:** Código e dados reais do projeto.

## Slide 6 — Três dobras com o teste reservado
**Autor:** Joey · **Tempo planejado:** 45s

**Fala sugerida**
As letras são partes fixas dos dados de desenvolvimento. Primeiro treinamos com B e C e validamos em A. Depois usamos A e C para validar em B. Na terceira rodada usamos A e B para validar em C. Todos os algoritmos usam essas mesmas divisões.

**Imagem / diagrama**
Matriz A/B/C: uma célula de validação em cada linha e duas de treino. As três linhas representam rodadas, não três testes finais.

**Aprofundamento para perguntas**
A corresponde à dobra 0. Os treinos têm 1.435.960, 1.435.961 e 1.435.961 participantes. A semente 42 torna a divisão reproduzível com os mesmos dados e configuração; não garante transferência para outro ano. A validação orienta comparação e parâmetros. O teste ficou separado durante as escolhas. As receitas foram congeladas antes da avaliação final, já concluída e apresentada no slide 16.

**Trechos exatos de código**
```python
src/enem_base/splits.py, linhas 31–46:
    eligible = ids[observed.notna()].reset_index(drop=True)
    if len(eligible) < 5:
        raise ValueError("São necessários ao menos cinco registros elegíveis para três dobras.")
    development, test = train_test_split(np.arange(len(eligible)), test_size=0.2, random_state=42)
    partition = pd.DataFrame(
        {
            identifier: eligible,
            "partition": "test",
            "validation_fold": pd.Series(pd.NA, index=eligible.index, dtype="Int64"),
        }
    )
    partition.loc[development, "partition"] = "development"
    for fold, (_, validation) in enumerate(
        KFold(3, shuffle=True, random_state=42).split(development)
    ):
        partition.loc[development[validation], "validation_fold"] = fold
```

**Fonte:** Código e dados reais do projeto.

## Slide 7 — Sete famílias efetivamente avaliadas
**Autor:** Joey · **Tempo planejado:** 65s

**Fala sugerida**
Dez regressores foram treinados nas mesmas três dobras, além da média de referência. A tabela detalha o recorte de sete famílias; linear, Ridge e árvore isolada também foram avaliados. Bagging e Pasting diferem na reposição. Random Forest também sorteia atributos. Boosting constrói árvores em sequência. KNN usa perfis próximos e a SVM aprende uma fórmula linear. O Stacking combina dois modelos de base.

**Imagem / diagrama**
Comparação por mecanismo e configuração, mantendo os nomes das sete famílias separados.

**Aprofundamento para perguntas**
SVM: random_state=42, dual="auto", max_iter=5000, tol=0.001. C controla a penalização relativa dos erros, epsilon a margem de erro sem penalização e tol a tolerância do otimizador. A versão é linear, sem kernel RBF. KNN: ExactProfileKNeighborsRegressor, n_neighbors=25 e weights="distance". Quando aplicável, índice binário Faiss exaustivo mais distância numérica preserva a distância euclidiana, sem aproximação e sem amostragem da população. Bagging/Pasting usam max_samples=0.7 e bootstrap True/False. RF usa min_samples_leaf=100 e max_features=0.8. Boosting usa learning_rate=0.1. Esses limites controlam custo e complexidade, sem garantia de superioridade universal.

**Trechos exatos de código**
```python
src/enem_base/modeling.py, linhas 82–128:
    tree = DecisionTreeRegressor(max_depth=8, min_samples_leaf=100, random_state=42)
    catalog = {
        "baseline": DummyRegressor(strategy="mean"),
        "linear": pipeline(LinearRegression(tol=1e-6)),
        "ridge": pipeline(Ridge(alpha=1.0, solver="lsqr", tol=1e-5)),
        "svm": pipeline(LinearSVR(random_state=42, dual="auto", max_iter=5000, tol=1e-3)),
        "arvore": pipeline(
            DecisionTreeRegressor(max_depth=12, min_samples_leaf=100, random_state=42)
        ),
        "knn": pipeline(
            ExactProfileKNeighborsRegressor(n_neighbors=25, weights="distance", n_jobs=2)
        ),
        "bagging": pipeline(
            BaggingRegressor(
                estimator=tree,
                n_estimators=20,
                max_samples=0.7,
                bootstrap=True,
                random_state=42,
                n_jobs=2,
            )
        ),
        "pasting": pipeline(
            BaggingRegressor(
                estimator=tree,
                n_estimators=20,
                max_samples=0.7,
                bootstrap=False,
                random_state=42,
                n_jobs=2,
            )
        ),
        "random_forest": pipeline(
            RandomForestRegressor(
                n_estimators=30,
                max_depth=12,
                min_samples_leaf=100,
                max_features=0.8,
                random_state=42,
                n_jobs=2,
            )
        ),
        "boosting": pipeline(
            GradientBoostingRegressor(
                n_estimators=60, max_depth=2, min_samples_leaf=100, random_state=42
            )
        ),
```
```python
src/enem_base/neighbors.py, linhas 71–96:
    def kneighbors(self, X=None, n_neighbors=None, return_distance=True):
        check_is_fitted(self)
        if not self.binary_backend_:
            return super().kneighbors(
                dense_knn_input(X) if X is not None else None,
                n_neighbors=n_neighbors,
                return_distance=return_distance,
            )
        if X is None:
            raise ValueError("Forneça explicitamente as entradas para a consulta de vizinhos.")
        X = validate_data(self, X, accept_sparse="csr", reset=False)
        k = self.n_neighbors if n_neighbors is None else n_neighbors
        if not isinstance(k, (int, np.integer)) or not 0 < k <= self.n_samples_fit_:
            raise ValueError("Quantidade de vizinhos inválida.")
        numeric, packed = _pack(X)
        if numeric is None:
            raise ValueError("A validação contém valores não binários no bloco one-hot.")
        distances = np.empty((len(numeric), k), dtype=np.float64)
        indices = np.empty((len(numeric), k), dtype=np.int64)
        for start in range(0, len(numeric), 2048):
            stop = min(start + 2048, len(numeric))
            candidates_d, candidates_i = [], []
            for value, positions, index in self.indices_:
                count = min(k, len(positions))
                hamming, local = index.search(packed[start:stop], count)
                squared = hamming.astype(np.float64) + (numeric[start:stop, None] - value) ** 2
```

**Fonte:** Código e dados reais do projeto.

## Slide 8 — Stacking: duas bases e um combinador
**Autor:** Joey · **Tempo planejado:** 40s

**Fala sugerida**
Cada base tem sua própria preparação. As dobras internas produzem previsões para participantes que ficaram fora do treino daquela base. Essas duas previsões viram as entradas da Ridge, que aprende a combinação. Para novos participantes, as bases ajustadas produzem previsões e a Ridge combina as respostas.

**Imagem / diagrama**
Diagrama das duas bases, das previsões OOF e do combinador. O fluxo mostra o treinamento, não a soma simples de todas as famílias.

**Aprofundamento para perguntas**
As dobras internas do Stacking são distintas das externas usadas para comparar modelos. A Ridge é uma regressão linear com penalização L2: em geral desencoraja coeficientes grandes. O alpha define a força da penalização. LinearRegression e DecisionTreeRegressor são as bases reais. SVM e Random Forest não são bases deste Stacking. O ganho da busca de alpha foi de apenas cerca de 3,205×10^-8 ponto de RMSE.

**Trechos exatos de código**
```python
src/enem_base/modeling.py, linhas 130–136:
    # Cada base conserva o seu próprio Pipeline nas dobras internas do stacking.
    catalog["stacking"] = StackingRegressor(
        estimators=[("linear", clone(catalog["linear"])), ("arvore", clone(catalog["arvore"]))],
        final_estimator=Ridge(alpha=1.0),
        cv=KFold(3, shuffle=True, random_state=42),
        n_jobs=1,
    )
```

**Fonte:** Código e dados reais do projeto.

## Slide 9 — Métricas e modelos de referência
**Autor:** Joey · **Tempo planejado:** 25s

**Fala sugerida**
RMSE e MAE medem erro em pontos, e valores menores são melhores. R² compara o erro do modelo à variação em torno da média observada. O desvio entre dobras descreve variação, sem equivaler a intervalo de confiança. A média de treino é um baseline que não usa os atributos.

**Imagem / diagrama**
Três fórmulas acompanhadas de sua interpretação. Baseline e DP ficam em uma segunda faixa.

**Aprofundamento para perguntas**
Nas fórmulas, y é nota real, ŷ é previsão, n é quantidade de participantes e ȳ é a média observada do conjunto avaliado. DummyRegressor usa strategy="mean" do treinamento. Linear, Ridge e árvore usam atributos. O DP usa ddof=0. Os tempos são de parede observados, com recursos compartilhados; os tempos finais de ajuste não incluem predição. R² próximo de 0,25 não prova sozinho underfitting. Como o alvo é contínuo, são adequados resíduos e erros, não matriz de confusão.

**Trechos exatos de código**
```python
src/enem_base/modeling.py, linhas 140–156:
def regression_metrics(observed, predicted) -> dict:
    observed, predicted = np.asarray(observed, dtype=float), np.asarray(predicted, dtype=float)
    if (
        observed.shape != predicted.shape
        or observed.ndim != 1
        or not len(observed)
        or not np.isfinite(observed).all()
        or not np.isfinite(predicted).all()
    ):
        raise ValueError("Métricas exigem vetores finitos, não vazios e da mesma dimensão.")
    return {
        "rmse": float(root_mean_squared_error(observed, predicted)),
        "mae": float(mean_absolute_error(observed, predicted)),
        "r2": float(r2_score(observed, predicted))
        if len(observed) > 1 and np.var(observed)
        else None,
    }
```

**Fonte:** Código e dados reais do projeto.

## Slide 10 — Catálogo completo e seleção pelo RMSE
**Autor:** Joey · **Tempo planejado:** 20s

**Fala sugerida**
No catálogo completo, os menores RMSE médios foram Stacking (76,174516), Ridge (76,483610) e linear (76,483799). No recorte de sete famílias, o trio foi Stacking, SVM e Random Forest. Todos usam as mesmas dobras. As buscas cobriram a união dos dois trios, com cinco modelos. Stacking foi a solução selecionada no desenvolvimento e seguiu para o teste com as referências obrigatórias e os dois modelos adicionais.

**Imagem / diagrama**
Gráfico original 18_comparacao_completa.png: RMSE médio e DP dos dez regressores e da média nas três dobras. Menor é melhor. Ridge e linear empatam visualmente pelo arredondamento, mas Ridge teve RMSE ligeiramente menor antes dele.

**Aprofundamento para perguntas**
Bagging: 77,484; Gradient Boosting: 77,589; Pasting: 77,609; KNN: 77,896. As diferenças são observadas, sem teste de significância. MAE e R² confirmaram a ordem do trio. No catálogo ampliado, incluindo referências, os três menores RMSE iniciais foram Stacking, Ridge e linear. Isso motivou a busca em cinco modelos sem substituir o trio solicitado. Não foi identificada uma causa única para cada diferença entre algoritmos.

**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** resultados/comparacao_modelos.csv e resultados/figuras/18_comparacao_completa.png

## Slide 11 — Engenharia de atributos

ESCOLARIDADE_PAIS_MAX exige os dois níveis conhecidos. Se algum responsável tiver escolaridade desconhecida, a feature derivada fica ausente.
**Autor:** Paulo · **Tempo planejado:** 35s

**Fala sugerida**
Criamos três atributos usando respostas existentes. Computadores por morador procura representar disponibilidade relativa. O acesso digital soma presença de computador e internet. A escolaridade máxima usa os níveis informados pelos responsáveis. A engenharia teve um ganho pequeno no Ridge.

**Imagem / diagrama**
Três definições e comparação dos RMSE, sem inflar a diferença pequena.

**Aprofundamento para perguntas**
Q024 é mapeada de A–E para 0–4; quatro ou mais usa o mínimo quatro, não uma contagem exata. Q005 deve estar entre 1 e 20 para o denominador; inválidos ficam ausentes. ACESSO_DIGITAL soma indicador de computador maior que zero e internet (Q025 A=0/B=1), ficando em 0–2 quando as duas informações são conhecidas. Não é uma medida social validada. Escolaridade de Q001/Q002 A–G é ordinal; código de desconhecimento não recebe nível fictício e np.maximum exige as duas respostas conhecidas. Imputação posterior aprende no treino.

**Trechos exatos de código**
```python
src/enem_base/variants.py, linhas 37–46:
        people = pd.to_numeric(X.Q005, errors="raise").astype(float)
        people = people.where(people.between(1, 20))
        computers = X.Q024.map(dict(zip("ABCDE", range(5), strict=True))).astype(float)
        internet = X.Q025.map({"A": 0.0, "B": 1.0}).astype(float)
        father = X.Q001.map(dict(zip("ABCDEFG", range(7), strict=True))).astype(float)
        mother = X.Q002.map(dict(zip("ABCDEFG", range(7), strict=True))).astype(float)
        result[DERIVED[0]] = computers / people
        result[DERIVED[1]] = computers.gt(0).astype(float).where(computers.notna()) + internet
        result[DERIVED[2]] = np.maximum(father, mother)
        return result
```

**Fonte:** Código e dados reais do projeto.

## Slide 12 — Seleção de atributos e PCA
**Autor:** Paulo · **Tempo planejado:** 35s

**Fala sugerida**
A seleção escolheu 75% das colunas transformadas pelo teste F de regressão. O PCA criou componentes para preservar pelo menos 80% da variância. Nenhuma dessas variantes melhorou os modelos nas configurações testadas. Variância preservada e capacidade preditiva são critérios diferentes.

**Imagem / diagrama**
Curva real de variância acumulada com o limiar de 80%. Bloco lateral distingue seleção e PCA.

**Aprofundamento para perguntas**
SelectPercentile(f_regression, percentile=75) foi aplicado depois da engenharia e codificação no treino. Ridge com seleção: 76,529, contra 76,484 originalmente. PCA foi aplicado a Ridge e árvore nas três dobras: seis ajustes, 45 componentes em cada um. Valores originais: Ridge 76,484, árvore 77,167. PCA centrado preserva a variância natural dos indicadores; Q005 já é padronizada. Os componentes são aprendidos apenas no treino. Seleção foi experimentada no Ridge; PCA foi avaliado em dois regressores. Não declarar seleção executada em dois regressores sem evidência.

**Trechos exatos de código**
```python
src/enem_base/variants.py, linhas 69–77:
        self.pca_ = PCA(svd_solver="covariance_eigh", random_state=42).fit(X)
        self.explained_variance_ratio_ = self.pca_.explained_variance_ratio_
        if not np.isfinite(self.explained_variance_ratio_).all():
            raise ValueError("PCA sem variância finita no treino.")
        self.n_components_ = min(
            int(np.searchsorted(np.cumsum(self.explained_variance_ratio_), self.variance)) + 1,
            len(self.explained_variance_ratio_),
        )
        self.n_features_in_ = X.shape[1]
```
```python
src/enem_base/variants.py, linhas 150–156:
        if engineered:
            estimator.steps.insert(0, ("features", ProfileFeatures()))
        if variant == "selected":
            estimator.steps.insert(-1, ("selection", SelectPercentile(f_regression, percentile=75)))
        if variant == "pca":
            estimator.steps.insert(-1, ("pca", VariancePCA()))
        if variant == "weighted":
```

**Fonte:** apresentacao/tabelas/pca_variancia.csv

## Slide 13 — Ponderação e duas ablações
**Autor:** Paulo · **Tempo planejado:** 35s

**Fala sugerida**
A ponderação deu mais peso às faixas de nota raras, mantendo o alvo numérico. Algumas faixas extremas melhoraram, mas o erro global aumentou bastante. Nas ablações, retirar o questionário ou a UF aumentou o erro. Mantivemos esses resultados negativos na análise.

**Imagem / diagrama**
Tabela com referência, hipótese testada, RMSE e interpretação, mantendo visíveis os resultados negativos.

**Aprofundamento para perguntas**
Faixas de largura igual e pesos inversos foram aprendidos no treino, em dez faixas. Validação e teste conservam suas distribuições. Não houve sobreamostragem sintética. O grupo sem socioeconômicas retira as variáveis cujo nome começa por Q, incluindo Q005. São duas hipóteses adicionais, comparadas ao mesmo Ridge e às mesmas dobras. O resultado não identifica efeitos causais.

**Trechos exatos de código**
```python
src/enem_base/variants.py, linhas 104–116:
    def __init__(self, estimator, n_bins=10):
        self.estimator = estimator
        self.n_bins = n_bins

    def fit(self, X, y):
        y = np.asarray(y, dtype=float)
        if self.n_bins < 2 or not np.isfinite(y).all() or np.ptp(y) == 0:
            raise ValueError("Ponderação exige pelo menos duas faixas e alvo variável finito.")
        self.bin_edges_ = np.linspace(y.min(), y.max(), self.n_bins + 1)
        labels = np.clip(np.searchsorted(self.bin_edges_, y, side="right") - 1, 0, self.n_bins - 1)
        self.bin_counts_ = np.bincount(labels, minlength=self.n_bins)
        weights = len(y) / (np.count_nonzero(self.bin_counts_) * self.bin_counts_[labels])
        self.estimator_ = clone(self.estimator).fit(X, y, regressor__sample_weight=weights)
```
```python
src/enem_base/variants.py, linhas 128–140:
        raise ValueError(f"Representação desconhecida: {variant}")
    if variant == "without_socio":
        config = replace(
            config,
            numeric=tuple(n for n in config.numeric if not n.startswith("Q")),
            categorical=tuple(n for n in config.categorical if not n.startswith("Q")),
        )
    elif variant == "without_uf":
        config = replace(
            config, categorical=tuple(n for n in config.categorical if n != "SG_UF_PROVA")
        )
    engineered = variant in {"engineered", "selected"}
    if engineered:
```

**Fonte:** apresentacao/tabelas/comparacoes_cv_completas.csv

## Slide 14 — Busca de hiperparâmetros
**Autor:** Paulo · **Tempo planejado:** 35s

**Fala sugerida**
O GridSearchCV compara configurações pelas mesmas três dobras e pelo RMSE. Foram doze configurações em cada um de cinco modelos. Os ganhos encontrados foram pequenos. O teste final não foi usado para decidir os parâmetros.

**Imagem / diagrama**
Destaque das 180 avaliações e tabela dos parâmetros. Os ganhos exatos estão no guia e nas figuras da galeria.

**Aprofundamento para perguntas**
PredefinedSplit utiliza as dobras persistidas. Alpha: [0.001,0.003,0.01,0.03,0.1,0.3,1,3,10,30,100,1000]. SVM usa max_iter=50000 na busca. Stacking selecionou alpha=1000 com ganho de 3,205×10^-8; Ridge selecionou alpha=10 com ganho de 0,0000376; linear selecionou tol=10^-5 com ganho de 0,000205. SVM e RF mantiveram as receitas iniciais. O limiar 10^-8 para manter parâmetros iniciais é tolerância numérica, não significância. A linear de referência do teste usa tol original 10^-6.

**Trechos exatos de código**
```python
src/enem_base/tuning.py, linhas 26–40:
MODELS = ("svm", "linear", "ridge", "random_forest", "stacking")
ALPHAS = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 1000.0]
SPACES = {
    "svm": {"regressor__C": [0.01, 0.1, 1.0, 10.0], "regressor__epsilon": [0.0, 0.1, 1.0]},
    "linear": {
        "regressor__fit_intercept": [True, False],
        "regressor__tol": [1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8],
    },
    "ridge": {"regressor__alpha": ALPHAS},
    "random_forest": {
        "regressor__max_depth": [8, 12],
        "regressor__n_estimators": [5, 10, 15, 20, 25, 30],
    },
    "stacking": {"final_estimator__alpha": ALPHAS},
}
```

**Fonte:** apresentacao/tabelas/antes_depois.csv

## Slide 15 — Curvas de aprendizado dos três modelos
**Autor:** Paulo · **Tempo planejado:** 45s

**Fala sugerida**
Cada curva compara treino e validação em cinco tamanhos de treino. As diferenças finais são pequenas, sem sinal de sobreajuste acentuado nas condições avaliadas. Isso não prova ausência absoluta de sobreajuste nem desempenho em outro ano.

**Imagem / diagrama**
Curvas reais, legenda de treino/validação e faixas de DP. Explique erro versus quantidade de dados.

**Aprofundamento para perguntas**
Frações cumulativas: 10%,25%,50%,75%,100% do treino de cada dobra, com validação fixa, média e DP de três dobras. O menor treino já tem aproximadamente 143.596 participantes. Overfitting costuma aparecer como erro de treino muito menor que validação; underfitting descreve capacidade insuficiente para capturar os padrões úteis. R² baixo isoladamente não comprova subajuste, pois há informação não observada. As curvas finais incluem reutilização compatível: 30 pontos idênticos às configurações iniciais, 12 com bases e novo combinador, três de treino completo vindos das buscas. Não são 45 treinamentos inteiramente novos.

**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** apresentacao/tabelas/curvas_resumo.csv

## Slide 16 — Teste final em 538.486 participantes
**Autor:** Paulo · **Tempo planejado:** 45s

**Fala sugerida**
Esses são os cinco modelos avaliados no mesmo teste reservado. O Stacking apresentou o menor RMSE observado e reduziu o erro em 13,38% em relação à média. A regressão linear ficou próxima, com menor complexidade. Não concluímos que a diferença seja estatisticamente significativa.

**Imagem / diagrama**
Tabela completa das métricas reais, com destaque para o Stacking e a proximidade da linear.

**Aprofundamento para perguntas**
Todos foram reajustados em 2.153.941 participantes de desenvolvimento, com parâmetros congelados. KNN, Bagging, Pasting, Boosting, Ridge e árvore isolada não foram avaliados no teste final deste protocolo. Os tempos de ajuste foram 1.250,63 s no Stacking e 36,41 s na linear, sem predição. Os tempos observados não são benchmark isolado. O baseline teve R² ligeiramente negativo, próximo de zero. A diferença RMSE 0,327 é arredondada de 76,516794 menos 76,189590. Não houve nova seleção após consultar o teste.

**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** apresentacao/tabelas/comparacao_teste.csv

## Slide 17 — Erros concentrados nos extremos
**Autor:** Paulo · **Tempo planejado:** 40s

**Fala sugerida**
No gráfico da esquerda, a diagonal representa previsão perfeita. As previsões ficam mais concentradas no centro da escala. Por isso, os modelos tendem a superestimar notas baixas e subestimar notas altas. À direita, os erros por faixa tornam esse limite visível.

**Imagem / diagrama**
Dois gráficos reais: observado/previsto e erro por faixa. A tabela explicita as contagens dos grupos citados.

**Aprofundamento para perguntas**
O gráfico observado/previsto usa todas as previsões em células, não amostra. No Stacking, resíduos médios observado menos previsto: -118,60 abaixo de 400 e +156,03 a partir de 700. As outras faixas têm n=200.516 em [500,600) e n=47.562 em [600,700). A distribuição de resíduos e o gráfico resíduos versus previsão estão na galeria; resíduo negativo indica superestimação. O erro global semelhante entre CV e teste não elimina essa estrutura nos extremos.

**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** apresentacao/tabelas/erros_grupos.csv

## Slide 18 — Análise por grupos de participantes
**Autor:** Paulo · **Tempo planejado:** 30s

**Fala sugerida**
O erro varia entre os tipos de escola. É necessário observar as contagens e as diferenças de composição. Esse gráfico mede erro de previsão, não a média das notas. Renda e UF de aplicação também foram examinadas, mas não isolam efeitos causais.

**Imagem / diagrama**
Gráfico real por tipo de escola com legendas e contagens explícitas ao lado.

**Aprofundamento para perguntas**
UF de aplicação pode diferir da residência. Renda Q006 é autodeclarada e as categorias seguem o dicionário oficial. Para as visualizações completas de UF e renda, use apresentacao/figuras/15_uf.svg e 16_renda.svg e a tabela erros_grupos.csv, que contém n por categoria. Não generalizar capacidade individual nem qualidade da escola ou UF a partir desses erros. Grupos de escola somam 538.486 participantes.

**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** apresentacao/tabelas/erros_grupos.csv

## Slide 19 — Limites e rastreabilidade
**Autor:** Paulo · **Tempo planejado:** 30s

**Fala sugerida**
A consistência observada vale para esta divisão do ENEM 2023. Não houve teste em outra edição nem inferência causal. O projeto preserva arquivos para reproduzir as comparações. Os testes de software verificam o código e são distintos dos experimentos científicos.

**Imagem / diagrama**
Duas colunas para limites e evidências. Separe claramente testes de código e validação dos modelos.

**Aprofundamento para perguntas**
A suíte teve 87 testes de software aprovados em Linux em 15/11/2026, nesta revisão. Não alegar Windows ou testes externos nesta apresentação. São 54 avaliações iniciais/variantes, 180 avaliações de busca, 45 pontos iniciais e 45 finais de curvas, cinco modelos no teste. Requisitos e entregas: artigo em LaTeX/PDF, acompanhamento, pitch e código com resultados. dados/splits contém partições locais; previsoes_teste.csv e modelos ajustados ficam locais e fora do Git. O GitHub contém código, métricas agregadas, figuras e manifestos. A limpeza retirou documentos de acompanhamento antigos; não afirmar que arquivos excluídos ainda estão publicados.

**Trechos exatos de código**
```python
src/enem_base/modeling.py, linhas 342–348:
                    with warnings.catch_warnings(record=True) as captured:
                        warnings.simplefilter("always")
                        if name == "baseline":
                            estimator.fit(np.zeros((len(train), 1)), y[train])
                            predicted = estimator.predict(np.zeros((len(validation), 1)))
                        else:
                            estimator.fit(x.iloc[train], y[train])
```

**Fonte:** Código e dados reais do projeto.

## Slide 20 — Conclusões e próximos passos
**Autor:** Paulo · **Tempo planejado:** 30s

**Fala sugerida**
A contribuição é uma comparação nacional com partições consistentes e resultados verificáveis, incluindo ideias que não melhoraram o desempenho. O Stacking venceu pelo critério observado, mas a proximidade da linear e os erros extremos pedem cautela. Outras edições e partições por grupos são próximos estudos, não testes já realizados.

**Imagem / diagrama**
Fecho com destaque tipográfico, conclusões e fontes. Propostas futuras são identificadas como não executadas.

**Aprofundamento para perguntas**
Fontes: Inep, Microdados do ENEM 2023 e dicionário; Pedregosa et al., Scikit-learn: Machine Learning in Python, JMLR 2011; Douze et al., The Faiss library, arXiv 2401.08281, 2024; documentação do scikit-learn utilizada no projeto. Referências completas em docs/artigo.md. Para perguntas, consultar o guia, a lista integral dos atributos e as 18 figuras originais do projeto. Demonstrar código nos slides 5 (pré-processamento), 6 (partições), 7 (modelos), 8 (Stacking), 11–14 (variantes/busca) e 19 (fit somente no treino).

**Trechos exatos de código**
Não é necessário neste slide.

**Fonte:** Código e dados reais do projeto.
