# Pitch - Comparação nacional de modelos no ENEM 2023

Joey Alan de Freitas Solis e Paulo Henrico

Universidade de Fortaleza (Unifor) - Professor Tulio

Roteiro oral, sem slides. Duração planejada: 12 minutos, dentro da faixa de 10 a 15 minutos. A divisão abaixo propõe seis minutos para cada autor; o tempo efetivo depende de ensaio e ainda não foi medido.

## Distribuição das falas

| Intervalo | Responsável | Conteúdo |
|---|---|---|
| 0:00 a 2:00 | Joey | Problema, relevância e base nacional |
| 2:00 a 4:00 | Paulo | Preparação e protocolo de avaliação |
| 4:00 a 6:00 | Joey | Algoritmos e seleção do trio |
| 6:00 a 8:00 | Paulo | Variantes, buscas e curvas |
| 8:00 a 10:00 | Joey | Teste final e análise dos erros |
| 10:00 a 12:00 | Paulo | Limitações, conclusão e contribuições |

## 1 Problema e dados - Joey - 0:00 a 2:00

Nosso projeto investiga uma pergunta: quanto conseguimos estimar da nota de Ciências da Natureza no ENEM usando apenas informações de perfil dos participantes? Essa pergunta é relevante porque permite comparar modelos de aprendizado de máquina em uma base nacional grande, com características socioeconômicas, escolares e demográficas. Também permite mostrar os limites dessas informações: prever uma nota não é medir toda a capacidade de uma pessoa nem explicar por que ela obteve aquele resultado.

Usamos os microdados do ENEM 2023 disponibilizados pelo Inep. O arquivo original contém 3.933.955 participantes e 76 colunas. Para a regressão, consideramos os 2.692.427 participantes com nota de Ciências da Natureza observada. Não confundimos nota ausente com nota zero: os 16.547 zeros foram mantidos. Também não excluímos participantes por idade, por serem treineiros ou por não terem nota em outra área.

A fonte foi conferida por integridade dos arquivos compactados e hashes. Além disso, comparamos todas as linhas e colunas do CSV normalizado com a base preparada, e os valores coincidiram integralmente. O complemento de competências da redação foi preservado, mas suas notas não entram nos preditores. O recorte é prever Ciências da Natureza pelo perfil, sem usar resultados de outras provas. Agora o Paulo explica como organizamos a avaliação para tornar as comparações consistentes.

## 2 Preparação e protocolo - Paulo - 2:00 a 4:00

A comparação usa quarenta atributos originais: uma variável numérica, Q005, e trinta e nove categóricas. As entradas descrevem aspectos do questionário socioeconômico, do perfil demográfico e escolar, a língua escolhida e a UF de realização da prova. A UF da prova não deve ser interpretada automaticamente como o estado onde a pessoa mora. Identificadores servem para controlar as partições, mas não ajudam o modelo a prever.

Reservamos vinte por cento dos participantes elegíveis para o teste final: 538.486 pessoas. Os outros 2.153.941 participantes formam o desenvolvimento. Nesse conjunto, usamos três dobras de validação cruzada, com os mesmos participantes em cada dobra para todos os modelos e semente 42. Cada modelo aprende em duas partes e é avaliado na terceira; repetimos isso até percorrer as três partes.

O cuidado central foi evitar vazamento de informação. Imputação de ausências, padronização, codificação de categorias, seleção de atributos e PCA são aprendidos somente com o treino da dobra. O teste final fica fora das escolhas de modelo e de parâmetros. Mesmo o Stacking, que combina previsões de outros modelos, usa previsões fora das dobras internas para treinar seu combinador.

Escolhemos o RMSE como critério principal, em pontos da nota. Ele penaliza mais os erros grandes. Complementamos com MAE, R², variação entre dobras e tempo observado. O desvio entre três dobras é descritivo; não equivale a um intervalo de confiança. Assim, a avaliação compara erros observados sem prometer precisão que os dados não sustentam.

## 3 Algoritmos e seleção - Joey - 4:00 a 6:00

Comparamos sete famílias: SVM, KNN, Bagging, Pasting, Random Forest, Boosting e Stacking. Todas foram implementadas como regressão, porque queremos estimar uma nota numérica, não classificar participantes. A SVM adotada é linear. O KNN considera vinte e cinco vizinhos e usa busca euclidiana exata, com uma implementação que reduz o custo de processamento sem recorrer a vizinhos aproximados.

