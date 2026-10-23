# Protocolo preparado para a fase de pesquisa

Este é um plano de execução derivado do enunciado, não um relato de experimentos feitos.

1. Obter a fonte nacional de 2023 e seu dicionário. Registrar origem, edição e hash.
   Executar diagnóstico técnico integral sem filtros por perfil. Investigar divergências.
2. Registrar a nota atribuída. Separar para o supervisionado apenas participantes com
   esse alvo observado; zero continua observado. Não exigir as demais notas nem usar
   presença/situação da redação para selecionar a população de previsão.
3. Usar `make_split_table` e `save_splits` com ID, alvo e hash. O sorteio 80/20 usa 42;
   `validation_fold` 0,1,2 marca a dobra de validação de cada registro do desenvolvimento.
   Para a dobra k, treinar nos outros dois valores e validar em k. O teste tem dobra nula.
   Persistir uma vez e reutilizar os mesmos participantes e dobras nas comparações.
4. Explorar somente desenvolvimento: tipos, ausências, alternativas, distribuição do
   alvo, zeros, relação com features e grupos. Identificar onde cada informação estava
   disponível no contexto da previsão. Conferir códigos no dicionário.
5. Definir representação inicial e cada transformação. A fábrica de pré-processamento
   retorna um `ColumnTransformer` sem ajuste. Usá-lo no Pipeline completo por dobra.
   A estratégia de mediana do exemplo não é uma decisão sobre os dados oficiais.
6. Comparar baseline pela média e todos os regressores exigidos com RMSE principal,
   MAE, R² e tempos, guardando métricas por dobra, média e desvio padrão.
7. Criar ao menos três features justificadas, testar seleção e comparar à representação
   inicial. Registrar fórmulas, unidades, categorias e denominadores inválidos.
8. Avaliar PCA em pelo menos dois regressores, com representação e padronização
   justificadas. Escolher componentes só com o treino; reportar variância acumulada.
   Preservar ao menos 80% é sugestão do enunciado, não escolha feita nesta fase.
9. Testar uma estratégia de balanceamento para regressão. Faixas, frequências e pesos
   são definidos dentro do treino. Reamostrar somente treino; validação e teste mantêm
   distribuição original. Comparar o mesmo regressor com e sem estratégia.
10. Escolher os três melhores regressores distintos da comparação inicial, excluindo
    o baseline. GridSearchCV ou RandomizedSearchCV com ≥10 configurações válidas por
    regressor e três dobras; registrar espaço de busca e resultados antes/depois.
11. Investigar duas hipóteses adicionais para o aprofundamento integral, sem confundir
    execução dos requisitos mínimos com hipótese adicional.
12. Fixar a configuração final pelo desenvolvimento. Curva de aprendizado com 10%,25%,
    50%,75%,100% do treino de cada dobra, subconjuntos aleatórios progressivos com 42,
    validação fixa, Pipeline reajustado por ponto e configuração do regressor constante.
    Incluir a estratégia de treino escolhida; mostrar média e desvio do RMSE nas dobras.
13. Reajustar solução, baseline e linear sem regularização nos 80% completos. Só então
    avaliar os três nos mesmos participantes dos 20% reservados. Guardar previsões e
    não retomar a seleção a partir do teste.
14. Interpretar métricas, resíduos, faixas e grupo escolhido com n, sub/sobreajuste,
    limitações e custo. Escrever artigo e apresentações com fonte e interpretação.

## Catálogo obrigatório para implementação posterior

| Referência/modelo | Condição do enunciado |
|---|---|
| DummyRegressor(strategy="mean") | Média aprendida no treino de cada dobra |
| LinearRegression | Sem regularização; também avaliado no teste final |
| Ridge ou Lasso | Versão com regularização, além da linear simples |
| SVR ou LinearSVR | Kernel/implementação justificado e viável para a base completa |
| DecisionTreeRegressor | Configuração inicial registrada |
| KNeighborsRegressor | Escala e custo de predição considerados |
| BaggingRegressor | bootstrap=True |
| Pasting | bootstrap=False e max_samples < 1 |
| RandomForestRegressor | Comparar também com bagging |
| Boosting | Ao menos uma implementação permitida |
| StackingRegressor ou equivalente | ≥2 bases distintas; combinador com previsões fora da dobra; pré-processamento interno correto |

Não há necessidade de redes neurais, que ficam fora do escopo. Um método não visto
em sala exige explicação breve do funcionamento, motivo e parâmetros, com referência.

## Métricas e interpretação

Para n observações, erro residual e_i = y_i − previsão_i:

- RMSE = sqrt(sum(e_i²)/n); principal, em pontos da nota, sensível a erros grandes.
- MAE = sum(abs(e_i))/n; complementar, em pontos da nota.
- R² = 1 − sum(e_i²)/sum((y_i − média(y))²); pode ser negativo. Em grupos constantes
  ou muito pequenos, registrar a indefinição em vez de fabricar uma métrica útil.
- Média e desvio padrão entre dobras devem indicar a convenção do desvio adotada.
  Duração e unidade também são explícitas. Resultados de teste não integram a média CV.

Métricas devem ser calculadas na escala original, inclusive após transformação do alvo.
Faixas e grupos são definidos no desenvolvimento e mantidos na avaliação final. Todas
as métricas e análises por grupo usam os elegíveis do conjunto avaliado; amostra visual
documentada é permitida apenas para figuras densas e fins previstos no enunciado.

R² baixo isolado não diagnostica subajuste. Erros altos podem refletir informação
insuficiente. Generalização a participantes da mesma edição não demonstra desempenho
em municípios/escolas inéditos ou em outra edição. Associação não demonstra causalidade.
