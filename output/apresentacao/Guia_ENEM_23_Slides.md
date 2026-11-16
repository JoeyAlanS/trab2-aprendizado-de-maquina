# Roteiro de apresentação - ENEM 2023: 23 slides

Joey: slides 1 a 10. Paulo: slides 11 a 23. A fala principal orienta o pitch; os aprofundamentos e as perguntas são material de estudo. Duração a ajustar em ensaio, com referência de 15 a 20 minutos.

## Slide 1 - Predição da nota de Ciências da Natureza

**Apresentador:** Joey

**Fala principal sugerida**

Nosso trabalho compara dez regressores e uma referência pela média para estimar a nota de Ciências da Natureza no ENEM 2023. Usamos registros reais de participantes de todo o Brasil e mantivemos as mesmas partições para comparar os modelos. O objetivo foi verificar o desempenho e compreender os limites das previsões. O principal resultado foi o menor RMSE do Stacking, com vantagem pequena sobre uma regressão linear simples.

**Explicação para estudar e aprofundar**

Apresente os autores e o contexto acadêmico na Unifor. Explique que nacional significa cobertura dos participantes elegíveis desta edição, não uma amostra representativa de toda a população brasileira. O diferencial demonstrado é a comparação consistente em escala nacional, acompanhada de resultados negativos e análise dos erros. O projeto é um estudo acadêmico exploratório; não valida uma ferramenta para tomar decisões individuais sobre estudantes.

**Como explicar o visual**

Use a capa para situar o tema. Não antecipe todos os números: destaque apenas tarefa, comparação justa e leitura crítica.

**Pergunta provável e resposta**

O projeto prevê aprovação no ENEM? Não. Ele estima uma nota numérica de Ciências da Natureza, sem definir aprovação ou classificar pessoas.

**Transição**

Primeiro, precisamos delimitar a pergunta que esses modelos tentam responder.

## Slide 2 - Pergunta de pesquisa e objetivos

**Apresentador:** Joey

**Fala principal sugerida**

Queremos saber em que medida o perfil socioeconômico, escolar e demográfico permite estimar uma nota de Ciências da Natureza. Como a saída é um número, trabalhamos com regressão. Comparamos os erros dos algoritmos e investigamos em quais grupos ou faixas de nota eles erram mais. Isso ajuda a avaliar o quanto essas informações descrevem o desempenho observado, sem atribuir uma causa à renda, à escola ou a outra característica.

**Explicação para estudar e aprofundar**

Regressão supervisionada utiliza exemplos com entradas e uma saída conhecida. Durante o treino, o modelo ajusta seus parâmetros para aproximar essa saída. Depois, comparamos previsões e notas reais em registros separados. Associação preditiva não é causalidade: um atributo pode ajudar a prever por estar associado a outras condições não observadas. A utilidade demonstrada é metodológica e descritiva, adequada ao debate acadêmico sobre previsibilidade e limitações dos dados.

**Como explicar o visual**

Percorra os três blocos: alvo contínuo, comparação nas mesmas partições e diagnóstico dos erros. A pergunta de pesquisa conecta todo o pitch.

**Pergunta provável e resposta**

Por que não é classificação? Porque não criamos rótulos como aprovado ou reprovado; o valor previsto continua sendo uma nota.

**Transição**

Para responder à pergunta, começamos pela origem e pela qualidade dos dados.

## Slide 3 - População e divisão dos dados

**Apresentador:** Joey

**Fala principal sugerida**

A base original contém 3.933.955 registros e 76 colunas. Para treinar uma regressão supervisionada, precisamos conhecer a nota real: 2.692.427 participantes tinham Ciências da Natureza observada. Os 1.241.528 sem essa nota ficaram fora da supervisão. Isso é diferente de nota zero: os 16.547 zeros observados foram mantidos. Dividimos os elegíveis em 2.153.941 para desenvolvimento e 538.486 para teste.

**Explicação para estudar e aprofundar**

A importação foi feita em lotes, normalizando espaços, tokens de ausência e tipos, sem editar os arquivos originais. O projeto registrou integridade dos ZIPs e hashes e confirmou a igualdade do CSV normalizado com os Parquets preparados. Não houve substituição por dados sintéticos no experimento nacional. Fixtures fictícias pertencem apenas aos testes de software. O complemento de competências de redação foi preservado, mas não foi integrado aos preditores desta tarefa.

**Como explicar o visual**

Aponte a passagem de base original para elegíveis e depois os dois conjuntos. Explique por que excluir alvo ausente não significa apagar a pessoa da importação original.

**Pergunta provável e resposta**

Foi imputada uma nota para quem não fez a prova? Não. O alvo ausente não foi preenchido nem convertido em zero.

**Transição**

Com a população definida, precisamos mostrar quais informações os modelos receberam.

## Slide 4 - 40 atributos originais de perfil

**Apresentador:** Joey

**Fala principal sugerida**

