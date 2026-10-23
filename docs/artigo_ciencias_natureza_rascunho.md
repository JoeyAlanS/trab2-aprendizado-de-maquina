# Estimativa da nota de Ciências da Natureza no ENEM 2023 a partir do perfil dos participantes

**Rascunho em desenvolvimento, iniciado em 21/10/2026.** Não é o artigo final em PDF.
Autores, afiliação, equipe e link do repositório: a preencher. A formatação ABNT e o
limite final de dez páginas serão conferidos após completar os experimentos exigidos.

## Resumo provisório

Este trabalho investiga em que medida informações socioeconômicas, escolares e
demográficas permitem estimar a nota de Ciências da Natureza no ENEM 2023. Utiliza-se
a base nacional publicada pelo Inep, com 3.933.955 registros e 76 variáveis. O conjunto
supervisionado contém 2.692.427 participantes com nota observada na área, sem exigir
notas das demais provas. A avaliação separa 80% para desenvolvimento e 20% para teste,
com semente 42, e adota três dobras fixas de validação cruzada no desenvolvimento.
Uma representação inicial com 40 variáveis candidatas é comparada à previsão pela
média do treino. As transformações são ajustadas dentro de cada dobra, prevenindo
vazamento de informação. Resultados completos, aprofundamentos e conclusão serão
incorporados após a execução das etapas restantes. O teste permanece reservado.

Palavras-chave provisórias: ENEM; Ciências da Natureza; regressão; perfil socioeconômico;
validação cruzada.

## 1 Introdução

Os microdados do ENEM reúnem informações sobre participantes, questionário
socioeconômico e resultados das provas. A publicação possibilita investigar relações
entre características de perfil e desempenho observado. A disponibilidade dessas
variáveis, entretanto, não assegura previsão individual precisa e não autoriza uma
interpretação causal das associações encontradas (INEP, 2024).

A questão desta pesquisa é: em que medida o perfil socioeconômico, escolar e
demográfico permite estimar a nota de Ciências da Natureza dos participantes do ENEM
2023? O objetivo é comparar modelos de regressão, quantificar ganhos em relação a uma
referência simples e examinar erros e limitações. A comparação deve considerar também
complexidade e custo, evitando interpretar diferenças pequenas entre modelos como
evidência de melhoria relevante sem observar sua variação entre dobras.

## 2 Metodologia

### 2.1 Dados e população de estudo

O pacote oficial de 2023 foi obtido no portal do Inep em 21 de outubro de 2026. O ZIP
teve sua integridade verificada e os originais foram preservados. O CSV nacional contém
3.933.955 linhas e 76 colunas, conferidas pelo processamento integral. Não foi usada
amostra de conveniência. A importação em lotes de 50.000 registros resultou em 79 partes
Parquet; não houve exclusão de linhas nem identificadores duplicados.

O alvo é NU_NOTA_CN. Há 2.692.427 registros com nota observada e 1.241.528 sem essa
nota. Estes últimos integram o diagnóstico da fonte, mas não o treinamento ou a
avaliação supervisionados. Não houve imputação do alvo nem conversão de ausência em
zero. As 16.547 notas zero observadas na população elegível foram preservadas.
Treineiros e diferentes faixas etárias foram mantidos.

A população avaliada corresponde aos registros elegíveis da publicação de 2023.
Exclusões realizadas pelo próprio Inep na divulgação simplificada são uma limitação
da fonte, descrita no Leia-me, e não um filtro adicional criado pelo projeto.

### 2.2 Preparação e representação inicial

Identificadores e códigos foram importados como texto; somente colunas declaradas
numéricas foram convertidas. A preparação normaliza espaços externos e marcadores
explícitos de ausência, sem preencher valores aprendidos da população. A fonte, as
configurações, as partes preparadas e as partições possuem hashes SHA-256 registrados.

O dicionário oficial foi conferido nas 76 variáveis. A representação inicial contém
Q005 como variável numérica e 39 candidatas categóricas, incluindo perfil demográfico,
situação e contexto escolar, UF de prova, opção de língua e alternativas do questionário.
Os detalhes e a lista exata estão no contrato `configs/ciencias_natureza.toml` e em
`dicionario_ciencias_natureza.md`. Q004 foi tratada como categórica devido às alternativas
A-F, apesar da declaração inconsistente de tipo numérico no dicionário.

Não entram em X notas de qualquer área, competências da redação, respostas, gabaritos,
presença, situação da redação, identificador ou ano constante. Códigos de prova também
foram excluídos. A UF descreve o local de prova e não é interpretada como residência.
Alternativas como não respondeu, não declarado e não sei são preservadas e distintas
de células ausentes.

No Pipeline de cada regressor, a preparação numérica usa mediana do treino e
padronização; as categorias recebem marcador explícito de ausência e one-hot, com
tratamento de categorias inéditas. Toda aprendizagem de parâmetros de transformação
ocorre apenas no treino da dobra. O baseline usa a média do alvo no treino, sem usar
as características do participante (SCIKIT-LEARN, documentação).

### 2.3 Protocolo de avaliação

A divisão aleatória, com random_state=42, reservou 538.486 participantes (20%) ao teste
e 2.153.941 (80%) ao desenvolvimento. As três dobras de desenvolvimento usam
KFold(n_splits=3, shuffle=True, random_state=42), com IDs e rótulos de dobra persistidos.
Suas validações contêm 717.981, 717.980 e 717.980 participantes, respectivamente.
Não há outra parcela fixa de validação. Os IDs não são entradas de modelos.

