# Checkpoint 3 — curvas de aprendizado

**Estado: parcial, em execução.** Registro de acompanhamento de 06/11/2026,
19h35 (America/Fortaleza): 36 de 45 pontos concluídos. A existência deste relatório
não encerra o checkpoint. A comparação dos três, os gráficos finais e a validação
integral ainda dependem dos nove pontos restantes.

## O que está implementado

O módulo `src/enem_base/learning_curves.py` e o executor
`scripts/executar_checkpoint3.py` recebem a seleção validada do Checkpoint 2:
Stacking, SVM linear e Random Forest. São cinco tamanhos (10%, 25%, 50%, 75%, 100%)
em cada uma das três dobras, totalizando 45 ajustes. Cada pipeline é reajustado no
respectivo subconjunto. Os IDs de validação permanecem fixos; os prefixos aleatórios
de treino são cumulativos e compartilhados entre os modelos.

A população de desenvolvimento contém 2.153.941 participantes do ENEM 2023, com
NU_NOTA_CN observada. São mantidas as mesmas 40 entradas e as configurações iniciais
do Checkpoint 2. A Random Forest usa seis trabalhadores, em vez dos dois da
configuração de referência; essa diferença operacional foi registrada e validada.
As buscas de hiperparâmetros do enunciado continuam pendentes.

**100% significa todo o treino da dobra**, aproximadamente 1,436 milhão de pessoas;
a validação contém aproximadamente 718 mil. Não significa ajustar aqui sobre todo
o desenvolvimento. Os 538.486 participantes do teste final permanecem reservados.

O [protocolo completo](checkpoint-3-protocolo.md) explica os tamanhos, sementes,
contagens, verificações, retomada e comandos. O publicador
`scripts/publicar_checkpoint3.py` exige os 45 pontos completos, confere métricas e
hashes, compara os pontos de 100% ao Checkpoint 1 e prepara tabelas e figuras.

## Curva já concluída: SVM linear

Médias e desvios populacionais (`ddof=0`) entre três dobras. RMSE e MAE estão em
pontos da nota; R² é adimensional. O desvio não é intervalo de confiança.

| Fração | Treino por dobra (mínimo) | RMSE treino ± DP | RMSE validação ± DP | MAE validação | R² validação |
|---|---:|---:|---:|---:|---:|
| 10% | 143.596 | 76,775 ± 0,156 | 76,686 ± 0,087 | 55,563 | 0,239 |
| 25% | 358.990 | 76,773 ± 0,234 | 76,649 ± 0,053 | 55,515 | 0,240 |
| 50% | 717.980 | 76,719 ± 0,146 | 76,665 ± 0,054 | 55,508 | 0,240 |
| 75% | 1.076.970 | 76,665 ± 0,077 | 76,668 ± 0,036 | 55,504 | 0,240 |
| 100% | 1.435.960 | 76,570 ± 0,027 | 76,577 ± 0,059 | 55,519 | 0,241 |

Ao passar de 10% a 100%, o RMSE médio de validação diminuiu 0,109 ponto; de 75% a
100%, diminuiu 0,091. No treino completo, o RMSE de treino é 76,570 e o de validação,
76,577, uma diferença de aproximadamente 0,007 ponto. A curva apresenta pequenas
oscilações e ganho limitado com mais dados nesta configuração, sem uma grande
separação entre treino e validação. Isso não comprova que a configuração seja ótima
nem identifica, isoladamente, se a limitação restante vem da representação, da
capacidade do modelo ou de variabilidade não explicada nas notas.

A análise usará a relação entre os dois erros e a evolução com o tamanho do treino,
conforme a [documentação de curvas de aprendizado do scikit-learn](https://scikit-learn.org/stable/modules/learning_curve.html).
As mesmas dobras foram usadas na seleção do trio; a estimativa independente no teste
pertence ao Checkpoint 4. Não há conclusão sobre desempenho em outros anos.

## Verificações aprovadas até este registro

- Protocolo, seleção, código numérico, dependências e partições compatíveis.
- Quinze subconjuntos reconstruídos independentemente a partir dos IDs persistidos:
  composição cumulativa, separação de treino/validação e hashes confirmados.
- Retomada da SVM: quinze pontos reutilizados, nenhum novo ajuste e arquivos idênticos.
- Recomposição independente de RMSE, MAE e R² a partir dos modelos salvos dos três
  algoritmos, usando treino e validação completos do primeiro ponto (10%, dobra 0).
  Diferença máxima de métricas: 4,263 × 10⁻¹⁴; previsões em blocos e chamada única
  diferiram no máximo 2,274 × 10⁻¹³ nas 2.048 linhas reais conferidas.
- Seis pontos disponíveis com 100% de treino reproduziram o Checkpoint 1: três da
  SVM, dois da Random Forest e um do Stacking. A conferência final exige os nove.
- Publicação incompleta recusada sem criar resultados; 36 pontos sem avisos.

As execuções anteriores foram interrompidas antes de completar todas as curvas.
Ao retomar às 19h16, foram preservados 32 pontos e reiniciados os ajustes ainda não
salvos. Os tempos por ponto incluem o ajuste e a avaliação concluídos; trabalho
interrompido antes de ser registrado e intervalos sem execução não entram nesses
valores. Como houve duas famílias simultâneas, os tempos não são benchmark isolado.

## Pendências deste checkpoint

Concluir três pontos da Random Forest e seis do Stacking; conferir as nove
avaliações em 100%; agregar as três dobras em cada tamanho; gerar e inspecionar
curvas, comparação de métricas e diferenças entre treino e validação; finalizar
a análise de possível overfitting/underfitting e registrar o encerramento.

Diretório das evidências e resultados:
`resultados/ciencias_natureza/checkpoint-3-2026-11-06/`.
O Checkpoint 4 ainda não foi iniciado.