Utilizamos quarenta atributos originais. Q005 representa o número de moradores e é a única entrada numérica original; os outros trinta e nove atributos são tratados como categóricos. Há dados demográficos, escolares e do questionário socioeconômico. O alvo é NU_NOTA_CN. O identificador NU_INSCRICAO serve para controlar participantes e partições, sem entrar no modelo. Também não usamos outras notas, respostas, gabaritos ou presença como preditores.

**Explicação para estudar e aprofundar**

Não confunda Q005 com o alvo: quantidade de moradores é uma entrada; a nota de Ciências da Natureza é a saída que tentamos estimar. Códigos numéricos de categorias não significam necessariamente quantidades ou distâncias. Por isso, renda Q006 e escolaridade Q001/Q002 recebem codificação categórica na receita original. SG_UF_PROVA indica a UF de aplicação, que pode ser diferente da residência. A lista completa das quarenta entradas está na configuração e no guia de fala.

**Como explicar o visual**

Leia exemplos da tabela, evitando recitar os quarenta nomes. Relacione nome real, significado e tratamento. Destaque a diferença entre entrada e alvo.

**Pergunta provável e resposta**

Todas as entradas se tornam binárias? Não. As categorias viram indicadores, mas Q005 continua numérica e é padronizada.

**Transição**

Antes de treinar, essas entradas precisam de uma representação que evite vazamento.

## Slide 5 - Pré-processamento e prevenção de vazamento

**Apresentador:** Joey

**Fala principal sugerida**

A limpeza de formato acontece na importação; a preparação estatística acontece dentro de cada treino. Q005 recebe a mediana quando necessário e passa por padronização. Nas categorias, a ausência recebe um marcador próprio e a codificação one-hot cria indicadores de categoria. Mediana, escala e categorias aprendidas não são ajustadas usando a validação ou o teste. Esse isolamento impede que a preparação antecipe informações da avaliação.

**Explicação para estudar e aprofundar**

Vazamento ocorre quando uma decisão de treino utiliza informação que deveria estar fora dele. Calcular a média ou a mediana na base inteira antes de separar as dobras já quebraria esse isolamento. O Pipeline organiza preparação e regressor no mesmo ajuste. No one-hot, uma categoria A pode virar 1,0,0 e B virar 0,1,0: é um exemplo didático de representação, não uma previsão. Categorias inéditas são ignoradas pelo codificador; desconhecimento previsto no dicionário permanece distinto de ausência. O indicador de ausência numérica é criado quando aplicável.

**Como explicar o visual**

Mostre o fluxo e a pequena tabela A/B/C. Aqui A/B/C são categorias didáticas; no próximo slide as mesmas letras representarão partes dos participantes.

**Pergunta provável e resposta**

Padronizar muda a informação? Muda a escala numérica, usando parâmetros do treino; não cria novas notas nem transforma Q005 em categoria.

**Transição**

Agora veremos quais participantes entram no treino e na validação em cada rodada.

## Slide 6 - Três dobras com o teste reservado

**Apresentador:** Joey

**Fala principal sugerida**

Separamos 80% dos elegíveis para desenvolvimento e 20% para o teste final. Dentro do desenvolvimento, criamos três partes fixas: A, B e C. Na primeira rodada, treinamos em B e C e validamos em A. Na segunda, treinamos em A e C e validamos em B. Na terceira, treinamos em A e B e validamos em C. Assim, cada participante do desenvolvimento é avaliado uma vez fora do treino daquele ajuste.

**Explicação para estudar e aprofundar**

A tem 717.981 participantes; B e C têm 717.980 cada. Os treinos têm 1.435.960 ou 1.435.961 pessoas. Cada rodada reajusta o modelo e sua preparação. As dobras são as mesmas para todos os algoritmos. A semente 42 controla o sorteio para reproduzir a divisão com os mesmos dados e configuração; não melhora automaticamente o resultado. O teste ficou fora das escolhas, foi usado após o congelamento das receitas e já foi concluído. Três dobras externas não são três testes finais.

**Como explicar o visual**

Leia cada linha da matriz, mostrando duas células de treino e uma de validação. A cor identifica o papel da parte naquela rodada.

**Pergunta provável e resposta**

O teste é a terceira dobra? Não. Ele foi separado antes; as três dobras pertencem somente aos 80% do desenvolvimento.

**Transição**

Com esse protocolo comum, podemos comparar os mecanismos de aprendizagem.

## Slide 7 - Dez regressores efetivamente avaliados

**Apresentador:** Joey

**Fala principal sugerida**

A tabela reúne todos os dez regressores executados: linear sem regularização, Ridge, árvore de decisão, SVM linear, KNN, Bagging, Pasting, Random Forest, Gradient Boosting e Stacking. A média do treino é uma referência adicional. Todos usam as mesmas três dobras e o mesmo critério principal. Os próximos slides detalham linear, Ridge e árvore isolada, que antes estavam apenas numa observação.

**Explicação para estudar e aprofundar**