Bagging e Pasting agregam árvores e diferem na amostragem: com reposição no primeiro e sem reposição no segundo. Random Forest acrescenta aleatoriedade na escolha de atributos. O Boosting usa árvores sequenciais para reduzir a perda. O Stacking combina uma regressão linear e uma árvore, usando Ridge como combinador. Mantivemos ainda referências simples: a média do treino, regressão linear, Ridge e árvore isolada. Uma comparação complexa precisa mostrar se supera alternativas simples.

Nas três dobras nacionais, entre os sete modelos solicitados, os menores RMSE médios foram 76,175 para Stacking, 76,577 para SVM e 76,643 para Random Forest. MAE e R² confirmaram esse trio e sua ordem. Por isso, esses três seguiram para a análise detalhada.

Existe uma distinção importante: quando incluímos as referências no ranking, os três primeiros passam a ser Stacking, Ridge e regressão linear. Não escondemos essa diferença. As buscas de parâmetros cobriram a união dos dois grupos, com cinco modelos. O resultado não autoriza dizer que ensembles sempre são melhores: a regressão linear continuou bastante competitiva.

## 4 Experimentos adicionais e curvas - Paulo - 6:00 a 8:00

Também verificamos se mudar a representação dos dados melhoraria a previsão. Criamos três atributos: computadores por morador, acesso digital e escolaridade máxima dos pais. A engenharia com Ridge reduziu o RMSE de aproximadamente 76,484 para 76,458. É um ganho pequeno. A seleção de atributos e o PCA pioraram as configurações avaliadas. No PCA, quarenta e cinco de duzentos e trinta e cinco componentes atingiram o limiar de oitenta por cento de variância, tanto para Ridge quanto para árvore.

Investigamos ponderação para dar mais peso às faixas de nota menos frequentes. Ela melhorou extremos na validação, mas piorou muito o resultado global do Ridge, chegando a RMSE de 125,202. Esse resultado negativo é relevante: priorizar uma parte da distribuição pode prejudicar as demais. Duas outras hipóteses retiraram, separadamente, o bloco socioeconômico e a UF da prova. Ambas aumentaram o erro, indicando contribuição preditiva dessas informações nesse protocolo, sem conclusão causal.

As buscas avaliaram doze configurações em cada um dos cinco modelos, totalizando sessenta configurações e cento e oitenta avaliações por dobra. Os ganhos foram mínimos. O Stacking mudou o alpha do combinador, mas a melhora foi de apenas menos de um milionésimo de ponto, sem relevância prática demonstrada.

Depois do congelamento, analisamos curvas com cinco tamanhos de treino. Os erros de treino e validação ficaram próximos, sem indicação de sobreajuste acentuado nesses tamanhos. Isso não prova generalização perfeita nem que os atributos disponíveis sejam suficientes. As curvas finais reaproveitam cálculos compatíveis já conferidos; não representam quarenta e cinco treinamentos completamente novos.

## 5 Teste final e erros - Joey - 8:00 a 10:00

Depois de fixar as receitas, ajustamos cada modelo em todo o desenvolvimento e avaliamos os mesmos 538.486 participantes do teste. Foram avaliados os três selecionados, a média do treino e a regressão linear de referência. Os outros quatro algoritmos tiveram validação cruzada completa, mas não foram aplicados ao teste reservado, conforme o protocolo. Portanto, não afirmamos que todos os sete passaram por uma avaliação final de teste.

O Stacking teve o menor erro entre os modelos avaliados: RMSE de 76,190 pontos, MAE de 55,325 e R² de aproximadamente 0,25. A média de referência teve RMSE de 87,959. Isso representa uma redução relativa de 13,38 por cento no RMSE. A regressão linear, porém, ficou próxima: RMSE de 76,517. Já SVM e Random Forest tiveram 76,622 e 76,658. O ganho do Stacking deve ser comparado com a maior complexidade e o custo de ajuste observado.

A média global não conta toda a história. Para notas abaixo de quatrocentos, o RMSE do Stacking foi 154,31; para notas a partir de setecentos, 160,74. No intervalo de quatrocentos a quinhentos, foi 48,12. O modelo tende a superestimar notas baixas e subestimar notas altas. Também examinamos os erros por escola, renda e UF, sempre informando o tamanho dos grupos.

Como o problema é regressão, usamos notas observadas versus previstas, resíduos e erros por faixa. Uma matriz de confusão não é a ferramenta adequada para esse alvo contínuo. As métricas finais foram novamente recompostas das previsões salvas durante a revisão da entrega.

## 6 Limitações e conclusão - Paulo - 10:00 a 12:00

