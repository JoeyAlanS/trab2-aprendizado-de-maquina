# Checkpoint 3 — protocolo das curvas de aprendizado

Registrado em 06/11/2026, antes dos 45 ajustes. Esta página descreve o procedimento;
não comprova a conclusão dos experimentos. Resultados só serão publicados depois de
conferir as quinze avaliações de cada modelo.

## População e modelos

- Alvo de regressão: `NU_NOTA_CN` no ENEM 2023.
- Desenvolvimento nacional: 2.153.941 participantes; teste de 538.486 reservado.
- Trio recebido do Checkpoint 2: Stacking, SVM linear e Random Forest.
- Mesmas 40 entradas originais; configurações iniciais já registradas. Não há busca
  de hiperparâmetros nesta etapa. As buscas do enunciado permanecem pendentes.
- Três dobras externas persistidas; os participantes de validação de cada dobra
  permanecem os mesmos em todos os pontos e em todos os modelos.

## Construção das curvas

Para cada dobra, os índices elegíveis para treino são permutados por
`numpy.random.RandomState(42)`. Selecionam-se os prefixos de 10%, 25%, 50%, 75% e 100%,
com tamanho inteiro arredondado para baixo. Os subconjuntos são cumulativos.
Os índices selecionados são ordenados novamente na ordem da fonte antes do ajuste.
Isso mantém a composição aleatória e permite reproduzir o ajuste do Checkpoint 1
quando a fração chega a 100%.

| Fração | Participantes por treino |
|---|---:|
| 10% | 143.596 |
| 25% | 358.990 |
| 50% | 717.980 |
| 75% | 1.076.970 |
| 100% | 1.435.960 ou 1.435.961 |

Cada validação contém 717.980 ou 717.981 participantes. Os IDs, as contagens e seus
hashes são registrados em `protocolo.json`; a execução reconstrói e confere o plano.
São 3 modelos × 3 dobras × 5 tamanhos = **45 ajustes**, cada um com métricas reais de
treino e validação. Transformações são ajustadas somente no respectivo subconjunto.
No Stacking, os pipelines também são reajustados nas três dobras internas.

## Execução e retomada

`src/enem_base/learning_curves.py` implementa o procedimento. A Random Forest utiliza
seis trabalhadores para suas árvores; sua configuração de referência usa dois.
Essa diferença de execução está explícita no protocolo; número de árvores, sementes,
profundidade, folha mínima e demais parâmetros estatísticos permanecem iguais.
A verificação prévia com 10.000 participantes reais de treino e 2.048 de validação
produziu árvores idênticas e diferença máxima de previsão de 2,274 × 10⁻¹³.
Essa sondagem técnica não integra os 45 pontos científicos.

A execução admite duas famílias simultâneas: Random Forest e, em sequência, SVM e
Stacking. Bibliotecas numéricas têm limite de dois threads. Os tempos observados
dependem do compartilhamento de recursos; não são benchmark isolado de velocidade.

Cada ajuste é salvo localmente antes de calcular as métricas. Cada ponto concluído
possui JSON atômico com contexto, parâmetros, hashes, avisos e métricas. A retomada
recusa diferenças de código numérico, dependências, origem, partições ou configuração.
Uma trava impede dois processos de escrever na mesma família. Os modelos serializados
ficam em `modelos_ajustados/`, ignorados pelo Git; são artefatos locais confiáveis, não
arquivos para abrir de fontes externas.

Na raiz do repositório:

```bash
.venv/bin/python scripts/executar_checkpoint3.py \
  --study configs/ciencias_natureza.toml \
  --selection resultados/ciencias_natureza/checkpoint-2-2026-11-06 \
  --output resultados/ciencias_natureza/checkpoint-3-2026-11-06 \
  --prepare-only --forest-jobs 6

.venv/bin/python -u scripts/executar_checkpoint3.py \
  --study configs/ciencias_natureza.toml \
  --selection resultados/ciencias_natureza/checkpoint-2-2026-11-06 \
  --output resultados/ciencias_natureza/checkpoint-3-2026-11-06 \
  --models svm random_forest stacking --resume
```

O segundo comando é sequencial por padrão. Para reproduzir a execução concorrente,
rodar `--models random_forest` e `--models svm stacking` em dois processos separados,
depois de preparar o protocolo uma única vez. Uma nova reprodução deve usar outra pasta.
`--resume` confere e preserva pontos existentes; não autoriza substituir resultados.

## Critérios de validação e análise

Conferir os 45 pontos, ausência de sobreposição entre treino e validação, composição
cumulativa, hashes idênticos entre modelos, métricas finitas e parâmetros congelados.
Comparar as nove avaliações de validação em 100% às do Checkpoint 1, com tolerância
absoluta de 10⁻⁸. Recalcular médias e desvios populacionais (`ddof=0`) das três dobras.
Inspecionar figuras PNG de 300 dpi e SVG, com títulos, eixos, legendas e fonte.

Analisar a diferença entre erros de treino e validação, a evolução com mais dados e
o ganho de 75% a 100%. A dispersão entre três dobras é descritiva, não intervalo de
confiança; as mesmas dobras já foram usadas para selecionar o trio. Generalização
aqui significa desempenho interno nos participantes retidos dessas dobras. A
avaliação independente no teste pertence ao Checkpoint 4. Não inferir causalidade,
significância estatística, desempenho de outros anos ou ausência definitiva de viés.

Referências do mecanismo: [curvas de aprendizado no scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.learning_curve.html)
e [paralelismo da Random Forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).