Ridge atende à opção de regressão linear com regularização; não é obrigatório acrescentar Lasso. LinearSVR é permitido no enunciado. A escolha linear define uma hipótese aditiva e uma implementação viável para este protocolo nacional, mas não demonstra superioridade sobre RBF ou polinomial, que não foram comparados. GradientBoostingRegressor atende à exigência de ao menos um boosting; AdaBoost, XGBoost e outros não foram executados. O KNN real é ExactProfileKNeighborsRegressor, uma implementação própria de regressão com 25 vizinhos e busca euclidiana exata, não uma instância literal de KNeighborsRegressor. Faiss não transforma a busca em aproximação. Bagging e Pasting usam vinte árvores e 70% do treino, com e sem reposição. Random Forest obteve RMSE 76,643 contra 77,484 do Bagging; também mudam quantidade e profundidade das árvores, portanto não isolamos o efeito do sorteio de atributos. A folha mínima é cem nas árvores. As configurações iniciais não foram alteradas nesta revisão.

**Como explicar o visual**

Explique os mecanismos em pares: Bagging/Pasting e Random Forest/Boosting. A tabela mostra configurações iniciais; a busca de parâmetros aparece depois.

**Pergunta provável e resposta**

A lista está completa? Sim: há dez regressores, incluindo a linear com e sem regularização e a árvore isolada, mais o baseline. As alternativas não executadas não devem ser apresentadas como modelos testados.

**Transição**

Começamos pelos três regressores que faltavam na explicação individual, a partir da linear sem regularização.

## Slide 8 - Linear sem regularização

**Apresentador:** Joey

**Fala principal sugerida**

A regressão linear sem regularização estima a nota por um intercepto somado aos atributos multiplicados por coeficientes aprendidos. O ajuste minimiza a soma dos erros ao quadrado, sem uma penalização L1 ou L2. Essa é uma referência importante: antes de defender um ensemble, precisamos verificar se ele supera uma solução simples. A linear teve RMSE médio de 76,484 na validação e 76,517 no teste final.

**Explicação para estudar e aprofundar**

A fórmula geral é nota prevista = intercepto + soma dos coeficientes vezes as entradas preparadas. Os indicadores one-hot permitem coeficientes diferentes para categorias, enquanto Q005 permanece numérica padronizada. Os coeficientes são aprendidos no treino; não foram publicados nos slides como uma equação numérica final. Tol=1e-6 é a tolerância inicial do solucionador, não uma penalização de regularização. A linear usa o mesmo Pipeline e as mesmas dobras dos outros modelos. Ela também é uma base do Stacking, mas sua avaliação isolada é um experimento distinto. Na busca foi selecionado tol=1e-5; a referência do teste conserva tol=1e-6. Coeficientes preditivos não identificam efeitos causais.

**Como explicar o visual**

Percorra previsão, ajuste e configuração. Compare os dois números com cuidado: o primeiro resume três dobras; o segundo pertence ao teste final, em outro conjunto de participantes.

**Pergunta provável e resposta**

Sem regularização significa sem preparação? Não. A linear recebe a mesma preparação das entradas; o que não existe é a penalização adicional L1 ou L2 nos coeficientes.

**Transição**

Agora veremos uma regressão linear que acrescenta controle sobre o tamanho dos coeficientes: Ridge.

## Slide 9 - Ridge: regularização L2

**Apresentador:** Joey

**Fala principal sugerida**

Ridge também aprende uma combinação linear dos atributos, mas acrescenta uma penalização L2. O objetivo combina a soma dos erros quadráticos com alpha vezes a soma dos coeficientes ao quadrado. Alpha controla a força dessa penalização. Como regressor independente, Ridge recebe as quarenta entradas originais após preparação, e não as previsões de outros modelos. Seu RMSE inicial foi 76,484, com a segunda colocação no ranking completo antes do arredondamento.

**Explicação para estudar e aprofundar**

A penalização desencoraja coeficientes muito grandes e permite controlar a complexidade. Isso pode ajudar quando há entradas correlacionadas, mas não garante menor erro em qualquer base. A receita inicial tem alpha=1, solver=lsqr e tol=1e-5. A busca selecionou alpha=10, com ganho de aproximadamente 0,0000376 ponto de RMSE. O RMSE inicial exato foi 76,483610, contra 76,483799 da linear: ambos aparecem como 76,484 nos slides. A diferença é muito pequena e não recebeu teste de significância. Há dois usos distintos de Ridge: isolada, aprende dos atributos; como combinador do Stacking, aprende das duas previsões OOF. No combinador, alpha passou de 1 para 1000. A Ridge isolada tem CV completa, mas não foi avaliada no teste final deste protocolo. Lasso seria uma alternativa permitida de regularização; não foi o método executado.

**Como explicar o visual**

Explique o que muda na função de ajuste e o significado de alpha. A posição de segundo lugar é pelo RMSE da CV inicial, não pelo teste. O número grande é o RMSE inicial, não o valor de alpha.

**Pergunta provável e resposta**

