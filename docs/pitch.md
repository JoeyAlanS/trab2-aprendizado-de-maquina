# Roteiro e Slides do Pitch Presencial (10 a 15 Minutos)

**Projeto Aplicado | Unidade II — Aprendizado de Máquina com Dados do ENEM 2023**  
**Alvo Numérico:** `NU_NOTA_CN` (Ciências da Natureza e suas Tecnologias)  
**Entrega:** Apresentação Final com Slides Estruturados, Roteiro de Fala Equilibrado e Guia de Defesa  
**Repositório:** [https://github.com/joey/trab2-aprendizado-de-maquina](https://github.com/joey/trab2-aprendizado-de-maquina)  

---

## 1. Visão Geral e Estratégia da Apresentação

- **Duração Total:** 12 a 14 minutos (dentro do intervalo estrito de 10 a 15 minutos exigido pelo edital).
- **Formato:** 11 slides executivos, priorizando gráficos de alta resolução, tabelas de síntese e raciocínio científico.
- **Divisão da Equipe (4 Integrantes):**
  - **Integrante 1 (Slides 1 a 3 | ~3.5 min):** Contextualização, base nacional, elegibilidade, features e prevenção de vazamento.
  - **Integrante 2 (Slides 4 a 6 | ~3.5 min):** Engenharia de features, catálogo de modelos, PCA e balanceamento.
  - **Integrante 3 (Slides 7 a 9 | ~3.5 min):** Busca de hiperparâmetros, curva de aprendizado e diagnóstico de viés-variância.
  - **Integrante 4 (Slides 10 e 11 | ~3.0 min):** Avaliação no teste reservado, limites estruturais, ausência de causalidade e conclusão.
- **Sessão de Perguntas e Respostas:** Guia preparado para responder a questionamentos da banca avaliadora.

---

## 2. Estrutura dos Slides e Roteiro de Fala

---

### Slide 1: Título e Identificação da Pesquisa
- **Título:** Estimativa da Nota de Ciências da Natureza no ENEM 2023: Uma Investigação Reproduzível de Aprendizado de Máquina
- **Subtítulo:** Apresentação Final do Projeto Aplicado — Unidade II
- **Alvo:** `NU_NOTA_CN` | **Tema:** Ciências da Natureza e suas Tecnologias
- **Autores:** Integrante 1, Integrante 2, Integrante 3, Integrante 4
- **Instituição:** Universidade de Fortaleza (Unifor) | Ciência de Dados
- **Link do Repositório:** `github.com/joey/trab2-aprendizado-de-maquina`

> **Fala do Integrante 1 (~1 min):**  
> *"Boa tarde, professor e colegas. Hoje apresentamos os resultados finais do nosso projeto de regressão aplicada aos dados do ENEM 2023. Nosso desafio central foi responder com rigor científico: até que ponto o perfil socioeconômico, escolar e demográfico de um estudante é capaz de prever sua nota na prova de Ciências da Natureza? Em nosso repositório no GitHub, disponibilizamos todo o código, partições e relatórios auditáveis que fundamentam as conclusões que veremos a seguir."*

---

### Slide 2: A Base Nacional e a População Elegível
- **Fonte Integral Inep:** 3.933.955 inscrições nacionais no ENEM 2023 (processamento em lotes Parquet, hash SHA-256 verificado).
- **População Elegível:** 2.692.427 candidatos com nota observada em `NU_NOTA_CN` (sem imputar ausências nem filtrar por notas de outras provas).
- **Preservação de Zeros e Diversidade:** 16.547 notas zero observadas foram mantidas; treineiros e todas as faixas etárias incluídos.
- **Particionamento Sem Vazamento (Semente 42):**
  - 80% Desenvolvimento: **2.153.941** participantes (validação cruzada em 3 dobras fixas).
  - 20% Teste Reservado: **538.486** participantes (acessado uma única vez após congelamento da solução).
- **Elemento Visual:** Histograma de distribuição de notas do desenvolvimento (`distribuicao_nota_cn.png`), destacando média de 495,77 e o bloco de notas zero.

> **Fala do Integrante 1 (~1.2 min):**  
> *"Diferente de abordagens convencionais que recortam amostras de conveniência, nós trabalhamos com a totalidade da base nacional do Inep. Dos 3,93 milhões de registros, filtramos com transparência os 2,69 milhões com nota observada em Ciências da Natureza. Um ponto crítico de honestidade científica: não removemos as notas zero observadas — foram 13.236 no desenvolvimento —, pois elas refletem o resultado real de participantes presentes no exame. Dividimos a base em 80% para desenvolvimento e 20% para teste com semente fixa 42."*

---

### Slide 3: Prevenção Rígida de Vazamento (*Data Leakage*)
- **Blindagem do Conjunto de Entrada ($X$):**
  - Exclusão absoluta de notas de outras áreas (`MT`, `CH`, `LC`, `REDACAO`), competências e vetores de respostas/gabaritos.
  - Bloqueio de campos de presença (`TP_PRESENCA_*`) e status da redação (`TP_STATUS_REDACAO`).
- **Encapsulamento em Pipeline:**
  - Imputação numérica pela mediana do treino da dobra.
  - Codificação categórica *one-hot* com suporte a novas categorias.
  - Nenhuma informação da partição de validação ou de teste interferiu no treinamento.
- **Representação Inicial:** 40 variáveis candidatas (Q005 contínua e 39 categóricas).

> **Fala do Integrante 1 (~1.3 min):**  
> *"Para que as previsões fossem genuínas e justas, implementamos barreiras intransponíveis contra vazamento de dados. Não entra em $X$ nenhuma nota de outra área do ENEM, nenhum gabarito e nenhuma variável gerada após a prova, como dados de presença. O algoritmo opera estritamente com as informações que o estudante declarou na inscrição. Além disso, todas as transformações estatísticas foram ajustadas dentro de Pipelines do scikit-learn, garantindo isolamento total entre treino e validação em cada uma das três dobras."*

---

### Slide 4: Engenharia de Features e Seleção de Atributos
- **Criação de Três Novas Variáveis Contextuais:**
  1. `RENDA_PER_CAPITA`: Ponto médio da renda familiar (`Q006`) dividido por moradores (`Q005`).
  2. `ACESSO_DIGITAL`: Combinação ordinal de computador (`Q024`) e internet (`Q025`).
  3. `ESCOLARIDADE_PAIS`: Índice conjunto da escolaridade do pai (`Q001`) e da mãe (`Q002`).
- **Seleção de Atributos:** Seleção supervisionada univariada (`SelectPercentile` dos 75% atributos com maior $F$).
- **Impacto no Desempenho:**
  - Inclusão das features reduziu o RMSE de 76,48 para 76,42 pontos no Ridge.
  - Seleção eliminou categorias raras sem perda apreciável de acurácia, enxugando a representação.

> **Fala do Integrante 2 (~1.2 min):**  
> *"Passo a palavra para detalhar nossa engenharia de features. Criamos três atributos baseados em literatura educacional: a renda familiar per capita, um índice de acesso digital que combina computador e internet, e um indicador consolidado da escolaridade dos pais. Essas variáveis capturam interações de capital econômico e cultural, trazendo ganho interpretativo e reduzindo o erro de predição. Complementamos com seleção supervisionada para expurgar categorias residuais com ruído estatístico."*

---

### Slide 5: Catálogo de Modelos e Comparação Inicial
- **Catálogo Obrigatório Completo (11 famílias avaliadas nas mesmas 3 dobras):**
  - Baseline Dummy: RMSE $87,92 \pm 0,08$ | $R^2 = -0,0000$
  - Modelos Lineares (Linear e Ridge): RMSE $76,48 \pm 0,05$ | $R^2 = 0,2433$
  - Modelos Baseados em Árvores (Árvore, Bagging, Pasting): RMSE entre 76,85 e 77,17
  - SVM Linear: RMSE $76,55 \pm 0,06$ | KNN: RMSE $78,62 \pm 0,07$ (alto custo)
  - Ensembles Avançados (Random Forest e HistGradientBoosting): RMSE 76,24 e 75,98
  - Stacking (Linear + Árvore $\to$ Ridge): RMSE 76,46
- **Elemento Visual:** Gráfico comparativo de RMSE com barras de erro (`comparacao_modelos_busca.png`).

> **Fala do Integrante 2 (~1.3 min):**  
> *"Avaliamos onze famílias distintas de algoritmos sob as mesmas dobras de validação cruzada. Como esperado, todos os regressores superaram expressivamente o baseline pela média, com uma redução de cerca de 12 pontos no RMSE. O modelo HistGradientBoosting destacou-se com o menor erro inicial (75,98 pontos), seguido pela Random Forest e pelo Ridge. Notem que a diferença entre a regressão linear e os ensembles complexos é de menos de 1 ponto de nota, revelando que a relação dominante é essencialmente linear e aditiva."*

---

### Slide 6: Redução de Dimensionalidade (PCA) e Balanceamento
- **PCA ($\ge 80\%$ de Variância Explicada):**
  - Limiar de 80,2% atingido com **$k=38$ componentes principais** (redução de 65,5% da dimensão original de 110 colunas).
  - Em Ridge: RMSE aumentou sutilmente de 76,48 para 77,12 (+0,64 ponto), mostrando alta preservação de informação.
  - Na Árvore de Decisão: RMSE degradou para 78,05 (+0,88 ponto), pois a rotação contínua prejudica splits ortogonais.
- **Balanceamento na Regressão:**
  - Ponderação inversa de frequências de faixas de notas no treinamento da dobra.
  - *Resultado:* Reduziu o erro médio nas caudas ($<400$ e $>700$), mas aumentou o RMSE global de 76,48 para 77,89 pontos, prejudicando mais de 80% dos estudantes da região central.
- **Elemento Visual:** Curva de variância acumulada do PCA (`pca_variancia_acumulada.png`).

> **Fala do Integrante 2 (~1.0 min):**  
> *"No experimento de redução de dimensionalidade por PCA, mostramos que 38 componentes explicam mais de 80% da variância total. No Ridge, o erro subiu apenas 0,6 ponto, provando que é possível comprimir drasticamente os dados quase sem perder poder preditivo. Já na estratégia de balanceamento por ponderação, encontramos um importante trade-off: tentar melhorar a precisão nas notas raras aumentou o erro médio da população geral, já que a esmagadora maioria dos estudantes está concentrada em torno da nota média."*

---

### Slide 7: Busca de Hiperparâmetros nos Três Melhores Modelos
- **Metodologia:** `GridSearchCV` e `RandomizedSearchCV` com $\ge 10$ configurações em cada um dos três melhores regressores distintos.
- **Resultados Antes vs. Depois da Otimização:**
  1. **Ridge:** $\alpha = 1,0 \to \alpha = 10,0$ | RMSE de $76,484 \to 76,482$ (estabilização L2 de pesos).
  2. **Random Forest:** $n=30$, prof=12 $\to n=100$, prof=16 | RMSE de $76,24 \to 76,05$ (custo: 3.420 s).
  3. **HistGradientBoosting:** default $\to \text{lr}=0,08$, $\text{max\_iter}=150$, $\text{max\_leaf}=63$ | RMSE de **$75,98 \to 75,82$** (menor erro do projeto).
- **Decisão da Solução Final:** O **HistGradientBoosting Otimizado** foi eleito o modelo definitivo para a avaliação no teste.

> **Fala do Integrante 3 (~1.2 min):**  
> *"Passo a palavra para apresentar a fase de otimização. Realizamos buscas com mais de dez configurações válidas para cada um dos nossos três melhores estimadores. No Ridge, regularização L2 moderada estabilizou os coeficientes. Na Random Forest, elevar para 100 árvores reduziu o erro para 76,05 pontos, mas exigiu quase uma hora de processamento. O campeão foi o HistGradientBoosting com taxa de aprendizado 0,08 e 63 folhas por árvore, atingindo um RMSE de 75,82 pontos nas três dobras. Esse foi o modelo congelado como nossa solução final."*

---

### Slide 8: Curva de Aprendizado e Diagnóstico de Viés vs. Variância
- **Protocolo Obrigatório em 5 Pontos de Treino:** 10%, 25%, 50%, 75% e 100% dos dados da dobra de treinamento.
- **Evidências Visuais e Matemáticas:**
  - **Ausência Total de Sobreajuste (*Overfitting*):** Em 100% dos dados, Treino $= 75,79$ e Validação $= 75,82$ ($\Delta = 0,03$ pontos).
  - **Convergência Assintótica:** A partir de 50% dos dados ($n \approx 718.000$), a curva atinge um patamar horizontal.
  - **Diagnóstico Teórico:** Adicionar mais milhões de candidatos não diminuirá o erro. O erro de $\approx 75,8$ pontos é decorrente de **subajuste estrutural** — variância não mensurada nas variáveis cadastrais.
- **Elemento Visual:** Gráfico da curva de aprendizado com bandas de desvio padrão (`curva_aprendizado.png`).

> **Fala do Integrante 3 (~1.3 min):**  
> *"Este slide traz a evidência mais importante do trabalho: a curva de aprendizado do modelo final. O gráfico revela que as curvas de treino e validação convergem com um hiato de apenas 0,03 pontos em 100% dos dados. Isso descarta formalmente qualquer hipótese de sobreajuste. Mais ainda: a partir de 50% dos dados, a curva entra em um platô assintótico perfeito. Isso prova que nosso erro residual de cerca de 75 pontos não é falta de dados e não é falha do algoritmo; trata-se de um teto de informação imposto pelas próprias features de perfil."*

---

### Slide 9: Hipóteses de Aprofundamento (H1 e H2)
- **Hipótese 1 — Ablação de Blocos de Informação:**
  - Remoção do Bloco Socioeconômico (`Q001` a `Q025`): RMSE salta em **+4,94 pontos** (de 76,48 para 81,42; $R^2$ cai para 0,14).
  - Remoção do Bloco Demográfico/Escolar: RMSE aumenta apenas **+1,37 pontos** (para 77,85).
  - *Conclusão:* As condições econômicas e culturais familiares respondem pela esmagadora maioria do poder explicativo.
- **Hipótese 2 — Princípio da Parcimônia:**
  - Ridge com apenas 10 atributos de maior relevância: RMSE de **76,71** e $R^2 = 0,2387$.
  - Preserva **98,1%** do desempenho preditivo com apenas **25%** do tempo de execução e total transparência.

> **Fala do Integrante 3 (~1.0 min):**  
> *"Indo além do mínimo exigido, testamos duas hipóteses de aprofundamento. Na primeira, fizemos a ablação de blocos e constatamos que retirar o questionário socioeconômico destrói grande parte da capacidade do modelo, enquanto retirar os dados escolares tem impacto muito menor. Na segunda hipótese, mostramos que um modelo parcimonioso com apenas 10 variáveis atinge 98% da acurácia de modelos completos, economizando três quartos do tempo computacional. A simplicidade, muitas vezes, é a escolha mais elegante em produção."*

---

### Slide 10: Avaliação no Teste Reservado e Análise de Erros
- **Avaliação Única e Definitiva no Teste ($n=538.486$ participantes):**
  - **Baseline:** $\text{RMSE} = 87,94$ | $\text{MAE} = 66,25$ | $R^2 = -0,0000$
  - **Linear sem Regularização:** $\text{RMSE} = 76,51$ | $\text{MAE} = 55,65$ | $R^2 = 0,2431$
  - **Modelo Final (HistGradientBoosting):** $\text{RMSE} = \mathbf{75,84}$ | $\text{MAE} = \mathbf{55,08}$ | $R^2 = \mathbf{0,2562}$
- **Análise de Resíduos e Comportamento por Grupos:**
  - Efeito clássico de **regressão à média**: previsões concentradas entre 360 e 690 pontos.
  - Subestimação das notas $>750$ e superestimação de notas zero.
  - RMSE é menor em escolas públicas ($73,8$) do que em escolas privadas ($82,4$), refletindo maior dispersão de notas no ensino privado.
- **Elemento Visual:** Painéis duplos de Observado vs Previsto e Erros por Faixa/Grupo (`observado_vs_previsto_residuos.png` e `erros_faixa_e_grupos.png`).

> **Fala do Integrante 4 (~1.5 min):**  
> *"Assumo a palavra para os resultados finais no conjunto de teste de 538 mil participantes, que abrimos pela primeira vez após congelar a solução. O modelo final confirmou excelente generalização, atingindo RMSE de 75,84 e $R^2$ de 0,2562. O gráfico de resíduos evidencia o fenômeno de regressão à média: o modelo acerta com muita precisão no miolo da distribuição (onde o erro cai para 54 pontos), mas subestima os candidatos de desempenho excepcional acima de 750 pontos e erra nos participantes com nota zero. Além disso, o erro é maior nas escolas privadas devido à maior variabilidade interna de notas desse público."*

---

### Slide 11: Limites Estruturais, Ausência de Causalidade e Conclusões
- **O que a Ciência de Dados nos ensinou neste estudo:**
  1. **Teto Estrutural:** O perfil socioeconômico explica $\approx 25,6\%$ da variância das notas. Os $74,4\%$ restantes pertencem a fatores não mensurados nos microdados: qualidade pedagógica escolar, esforço individual de estudo, vocação, saúde mental e ansiedade no dia da prova.
  2. **Ausência de Causalidade:** As correlações observacionais jamais autorizam prescrever relações causais (ter computador é um marcador de condições socioeconômicas amplas, não garantia mágica de aprendizado).
  3. **Ética em Políticas Públicas:** Modelos preditivos de notas a partir do perfil não devem ser usados para rotular ou discriminar estudantes. A ampla margem de variabilidade não explicada prova que a dedicação e o mérito pedagógico rompem determinismos de origem.
- **Agradecimento:** Obrigado pela atenção! Aberto a perguntas da banca.

> **Fala do Integrante 4 (~1.5 min):**  
> *"Para concluir, nossa principal contribuição não foi apenas ajustar um bom algoritmo, mas demonstrar os limites éticos e estruturais dos dados. Um $R^2$ de 25% não é uma falha matemática; é a constatação de que o ser humano não é determinado exclusivamente pela sua renda ou pela cor da sua pele. Quase 75% da nota de Ciências da Natureza decorre de esforço pessoal, qualidade pedagógica dos professores e fatores emocionais que nenhum formulário de inscrição consegue capturar. Finalizamos nosso pitch reforçando que machine learning na educação deve servir para promover igualdade de oportunidades, nunca para etiquetar futuros. Muito obrigado e estamos à disposição para as perguntas da banca!"*

---

## 3. Guia de Defesa: Possíveis Perguntas da Banca e Respostas Preparadas

### Pergunta 1: Por que o $R^2$ ficou em apenas 0,256? Vocês não conseguiram um modelo melhor?
> **Resposta Preparada (Qualquer Integrante):**  
> *"Excelente pergunta. Esse $R^2$ em torno de 0,25 não reflete uma limitação do algoritmo, mas um limite estrutural da fonte de dados. Nossa curva de aprendizado comprovou que com 700 mil dados o modelo já atinge convergência assintótica com gap treino-validação de apenas 0,03 pontos. Isso prova que o modelo extraiu praticamente todo o sinal preditivo contido no perfil socioeconômico. A variância não explicada de 75% decorre de variáveis omitidas cruciais: horas de estudo extraclasse, qualidade da metodologia de ensino dos colégios, afinidade vocacional com biologia/física/química e aspectos emocionais durante a prova, que os microdados tabulares simplesmente não medem."*

### Pergunta 2: Por que vocês não excluíram as notas zero do treinamento?
> **Resposta Preparada:**  
> *"Nós seguimos rigorosamente as diretrizes da Seção 3 do edital. Nota zero no ENEM é um resultado empírico observado de um candidato presente, diferindo de uma nota ausente por falta. Excluir os zeros do treino criaria um viés de seleção artificial, descrevendo outra população. Como demonstrado na Seção 2 do edital e em nossos testes de balanceamento, um modelo treinado sem zeros continua tendo que prever notas de toda a população no teste, gerando distorções na função de perda."*

### Pergunta 3: Qual a vantagem prática do modelo linear regularizado (Ridge) frente ao HistGradientBoosting?
> **Resposta Preparada:**  
> *"Embora o HistGradientBoosting tenha vencido com o menor RMSE (75,84 vs 76,51 no teste), o ganho relativo foi de apenas 0,87% (menos de 0,7 ponto de nota). No entanto, o Ridge executa em uma fração do tempo (89 segundos contra centenas de segundos em busca) e oferece explicabilidade direta através dos pesos dos coeficientes de regressão. Em cenários reais de políticas públicas com escassez de recursos computacionais, o princípio da parcimônia indica que o Ridge é uma solução altamente competitiva e muito mais interpretável."*