O RMSE é a métrica principal, com MAE e R² complementares, todos calculados na escala
original. Reportam-se média e desvio padrão nas três dobras, usando ddof=0, além dos
tempos e tamanhos. Os resultados do teste só serão calculados após congelar a solução
e serão apresentados separadamente. O baseline, a regressão linear sem regularização
e a solução final serão avaliados nos mesmos participantes do teste.

### 2.4 Experimentos e etapas em execução

A primeira comparação contém DummyRegressor pela média, regressão linear sem
regularização, Ridge e árvore de decisão. Trata-se de uma etapa preliminar da comparação
obrigatória. O catálogo implementado também contém SVM linear, KNN, bagging, pasting,
Random Forest, boosting e stacking; sua disponibilidade não equivale a execução.

Para completar a metodologia, ainda são necessários: três features criadas e seleção;
PCA em dois regressores; balanceamento adequado à regressão; busca nos três melhores
regressores distintos com pelo menos dez configurações válidas por modelo; duas hipóteses
de aprofundamento; curva de aprendizado e avaliação final do teste. Essas etapas não
são presumidas concluídas neste rascunho.

## 3 Resultados preliminares

No desenvolvimento, a média da nota é 495,77 e a mediana é 493,9; 13.236 participantes
apresentam nota zero. A figura de distribuição preserva esses resultados observados.
Os campos de dependência administrativa, localização e situação da escola apresentam
73,09% de células ausentes; TP_ENSINO apresenta 61,66%. As demais 36 candidatas não
apresentam células vazias, o que não significa ausência de alternativas de desconhecimento.

A análise descritiva por TP_ESCOLA registra médias de 473,60 para escola pública,
548,42 para privada e 499,93 para não respondeu, com 666.620, 177.424 e 1.309.897
participantes do desenvolvimento, respectivamente. A comparação é descritiva e não
controla confundidores; não estima efeito causal do tipo de escola.

A primeira comparação foi concluída nas três dobras, sem usar o teste. Os resultados
preliminares são apresentados abaixo, com média e desvio padrão (ddof=0).

| Modelo | RMSE (média ± DP) | MAE (média ± DP) | R² (média ± DP) | Tempo das três dobras (s) |
|---|---:|---:|---:|---:|
| Ridge (alpha=1) | 76,48 ± 0,05 | 55,62 ± 0,04 | 0,243251 ± 0,000488 | 89,33 |
| Linear sem regularização | 76,48 ± 0,05 | 55,62 ± 0,04 | 0,243247 ± 0,000491 | 118,26 |
| Árvore (profundidade 12) | 77,17 ± 0,04 | 56,29 ± 0,02 | 0,229672 ± 0,000539 | 556,22 |
| Baseline pela média | 87,92 ± 0,08 | 66,24 ± 0,04 | -0,000002 ± 0,000001 | 0,09 |

Linear e Ridge reduziram o RMSE em aproximadamente 13,01% em relação à previsão
pela média. A diferença entre esses dois modelos é inferior a 0,001 ponto, muito menor
que a variação entre dobras; não sustenta uma conclusão de superioridade relevante do
Ridge nesta configuração. A árvore teve erro maior e custo mais alto. As configurações
iniciais não substituem a comparação completa nem as buscas previstas. Todas as
validações incluíram os participantes elegíveis das dobras, sem amostra de conveniência.

Estão disponíveis figuras de distribuição, ausências, tipo de escola e comparação
inicial. Os tempos acima incluem ajuste, previsão e métricas por dobra, sem carga
inicial dos dados. O baseline teve R² ligeiramente negativo, próximo de zero.

## 4 Discussão provisória e limitações

A disponibilidade do alvo limita a população supervisionada aos participantes com
nota observada. Campos escolares têm cobertura reduzida e alternativas de não informação
podem representar processos de coleta relevantes. Essas condições devem ser examinadas
na interpretação das diferenças entre modelos e grupos.

O protocolo avalia participantes da mesma edição do exame; não demonstra generalização
para outras edições ou para escolas e municípios inéditos. A previsão estatística a
partir do perfil não determina capacidade individual. A ausência de notas e a cobertura
dos campos também impedem extrapolar automaticamente os resultados aos inscritos sem
nota observada.

O ajuste ainda não foi diagnosticado pela curva de aprendizado. Não se conclui subajuste
apenas pelo R², nem se presume que maior complexidade ou mais dados resolverão os erros.
As diferenças finais devem ser relacionadas à variação nas dobras, ao custo e às análises
de resíduos. Resultados sem melhoria também serão registrados e discutidos.

## 5 Conclusão

A preencher após completar os experimentos e realizar a avaliação final, sem escolher
ou reajustar modelos com base no teste. O início do estudo já estabeleceu população,
rastreabilidade, partições, exploração e comparação inicial reproduzível.

## Referências iniciais

INSTITUTO NACIONAL DE ESTUDOS E PESQUISAS EDUCACIONAIS ANÍSIO TEIXEIRA. **Microdados do
Enem 2023**. Brasília: Inep, 2024. Disponível em:
https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem.
Acesso em: 21 out. 2026. Dicionário e Leia-me integrantes do pacote oficial.

SCIKIT-LEARN. **Common pitfalls and recommended practices**. Documentação da versão
utilizada, 1.9.1. Disponível em: https://scikit-learn.org/stable/common_pitfalls.html.
Acesso em: 21 out. 2026.

As referências específicas dos métodos restantes e a normalização final serão
completadas conforme seu uso. O texto deve remeter ao repositório para detalhes e
manter o limite total de dez páginas do PDF final.