Ridge é apenas uma etapa do Stacking? Não. O projeto avaliou uma Ridge independente e também utiliza outra Ridge como combinador, com entradas e configurações diferentes.

**Transição**

A seguir, saímos da combinação linear para um modelo que aprende regras: a árvore de decisão.

## Slide 10 - Árvore de decisão isolada

**Apresentador:** Joey

**Fala principal sugerida**

A árvore de decisão aprende regras sobre os atributos preparados e divide o treino em regiões. Em cada divisão, busca reduzir o erro quadrático. Para uma nova pessoa, percorremos as regras até uma folha, e a previsão é a média das notas do treino naquela folha. A árvore isolada teve RMSE médio de 77,167 e ficou em sexto no catálogo completo. Ela é um modelo próprio e também uma das bases do Stacking.

**Explicação para estudar e aprofundar**

Foi utilizado DecisionTreeRegressor, com profundidade máxima doze, pelo menos cem participantes em cada folha e semente 42. O critério padrão squared_error corresponde à redução da variância dentro das regiões e à previsão pela média da folha. Profundidade doze não significa doze árvores, e folha mínima cem não significa cem folhas. Esses limites restringem a complexidade de uma árvore que, sem controles, pode ajustar detalhes particulares do treino. A árvore permite relações não lineares e interações entre entradas, sem aprender uma única soma linear global. Sua preparação continua restrita ao treino da dobra. Bagging, Pasting, floresta e boosting combinam várias árvores; não devem ser confundidos com este estimador isolado. Os experimentos com PCA também incluíram a árvore, mas a variante não melhorou o RMSE. Não há previsão da árvore isolada no teste final.

**Como explicar o visual**

Leia as três etapas: aprender regras, prever pela média e controlar complexidade. Os números destacam erro de validação e posição no ranking, sem representar uma avaliação final no teste.

**Pergunta provável e resposta**

Por que Random Forest pode diferir da árvore? A floresta agrega árvores com aleatoriedade e média de previsões. As configurações também diferem; a comparação observada não isola um único efeito.

**Transição**

Com linear, Ridge e árvore isolada esclarecidas, podemos entender como duas dessas bases são combinadas no Stacking.

## Slide 11 - Stacking: duas bases e um combinador

**Apresentador:** Paulo

**Fala principal sugerida**

Nosso Stacking tem duas bases: regressão linear e árvore de decisão. Primeiro, produz previsões internas para participantes que não estavam no treino da base naquela rodada. Essas previsões fora da dobra, chamadas OOF, tornam-se entradas de uma regressão Ridge que aprende a combinação. Portanto, o combinador aprende com erros de generalização das bases, em vez de receber apenas previsões sobre pessoas que elas já conheceram.

**Explicação para estudar e aprofundar**

As três dobras internas servem para treinar o combinador; as três externas servem para avaliar o Stacking inteiro. Cada base possui seu próprio Pipeline, inclusive nas dobras internas. Ridge é regressão linear com penalização L2: minimiza o erro quadrático junto de uma penalização para coeficientes grandes. Alpha controla sua força. A receita inicial usa alpha=1 e a final usa 1000, com ganho de busca de apenas cerca de 3,205 vezes 10 elevado a menos 8 ponto de RMSE. SVM e Random Forest não são bases deste Stacking. Os coeficientes numéricos da combinação não são exibidos nos slides.

**Como explicar o visual**

Siga o diagrama de cima para baixo: duas bases, previsões OOF e combinador Ridge. Não confunda combinação aprendida com média simples fixa.

**Pergunta provável e resposta**

Qual é a fórmula? Ela combina linearmente as duas previsões com coeficientes aprendidos. Não há valores de coeficientes publicados no slide para apresentar como fórmula numérica final.

**Transição**

Para julgar se essa combinação ajuda, precisamos definir o significado das métricas.

## Slide 12 - Métricas e modelos de referência

**Apresentador:** Paulo

**Fala principal sugerida**

O RMSE é a raiz da média dos erros ao quadrado, em pontos da nota. Ele dá maior peso a erros grandes e é nosso critério principal. O MAE é a média dos erros absolutos, também em pontos. O R² compara o erro quadrático com a variação em torno da média observada. RMSE e MAE menores são melhores; R² maior é melhor. Resumimos a validação pela média e pelo desvio padrão das três dobras.

**Explicação para estudar e aprofundar**

Nas fórmulas, y é a nota real, y previsto é a estimativa e n é o total avaliado. Como exemplo didático, erros de dez e trinta pontos produzem MAE de vinte e RMSE de aproximadamente 22,36; isso ilustra a penalização dos erros maiores, sem representar resultados do projeto. O desvio padrão populacional entre três dobras descreve variação e não é intervalo de confiança. O baseline prevê a média do alvo do treino, sem usar atributos. Um R² perto de 0,25 não significa 25% de acertos nem prova sozinho subajuste.

**Como explicar o visual**

Relacione cada fórmula à sua leitura oral. Use a referência pela média para explicar o valor de comparar um método complexo com uma alternativa simples.

**Pergunta provável e resposta**

