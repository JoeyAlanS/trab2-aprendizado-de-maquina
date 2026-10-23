# Ciências da Natureza - delimitação e plano da pesquisa

Tema definido pelo usuário em 21/10/2026: **Ciências da Natureza e suas Tecnologias**.
Alvo numérico: **NU_NOTA_CN**, no ENEM 2023. Nenhuma nota das demais áreas integra X.

## Problema e objetivo

**Pergunta:** em que medida o perfil socioeconômico, escolar e demográfico permite
estimar a nota de Ciências da Natureza dos participantes do ENEM 2023?

**Objetivo geral:** comparar modelos de regressão sobre o perfil tabular, avaliar
ganhos em relação à média do treino e analisar erros, custo e limites das previsões.

Objetivos específicos: caracterizar a base nacional e a disponibilidade da nota CN;
tratar os dados com rastreabilidade; comparar as representações e modelos exigidos;
investigar a contribuição de blocos de features; comunicar resultados com evidências.

Unidade de observação: participante da edição de 2023. O diagnóstico utiliza a fonte
nacional completa. A população supervisionada contém todos com NU_NOTA_CN observada,
inclusive zero, treineiros e todas as faixas etárias. Não imputar notas e não exigir
outras notas. Ausência do alvo é a exclusão supervisionada principal, a contabilizar.

## Hipóteses e experimentos

| Etapa | Hipótese ou comparação | Evidência prevista |
|---|---|---|
| Referência | O perfil tabular pode reduzir o erro em relação à média do treino | RMSE/MAE/R² nas mesmas três dobras |
| Representação | Features criadas e seleção podem alterar o erro ou reduzir o custo | Comparação originais/criadas/selecionadas |
| Redução | PCA pode preservar parte da informação com menor dimensão | Variância do treino e comparação em dois regressores |
| Balanceamento | Pesos ou reamostragem podem reduzir erros em faixas raras, com possíveis perdas gerais | Mesmo regressor, com/sem estratégia, distribuição original na validação |
| Aprofundamento 1 | A contribuição do bloco socioeconômico pode ser distinta da demográfica/escolar | Ablação de blocos nas mesmas dobras |
| Aprofundamento 2 | Uma representação/codificação mais simples pode manter desempenho com menor custo | RMSE, variação por dobra, tempo e dimensão |

As duas últimas hipóteses são propostas de aprofundamento, sem resultado antecipado.
Executar PCA ou seleção obrigatórios, isoladamente, não comprova aprofundamento.

## Representação inicial proposta

O contrato declara candidatas demográficas/escolares, UF de prova e Q001-Q025.
Q005 é candidata numérica (moradores); as demais alternativas são inicialmente
categóricas, preservando desconhecimento/não informação como alternativas próprias.
As colunas e alternativas foram confrontadas com o dicionário do pacote efetivamente
obtido em 21/10/2026. O extrato JSON cobre as 76 colunas, e o código valida as categorias
enumeradas do desenvolvimento antes do treinamento. A lista não foi escolhida pelo teste.
Detalhes e ressalvas em `dicionario_ciencias_natureza.md`.

UF de prova descreve o lugar da prova, não a residência. Município foi deixado de fora
da representação inicial para evitar alta cardinalidade sem justificativa específica;
essa escolha não restringe geograficamente participantes. As ausências escolares são
preservadas. Mediana numérica e categoria explícita de ausência são a representação
inicial de comparação, ajustadas somente no treino de cada dobra.

Propostas de features a especificar após conferir o dicionário: recursos digitais por
morador, composição da escolaridade dos responsáveis e combinação de acesso a recursos
digitais. Não aproximar renda por valores monetários nem assumir contagens exatas para
alternativas limitadas sem declarar limites, fórmulas e justificativa. Essas propostas
não são consideradas features implementadas nesta rodada inicial.

## Avaliação e execução incremental

80% desenvolvimento, 20% teste, semente 42. Três dobras embaralhadas no desenvolvimento,
persistidas uma vez. Imputação, one-hot, escala e qualquer etapa aprendida ficam dentro
do Pipeline. O stacking contém um Pipeline por modelo base nas dobras internas.

A primeira comparação executável contém baseline pela média, linear sem regularização,
Ridge e árvore. O catálogo também inclui LinearSVR, KNN, bagging, pasting, floresta,
boosting e stacking. **Disponibilidade no catálogo não significa treinamento concluído.**
O KNN exige especial cuidado com o custo de predição na base integral; medir e registrar
recursos, sem substituir a fonte por amostra de conveniência. Threads limitadas a duas
na execução inicial para controlar paralelismo e memória.

Depois de completar a comparação obrigatória, escolher três regressores distintos
pela CV e buscar pelo menos dez configurações válidas em cada um. A solução, faixas e
grupos são fixados pelo desenvolvimento. O teste permanece reservado até o final.

Métricas: RMSE principal, MAE e R² complementares, escala original, média/desvio das
três dobras (ddof=0, convenção explícita), tempos e tamanhos. Resíduo = observado −
previsto. A interpretação por grupo deve informar n e limitações. A previsão com dados
de perfil não determina a capacidade individual e não estabelece causalidade.

## Entregas e estado

O relatório de andamento com contagens, resultados executados e pendências será
registrado em `andamento_ciencias_natureza.md`. Artigo ABNT de até dez páginas, slides
de acompanhamento e pitch de 10-15 minutos exigem os resultados reais e participação
dos integrantes; não são declarados concluídos pela preparação do código.
Autores, matrícula/equipe e prazos do AVA continuam a preencher pela equipe.
