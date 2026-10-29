# Roteiro e Slides do Acompanhamento Obrigatório

**Projeto Aplicado | Unidade II — Aprendizado de Máquina com Dados do ENEM 2023**  
**Alvo Numérico:** `NU_NOTA_CN` (Ciências da Natureza e suas Tecnologias)  
**Entrega:** Apresentação de Andamento com Slides e Roteiro de Fala da Equipe  
**Repositório:** [https://github.com/joey/trab2-aprendizado-de-maquina](https://github.com/joey/trab2-aprendizado-de-maquina)  

---

## 1. Visão Geral da Apresentação

- **Tempo estimado:** 5 a 8 minutos.
- **Formato:** Apresentação de slides estruturados com gráficos e tabelas (sem exibição crua de código em terminal).
- **Participação da equipe:** Falas divididas equitativamente entre os integrantes (ex.: Integrante 1: Base e Problema; Integrante 2: Features e Prevenção de Vazamento; Integrante 3: Resultados Preliminares; Integrante 4: Próximos Passos e Dúvidas).
- **Status do Teste:** O conjunto de teste (20%) permanece estritamente reservado e intocado nesta etapa.

---

## 2. Estrutura dos Slides e Roteiro de Fala

---

### Slide 1: Abertura e Identificação do Projeto
- **Título:** Estimativa da Nota de Ciências da Natureza no ENEM 2023
- **Subtítulo:** Acompanhamento Obrigatório de Andamento — Aprendizado de Máquina (Unidade II)
- **Equipe:** Integrante 1, Integrante 2, Integrante 3, Integrante 4
- **Alvo Atribuído:** `NU_NOTA_CN` (Ciências da Natureza e suas Tecnologias)
- **Link do Repositório:** `github.com/joey/trab2-aprendizado-de-maquina`
- **Elementos Visuais:** Logomarca institucional Unifor, identificação clara do tema.

> **Fala do Integrante 1 (Abertura - ~1 min):**  
> *"Olá a todos, professor e colegas. Somos a equipe responsável pelo tema de Ciências da Natureza no ENEM 2023. Nosso objetivo central é investigar em que medida o perfil socioeconômico, demográfico e escolar dos estudantes permite prever sua nota na prova de Ciências da Natureza (`NU_NOTA_CN`). Hoje apresentamos o andamento do projeto, a caracterização da base nacional oficial, as decisões metodológicas de prevenção de vazamento e os resultados preliminares da nossa validação cruzada."*

---

### Slide 2: A Base Nacional Oficial e a População de Estudo
- **Fonte Oficial:** Inep / Microdados do ENEM 2023 (arquivo nacional completo, sem recortes de conveniência).
- **Volume Total:** 3.933.955 registros processados integralmente (checksum SHA-256 verificado).
- **Definição de Elegibilidade para Regressão:**
  - Registros com nota `NU_NOTA_CN` observada: **2.692.427** participantes (68,44%).
  - Registros sem nota (ausentes/eliminados): **1.241.528** (mantidos no diagnóstico, excluídos do treino/validação supervisionados).
  - Notas zero observadas: **16.547** participantes (0,61% dos elegíveis) preservados integralmente.
  - Treineiros e todas as faixas etárias mantidos na amostra.
- **Particionamento Rígido:**
  - 80% Desenvolvimento: **2.153.941** participantes (divididos em 3 dobras fixas de KFold, semente 42).
  - 20% Teste Reservado: **538.486** participantes (congelados para a avaliação final).
- **Elemento Visual:** Gráfico de distribuição da nota no desenvolvimento com média (495,77) e notas zero destacadas (`relatorio/images/distribuicao.png`).

> **Fala do Integrante 1 (Dados e Elegibilidade - ~1.5 min):**  
> *"Um compromisso central do nosso projeto foi a fidelidade à base nacional completa. Não utilizamos subamostragens arbitrárias. Processamos os 3,93 milhões de inscritos e identificamos 2,69 milhões de candidatos com nota de Ciências da Natureza. Diferenciamos com rigor ausência de prova (candidato faltante) de nota zero (candidato presente com desempenho nulo). Preservamos todos os 16.547 zeros e particionamos a base em 80% para desenvolvimento e 20% para teste com semente fixa 42, mantendo o teste intocado."*

---

### Slide 3: Features Candidatas e Prevenção de Vazamento (*Data Leakage*)
- **Variáveis Candidatas (40 colunas):**
  - Numérica: `Q005` (quantidade de pessoas residentes no domicílio).
  - Demográficas e Escolares (15 colunas): Faixa etária, sexo, cor/raça, estado civil, tipo de escola (`TP_ESCOLA`), modalidade de ensino, UF da prova.
  - Socioeconômicas (24 colunas): Questões `Q001` a `Q025` (escolaridade e profissão dos pais, renda familiar `Q006`, bens, internet e computadores).
- **Barreiras de Prevenção de Vazamento (Rigor Metodológico):**
  - **Zero Vazamento de Desempenho:** Nenhuma nota de outra área (`NU_NOTA_MT`, `NU_NOTA_CH`, etc.), notas da redação, respostas ou gabaritos entram em $X$.
  - **Variáveis Administrativas Bloqueadas:** Presença (`TP_PRESENCA_*`) e situação da redação (`TP_STATUS_REDACAO`) não são features preditivas.
  - **Pipeline Estrito:** Imputação pela mediana e codificação *one-hot* calculadas exclusivamente dentro do treino de cada dobra da validação cruzada.
- **Engenharia de Atributos Inicial:**
  - `RENDA_PER_CAPITA`: Ponto médio de `Q006` dividido por `Q005`.
  - `ACESSO_DIGITAL`: Score ordinal combinando computador (`Q024`) e internet (`Q025`).
  - `ESCOLARIDADE_PAIS`: Escala unificada do nível instrucional de pai e mãe.

> **Fala do Integrante 2 (Features e Pipeline - ~1.5 min):**  
> *"Para predizer a nota, utilizamos 40 atributos de perfil. O cuidado ético e técnico mais importante foi a blindagem contra vazamento de dados. Absolutamente nenhuma nota de outra prova ou gabarito entra no modelo; o algoritmo só enxerga o que uma escola ou governo saberia antes do aluno sentar para fazer o exame. Além disso, todas as transformações estatísticas foram encapsuladas em Pipelines do scikit-learn para garantir que dados da validação nunca interfiram no treinamento da dobra."*

---

### Slide 4: Resultados Preliminares da Validação Cruzada (3 Dobras)
- **Protocolo:** Validação Cruzada K-Fold ($K=3$, shuffle=True, semente 42) no conjunto de desenvolvimento completo ($n=2.153.941$).
- **Métricas:** RMSE (métrica principal), MAE e $R^2$, reportadas com média e desvio padrão amostral ($\text{ddof}=0$).

**Tabela de Resultados Preliminares:**
| Modelo Avaliado | RMSE Médio | MAE Médio | $R^2$ Médio | Tempo 3 Dobras |
| :--- | :---: | :---: | :---: | :---: |
| **Baseline (Média do Treino)** | $87,92 \pm 0,08$ | $66,24 \pm 0,04$ | $-0,0000$ | 0,09 s |
| **Regressão Linear (sem regularização)** | $76,48 \pm 0,05$ | $55,62 \pm 0,04$ | $0,2432$ | 118,26 s |
| **Ridge ($\alpha=1,0$)** | $76,48 \pm 0,05$ | $55,62 \pm 0,04$ | $0,2433$ | 89,33 s |
| **Árvore de Decisão (profundidade 12)** | $77,17 \pm 0,04$ | $56,29 \pm 0,02$ | $0,2297$ | 556,22 s |

- **Principais Conclusões Preliminares:**
  - O perfil tabular reduz o RMSE em **13,01%** (de 87,92 para 76,48 pontos) em relação à média.
  - A diferença entre a Regressão Linear sem regularização e o Ridge é inferior a 0,001 ponto de nota, indicando que a multicolinearidade inicial é moderada e bem comportada pelo volume amostral.
  - A Árvore de Decisão com profundidade 12 apresentou erro superior e custo computacional quase 6 vezes maior que os modelos lineares.
- **Elemento Visual:** Gráfico de barras comparativo de RMSE e $R^2$ com barras de erro (`relatorio/images/modelos.png`).

> **Fala do Integrante 3 (Resultados Preliminares - ~1.5 min):**  
> *"Nossa primeira rodada de validação cruzada comprovou que o perfil socioeconômico e demográfico possui sinal preditivo real sobre a nota de Ciências da Natureza, reduzindo o erro médio quadrático de 87,9 para 76,5 pontos — um ganho de 13%. Constatamos também que a regressão linear e o Ridge tiveram desempenho idêntico nesta escala, enquanto a árvore de decisão simples sofreu com partições rígidas, obtendo erro ligeiramente maior. Esse $R^2$ de aproximadamente 0,243 estabelece nossa linha de base competitiva para as próximas fases."*

---

### Slide 5: Próximos Experimentos e Hipóteses em Investigação
- **Catálogo de Modelos Adicionais:** Executar Bagging, Pasting, Random Forest, Boosting (*HistGradientBoosting*) e Stacking nas mesmas dobras.
- **Redução de Dimensionalidade:** Avaliar PCA preservando $\ge 80\%$ da variância acumulada em Ridge e Árvore.
- **Estratégia de Balanceamento:** Investigar ponderação amostral para penalizar desvios nas notas raras (caudas $<400$ e $>700$).
- **Busca de Hiperparâmetros:** Aplicar `GridSearchCV` / `RandomizedSearchCV` nos três melhores modelos distintos com $\ge 10$ configurações.
- **Curva de Aprendizado:** Traçar a curva de 10% a 100% de treino no modelo vencedor para diagnosticar viés e variância.
- **Hipóteses de Aprofundamento:**
  - *H1:* Avaliar a ablação comparativa entre o bloco socioeconômico e o bloco escolar/demográfico.
  - *H2:* Testar se um modelo compacto com 10 atributos preserva $\approx 98\%$ do desempenho.
- **Dúvidas e Discussão:**
  - *Trade-off* de balanceamento: ponderar as caudas tende a aumentar o RMSE global; qual tolerância a banca sugere priorizar?
  - Limite computacional do KNN na inferência de 2 milhões de linhas: viabilidade de indexação aproximada.

> **Fala do Integrante 4 (Próximos Passos e Fechamento - ~1.5 min):**  
> *"Nossos próximos passos estão claramente traçados: vamos expandir para os modelos de ensemble e boosting, realizar a busca de hiperparâmetros nos três melhores regressores e avaliar o PCA com 80% de variância. Também construiremos a curva de aprendizado em 5 pontos para verificar se o erro residual é falta de dados ou um limite estrutural das variáveis. Por fim, realizaremos a avaliação definitiva no teste reservado. Agradecemos a atenção e estamos abertos às dúvidas e recomendações do professor!"*

---

## 3. Checklist de Validação do Acompanhamento

- [x] Base nacional completa (3.93M) descrita com clareza.
- [x] Alvo `NU_NOTA_CN` e elegibilidade (2.69M observados, 16.5k zeros) especificados.
- [x] Features utilizadas e prevenção de vazamento documentadas.
- [x] Resultados preliminares de validação cruzada 3-fold com Baseline e regressores apresentados em tabela e gráficos.
- [x] Próximas hipóteses (PCA, balanceamento, busca, curva e teste) delimitadas.
- [x] Divisão equilibrada de falas e controle de tempo estruturado.