Por que não há matriz de confusão? Porque a tarefa é regressão contínua. Usamos resíduos, erros e observado versus previsto.

**Transição**

Com essas métricas, podemos ler o ranking completo.

## Slide 13 - Catálogo completo e seleção pelo RMSE

**Apresentador:** Paulo

**Fala principal sugerida**

No catálogo completo, o menor RMSE médio foi do Stacking, 76,175 pontos. Depois vêm Ridge e linear, ambos arredondados para 76,484. Antes do arredondamento, Ridge ficou ligeiramente à frente. No recorte de sete famílias, os três primeiros são Stacking, SVM linear e Random Forest. Essa diferença de escopo explica os dois trios apresentados durante o projeto. As buscas contemplaram a união deles: cinco modelos.

**Explicação para estudar e aprofundar**

Os RMSE não arredondados são 76,174516 para Stacking, 76,483610 para Ridge e 76,483799 para linear. A escolha usa RMSE no desenvolvimento, não o resultado do teste. O gráfico inclui a média, com 87,921, e mostra dez regressores mais essa referência. As pequenas barras de erro representam o DP das dobras, não significância. KNN, Bagging, Pasting e Boosting foram avaliados, mas não ficaram no trio do recorte de sete. Não identificamos uma causa única para suas diferenças; elas dependem dos dados, da representação e das configurações testadas.

**Como explicar o visual**

Leia o eixo horizontal e destaque que menor é melhor. Mostre as três primeiras linhas e depois explique o empate visual entre Ridge e linear.

**Pergunta provável e resposta**

SVM e Random Forest são segundo e terceiro gerais? Não. Essa colocação vale apenas para o recorte de sete algoritmos.

**Transição**

Também testamos se uma representação mais informativa das entradas reduziria o erro.

## Slide 14 - Engenharia de atributos

**Apresentador:** Paulo

**Fala principal sugerida**

Criamos três atributos derivados: computadores por morador, acesso digital e maior escolaridade dos responsáveis. O objetivo foi apresentar relações que poderiam ser úteis ao Ridge. O RMSE caiu de 76,484 na receita original para 76,458 com engenharia. A melhora é pequena e não foi submetida a teste de significância. Essa é uma comparação de representação, sem alterar o conjunto de participantes ou consultar o teste final.

**Explicação para estudar e aprofundar**

Q024 é convertida de A a E para zero a quatro computadores; a última alternativa informa quatro ou mais, então quatro é um limite inferior. A divisão usa Q005 entre um e vinte moradores; fora disso, o atributo derivado fica ausente. Acesso digital soma presença de computador e internet, de zero a dois quando ambas são conhecidas. Escolaridade máxima mapeia A a G para níveis de zero a seis e exige as duas respostas conhecidas: desconhecimento não recebe nível inventado. O preenchimento posterior de ausências aprende somente no treino. Esse índice digital é uma construção operacional, não uma escala social validada.

**Como explicar o visual**

Mostre as três fórmulas conceituais e a pequena redução do RMSE. Não apresente essa diferença como grande avanço.

**Pergunta provável e resposta**

Criamos dados fictícios? Não. São transformações determinísticas de respostas reais, com regras explícitas e tratamento de desconhecimento.

**Transição**

Em seguida, tentamos reduzir a quantidade de informações da representação.

## Slide 15 - Seleção de atributos e PCA

**Apresentador:** Paulo

**Fala principal sugerida**

Testamos duas estratégias diferentes de redução. A seleção manteve 75% das colunas codificadas após a engenharia, escolhidas pelo teste F de regressão. O PCA criou componentes que preservam pelo menos 80% da variância. Nas receitas avaliadas, nenhuma estratégia melhorou o erro global. O PCA reteve 45 componentes de uma representação original de 235 dimensões, tanto no Ridge quanto na árvore.

**Explicação para estudar e aprofundar**

Selecionar mantém um subconjunto de colunas existentes; PCA cria novas combinações numéricas delas. Preservar variância significa conservar dispersão das entradas, não necessariamente informação útil para prever a nota. Por isso, compressão não garante menor RMSE. O Ridge com seleção teve 76,529. Com PCA, o Ridge passou de 76,484 para 77,733 e a árvore de 77,167 para 78,328. Houve seis ajustes de PCA: dois regressores em três dobras, sempre aprendendo os componentes no treino. A seleção foi experimentada no Ridge. A receita final vencedora não utiliza PCA.

**Como explicar o visual**

No gráfico, o eixo horizontal é o número de componentes e o vertical é a variância acumulada. Mostre o cruzamento do limiar de 80% em 45 componentes.

**Pergunta provável e resposta**

O que são as 235 dimensões? São colunas da representação após preparação, principalmente indicadores categóricos; não são 235 perguntas originais.

**Transição**

Também investigamos o equilíbrio das notas e a contribuição de blocos de atributos.

## Slide 16 - Ponderação e duas ablações

**Apresentador:** Paulo

**Fala principal sugerida**