Nossa conclusão é que o Stacking foi o melhor dos modelos efetivamente avaliados no teste pelo critério escolhido. Ele melhorou o RMSE em relação à média e manteve a liderança do trio entre desenvolvimento e teste. Ao mesmo tempo, a regressão linear obteve desempenho próximo e exigiu menos tempo de ajuste nesta execução. Isso impede uma conclusão simplista de que o modelo mais complexo é sempre a melhor escolha prática.

A avaliação tem limites. Usamos uma única edição do ENEM e uma divisão aleatória de participantes. Isso testa consistência dentro de 2023, mas não demonstra que o modelo funcionará igualmente em outro ano ou em escolas inéditas. As informações são observacionais e parte delas é autodeclarada. Diferenças entre grupos não isolam causas. O R² próximo de 0,25 também mostra que o perfil disponível não explica toda a variação das notas; sozinho, esse número não prova subajuste.

As contribuições do trabalho são a comparação nacional com partições consistentes, a preservação de zeros e ausências de forma distinta, a avaliação de alternativas que melhoraram e pioraram o desempenho e a documentação de código, parâmetros e evidências. A revisão confirmou as execuções e separou claramente validação cruzada, curvas e teste final.

Como próximos estudos, propomos avaliar outras edições e partições por grupos, comparar perdas mais robustas e investigar intervalos de predição, sempre com um novo protocolo e um teste reservado. Essas propostas ainda não foram executadas. O principal aprendizado é que uma boa comparação precisa expor tanto o ganho global quanto os casos em que o modelo erra mais.

## Números para consulta durante o ensaio

| Modelo no teste | RMSE | MAE | R² |
|---|---|---|---|
| Stacking | 76,190 | 55,325 | 0,2497 |
| Linear de referência | 76,517 | 55,616 | 0,2433 |
| SVM linear | 76,622 | 55,538 | 0,2412 |
| Random Forest | 76,658 | 55,821 | 0,2405 |
| Média | 87,959 | 66,285 | aproximadamente zero |

Fonte: previsões finais persistidas do projeto, Inep/ENEM 2023. Os cinco modelos usam exatamente o mesmo teste; valores arredondados para apresentação.

## Perguntas prováveis e respostas

**Todos os sete modelos foram realmente executados?** Sim, em três dobras nacionais cada: vinte e uma avaliações. A seleção, as variantes e as buscas têm registros e hashes próprios. Isso é diferente de aplicar todos ao teste reservado.

**Todos passaram pelo teste final?** Não. Foram avaliados Stacking, SVM, Random Forest, média e linear. KNN, Bagging, Pasting, Boosting, Ridge e árvore isolada não tiveram teste final neste protocolo. Não se deve ampliar a seleção depois de olhar o teste.

**Por que preservar nota zero?** Zero é um resultado observado e faz parte do problema definido. Excluí-lo alteraria a população e poderia reduzir artificialmente o erro. Ausência de nota tem outro tratamento: fica fora da supervisão.

**Por que usar PCA se piorou?** A hipótese era compactar a representação mantendo informação útil. Os quarenta e cinco componentes preservaram a variância definida, mas não melhoraram os regressores avaliados. Variância explicada não garante capacidade preditiva.

**O Stacking ganhou de forma estatisticamente significativa?** Não foi realizado teste de significância nem calculado intervalo de confiança. Podemos afirmar que apresentou o menor erro observado nesse protocolo, com vantagem pequena sobre a linear.

**As curvas provam que não existe overfitting?** Não. Mostram pequenas diferenças entre treino e validação nos tamanhos usados; o menor treino já tem cerca de cento e quarenta e três mil participantes. Não descrevem amostras pequenas nem outras populações.

**Por que não usar as competências da redação?** São resultados de avaliação e ficam fora do conjunto permitido de preditores de perfil. O arquivo foi validado e preservado, sem ser unido à modelagem.

**Qual é a evidência de execução?** Manifestos concluídos, resultados por dobra, previsões persistidas, hashes, curvas com identidade dos subconjuntos e uma nova recomposição das métricas de busca e teste. A suíte de software é uma verificação distinta desses experimentos.

## Ensaio e fontes

Cronometrar uma leitura em voz alta, incluindo pausas e transições; ajustar a fala para 10 a 15 minutos sem omitir as limitações. As marcações de dois minutos são uma proposta, não um ensaio realizado. Os dois autores devem conseguir explicar o protocolo e os resultados de qualquer bloco.

Repositório: https://github.com/JoeyAlanS/trab2-aprendizado-de-maquina

Dados: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem

Evidência da revisão: resultados/ciencias_natureza/checkpoint-7-2026-11-07/auditoria_experimentos.json e cobertura_execucoes.csv. Artigo e referências técnicas: artigo.tex no pacote Overleaf. Não usar resultados arquivados como não validados.