A ponderação deu mais peso às faixas de notas menos frequentes durante o treino. O RMSE global do Ridge piorou para 125,202. Também fizemos duas ablações: retirar o questionário socioeconômico elevou o RMSE para 80,351; retirar a UF da prova elevou para 76,661. Esses resultados mostram que as propostas precisam ser medidas: uma mudança aparentemente razoável pode prejudicar o critério global.

**Explicação para estudar e aprofundar**

Os pesos são inversos à frequência de dez faixas de largura igual, calculadas a partir do alvo do treino. Eles alteram a importância de exemplos no ajuste, sem criar participantes. A avaliação global continua usando o mesmo RMSE para permitir comparação. Ablação é retirar um bloco e observar a mudança, mantendo o protocolo. O aumento do erro sugere contribuição preditiva dessas entradas nessa configuração, mas não identifica efeito causal. Não treinamos um modelo separado para cada renda ou UF. Uma melhoria de alguma faixa não basta para declarar melhora do resultado global.

**Como explicar o visual**

Compare cada linha à receita original de 76,484. Destaque o resultado negativo da ponderação e explique por que ele também é um achado.

**Pergunta provável e resposta**

Isso prova que renda determina a nota? Não. Mostra contribuição preditiva do bloco socioeconômico nas condições observadas.

**Transição**

Depois da representação, avaliamos alternativas de hiperparâmetros.

## Slide 17 - Busca de hiperparâmetros

**Apresentador:** Paulo

**Fala principal sugerida**

Hiperparâmetros são escolhas que definimos antes de ajustar o modelo, como profundidade, quantidade de árvores ou força da regularização. Testamos doze configurações em cada um de cinco modelos: sessenta configurações e cento e oitenta avaliações nas três dobras. A decisão usou o RMSE do desenvolvimento. Os ganhos foram mínimos, e as receitas foram congeladas antes de abrir o teste final.

**Explicação para estudar e aprofundar**

GridSearchCV avalia combinações de uma grade, usando as partições persistidas via PredefinedSplit. Stacking e Ridge variaram alpha; a SVM variou C e epsilon; a floresta variou profundidade e número de árvores; a linear variou intercepto e tolerância. Na busca da SVM, max_iter foi ampliado para 50.000; isso não deve ser confundido com a configuração inicial de 5.000. O Stacking selecionou alpha=1000, Ridge alpha=10 e linear tol=1e-5. SVM e floresta mantiveram as receitas iniciais. A linear de referência levada ao teste mantém tol=1e-6. A tolerância numérica de decisão não é teste de significância.

**Como explicar o visual**

Leia 12 por 5 e depois multiplique pelas três dobras. Evite chamar as 180 avaliações de 180 algoritmos diferentes.

**Pergunta provável e resposta**

Parâmetro aprendido e hiperparâmetro são iguais? Não. Coeficientes são aprendidos no ajuste; alpha e profundidade são escolhas da configuração.

**Transição**

As curvas ajudam a entender o comportamento das receitas com quantidades crescentes de treino.

## Slide 18 - Curvas de aprendizado dos três modelos

**Apresentador:** Paulo

**Fala principal sugerida**

As curvas mostram o erro de treino e de validação quando usamos 10%, 25%, 50%, 75% e 100% do treino de cada dobra. A validação permanece fixa. Nos três modelos, as curvas finais ficam próximas, com diferenças de RMSE de 0,193 no Stacking, 0,007 na SVM e 0,400 na floresta. Isso não sugere sobreajuste acentuado nessas condições, mas não comprova desempenho em outra edição do ENEM.

**Explicação para estudar e aprofundar**

O eixo horizontal indica quantidade de participantes de treino e o vertical indica RMSE. Cada ponto resume três dobras. Sobreajuste costuma produzir erro de treino muito menor que validação; subajuste pode aparecer quando o modelo não captura padrões úteis nem no treino. Gap pequeno, sozinho, não garante um modelo adequado ou ausência absoluta de sobreajuste. O menor treino já tem cerca de 143.596 participantes. Existem 45 pontos iniciais e 45 finais, com reuso registrado: trinta pontos iguais de SVM/floresta, doze do Stacking com bases reutilizadas e novo combinador, e três vindos das buscas em treino completo.

**Como explicar o visual**

Aponte primeiro a legenda treino/validação, depois a distância entre as linhas e o efeito de aumentar os dados. As faixas mostram DP, não intervalo de confiança.

**Pergunta provável e resposta**

São noventa treinamentos novos? Não. São pontos registrados, parte deles obtida com reuso compatível de ajustes ou bases.

**Transição**

Com a receita congelada, chegamos à avaliação final separada.

## Slide 19 - Teste final em 538.486 participantes

**Apresentador:** Paulo

**Fala principal sugerida**

No teste de 538.486 participantes, o Stacking teve RMSE de 76,190, MAE de 55,325 e R² de 0,2497. A regressão linear ficou próxima, com RMSE de 76,517. SVM e floresta tiveram 76,622 e 76,658. A média teve 87,959. A redução do RMSE do Stacking frente à média foi de 13,38%; a vantagem frente à linear foi de apenas 0,327 ponto. Isso exige uma interpretação equilibrada.

**Explicação para estudar e aprofundar**

Os cinco modelos foram ajustados no desenvolvimento completo, com receitas previamente definidas, e avaliados nos mesmos IDs do teste. A seleção veio do desenvolvimento; não voltamos a escolher parâmetros após consultar o teste. A presença da linear e da média permite avaliar alternativas simples. Ridge, árvore, KNN, Bagging, Pasting e Boosting têm CV completa, mas não previsões nesse teste final. O R² indica redução do erro quadrático frente à variação em torno da média observada, não percentual de pessoas acertadas. Os tempos de ajuste observados foram 1.250,63 s para Stacking e 36,41 s para linear; não constituem benchmark isolado de hardware.

**Como explicar o visual**

Leia a tabela por RMSE, depois use MAE e R² para complementar. Mostre que o ganho de 13,38% se refere à média, não à regressão linear.

**Pergunta provável e resposta**

O vencedor é estatisticamente superior? Não fizemos teste de significância. Podemos afirmar que apresentou o menor RMSE observado neste protocolo.

**Transição**

A média global do erro não revela onde as previsões falham mais.

## Slide 20 - Erros concentrados nos extremos

**Apresentador:** Paulo

**Fala principal sugerida**

No observado versus previsto, a diagonal representa previsão perfeita. As estimativas se concentram mais no centro da escala: notas baixas tendem a ser superestimadas e notas altas, subestimadas. No Stacking, o RMSE foi 154,31 abaixo de quatrocentos pontos e 160,74 a partir de setecentos. Entre quatrocentos e menos de quinhentos, ficou em 48,12. Portanto, o desempenho global esconde uma dificuldade importante nos extremos.

**Explicação para estudar e aprofundar**

As células coloridas agregam todos os participantes do teste, sem substituir a base por uma amostra de pontos. O gráfico por faixa usa a nota observada para agrupar o diagnóstico depois da previsão, não como entrada do modelo. Há 57.759 participantes abaixo de 400, 226.331 em [400,500) e 6.318 a partir de 700. Resíduo é observado menos previsto: negativo indica superestimação; positivo, subestimação. Os resíduos médios do Stacking foram -118,60 e +156,03 nas faixas extremas. Resíduo médio e RMSE são medidas diferentes: o primeiro conserva o sinal; o segundo mede magnitude.

**Como explicar o visual**

Explique a diagonal e o significado das cores antes de interpretar a concentração central. Depois conecte os extremos do gráfico às linhas da tabela.

**Pergunta provável e resposta**

O modelo acerta todo mundo com erro de 76 pontos? Não. RMSE é um resumo agregado; erros individuais e por faixa podem ser muito maiores.

**Transição**

Também verificamos como os erros se distribuem entre grupos de participantes.

## Slide 21 - Análise por grupos de participantes

**Apresentador:** Paulo

**Fala principal sugerida**

O gráfico compara erros por tipo de escola, sem treinar modelos diferentes para cada grupo. Temos 327.386 participantes que não responderam essa informação, 166.819 de escola pública e 44.281 de escola privada. As contagens são importantes porque os grupos têm tamanhos e perfis diferentes. Também analisamos renda e UF de aplicação. Essas diferenças são diagnósticos descritivos de previsão, sem demonstrar causalidade.

**Explicação para estudar e aprofundar**

O eixo vertical representa RMSE, não a média das notas e nem a qualidade da escola. Um grupo com erro menor não pode ser apresentado automaticamente como mais capaz ou melhor atendido pelo sistema educacional. As características e a distribuição das notas podem variar entre grupos. O código 1 de TP_ESCOLA é uma alternativa própria de não resposta, que não foi fundida com escola pública ou privada. SG_UF_PROVA descreve aplicação, não necessariamente residência. Renda Q006 é autodeclarada. Os erros de renda e UF e suas contagens estão nas figuras e tabelas do projeto; não exibimos resultados fictícios no slide.

**Como explicar o visual**

Mostre a legenda dos modelos, o RMSE e os tamanhos dos grupos. Reforce que o gráfico mede erro de previsão, e não ranking de desempenho escolar.

**Pergunta provável e resposta**

A análise comprova justiça do modelo? Não. Diferenças descritivas de RMSE, isoladamente, não certificam equidade nem adequação a decisões individuais.

**Transição**

Esses diagnósticos ajudam a delimitar o que podemos concluir.

## Slide 22 - Limites e rastreabilidade

**Apresentador:** Paulo

**Fala principal sugerida**

Preservamos parâmetros, partições, métricas e evidências de execução para permitir conferência. A suíte atual teve 87 testes de software aprovados. Esses testes verificam o código e não são novas rodadas de treinamento nacional. Cientificamente, analisamos uma edição e uma divisão aleatória. Não fizemos validação temporal, avaliação externa ou teste de significância entre modelos. O R² perto de 0,25 mostra que o perfil disponível não captura toda a variação da nota.

**Explicação para estudar e aprofundar**

As comparações iniciais têm 33 avaliações por dobra; as variantes somam 21. As buscas têm 180 avaliações e as curvas incluem reuso documentado. O teste final reúne cinco modelos. Não some tudo como se cada registro fosse um ajuste novo. Dados fictícios ficam isolados nos testes de software; treinamento nacional e métricas científicas utilizam participantes reais. Os agregados e o código estão no repositório; arquivos individuais grandes são locais. A divisão fixa e os hashes apoiam rastreabilidade, mas não garantem reprodução bit a bit em qualquer ambiente ou generalização para outro ano. Respostas autodeclaradas e ausências também limitam a análise.

**Como explicar o visual**

Separe as duas colunas: limites científicos e evidências técnicas. A aprovação de testes de código não elimina os limites da pesquisa.

**Pergunta provável e resposta**

Os 87 testes provam que o modelo generaliza? Não. Generalização é avaliada por dados separados; os testes de software verificam contratos e comportamento da implementação.

**Transição**

Encerramos com a contribuição demonstrada e as próximas perguntas de pesquisa.

## Slide 23 - Conclusões e próximos passos

**Apresentador:** Paulo

**Fala principal sugerida**

Concluímos que o Stacking apresentou o menor RMSE observado, mas a regressão linear foi uma alternativa muito próxima e mais simples. A engenharia teve ganho pequeno; PCA, seleção e ponderação não melhoraram o erro global nas configurações avaliadas. Nossa contribuição é uma comparação nacional documentada, incluindo os limites e as hipóteses que não funcionaram. Os próximos estudos são outra edição, partições por grupos e intervalos de predição. Essas etapas futuras ainda não foram realizadas.

**Explicação para estudar e aprofundar**

Ao defender o resultado, diferencie vantagem observada de superioridade universal. O custo adicional do Stacking e a pequena distância para a linear precisam ser considerados junto das métricas. A execução nacional demonstrou viabilidade computacional no ambiente do estudo, mas não foi avaliada como serviço em produção nem como solução de impacto educacional. A nota não resume a capacidade de um estudante. A mensagem final pode ser: comparamos métodos de forma consistente, medimos os erros reais e identificamos o alcance e os limites das previsões.

**Como explicar o visual**

Retome a pergunta do slide 2 e a resposta sustentada pelas métricas. Aponte as fontes e encerre abrindo espaço para perguntas.

**Pergunta provável e resposta**

Qual seria o próximo passo mais importante? Avaliar uma receita previamente definida em outra edição ou divisão por grupos, para testar estabilidade além desta partição.

**Transição**

Obrigado. Ficamos à disposição para explicar as escolhas, os resultados e os limites do estudo.

## Atributos utilizados

Lista integral dos 40 atributos, conforme a configuração:
Q005, TP_FAIXA_ETARIA, TP_SEXO, TP_ESTADO_CIVIL, TP_COR_RACA, TP_NACIONALIDADE, TP_ST_CONCLUSAO, TP_ANO_CONCLUIU, TP_ESCOLA, TP_ENSINO, IN_TREINEIRO, TP_DEPENDENCIA_ADM_ESC, TP_LOCALIZACAO_ESC, TP_SIT_FUNC_ESC, SG_UF_PROVA, TP_LINGUA, Q001, Q002, Q003, Q004, Q006, Q007, Q008, Q009, Q010, Q011, Q012, Q013, Q014, Q015, Q016, Q017, Q018, Q019, Q020, Q021, Q022, Q023, Q024, Q025.
Grupos: demográficos (5), escolares (8), localização/língua (2) e 24 respostas categóricas do questionário, além de Q005. Não confundir códigos de desconhecimento previstos no dicionário com valores ausentes.

## Trechos de código para demonstração

Os trechos abaixo são do código do projeto. A numeração indica o slide correspondente na apresentação ampliada. Os regressores mantêm suas configurações experimentais originais.

### Slide 4

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

### Slide 5

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

### Slide 6

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

### Slide 7

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

### Slide 11

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

### Slide 12

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

### Slide 14

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

### Slide 15

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

### Slide 16

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

### Slide 17

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

### Slide 22

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

### Slide 8: modelo independente

Arquivo: `src/enem_base/modeling.py`, função `model_catalog`. Cada regressor está no Pipeline de preparação.

```python
LinearRegression(tol=1e-6)
```

### Slide 9: modelo independente

Arquivo: `src/enem_base/modeling.py`, função `model_catalog`. Cada regressor está no Pipeline de preparação.

```python
Ridge(alpha=1.0, solver="lsqr", tol=1e-5)
```

### Slide 10: modelo independente

Arquivo: `src/enem_base/modeling.py`, função `model_catalog`. Cada regressor está no Pipeline de preparação.

```python
DecisionTreeRegressor(
    max_depth=12, min_samples_leaf=100, random_state=42
)
```
