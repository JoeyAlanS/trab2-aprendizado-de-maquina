# Checkpoint 5 — coleção final de gráficos

Concluído em 07/11/2026. A coleção reúne **17 figuras em PNG de 300 dpi e SVG**, **14 tabelas CSV**, catálogo de fontes e galeria HTML local com filtros. Foram criadas seis figuras a partir dos dados e resultados persistidos e incorporadas onze figuras já aprovadas do Checkpoint 4, com igualdade de hashes conferida.

[Abrir a galeria](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/index.html). A galeria funciona localmente, sem servidor ou conexão externa: abrir `index.html` no navegador. O [pacote de entrega ZIP](../output/checkpoint-5-visualizacoes-2026-11-07.zip) foi conferido por CRC e hashes; extrair a pasta inteira para preservar as imagens, tabelas e links.

O código desta etapa publica resultados existentes. Não executou treinamento, seleção de hiperparâmetros ou nova avaliação no teste. A distribuição foi recomposta dos Parquets, restringindo os IDs ao desenvolvimento; o novo gráfico de resíduos usa exclusivamente as previsões salvas no Checkpoint 4.

## Figuras e interpretações

| Figura | População / etapa | O que mostra |
|---|---|---|
| [01_distribuicao](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/01_distribuicao.png) | Desenvolvimento | Todos os 2.153.941 participantes do desenvolvimento; 13.236 notas zero preservadas. Ausência de nota não foi convertida em zero. Intervalos de 25 pontos. |
| [02_sete_algoritmos](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/02_sete_algoritmos.png) | Desenvolvimento | Mesmas três dobras e 40 entradas. Barras de erro: DP populacional entre dobras; não intervalos de confiança. |
| [03_trio_selecionado](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/03_trio_selecionado.png) | Desenvolvimento | Seleção do Checkpoint 2 entre os sete. Eixos ampliados, sem barras partindo de zero; a seleção não usa o teste. |
| [04_catalogo_variantes](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/04_catalogo_variantes.png) | Desenvolvimento | Inclui baseline e resultados sem melhoria. As variantes são comparações do modelo indicado, não novas buscas sobre o teste. Tempos completos estão na tabela. |
| [05_pca](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/05_pca.png) | Desenvolvimento | PCA centrado, ajustado apenas no treino de cada dobra. Ridge e árvore retiveram 45 componentes para alcançar pelo menos 80% da variância; as seis curvas quase coincidem. |
| [06_buscas](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/06_buscas.png) | Desenvolvimento | Cinco modelos, 12 configurações por modelo. Inclui o trio solicitado e os três melhores do catálogo ampliado. |
| [07_ganhos_buscas](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/07_ganhos_buscas.png) | Desenvolvimento | Ganhos muito pequenos; a mudança do Stacking não demonstrou relevância prática ou estatística. |
| [08_curvas_finais](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/08_curvas_finais.png) | Desenvolvimento | Treino e validação em cinco tamanhos, nas três dobras; receitas fixadas antes do teste. |
| [09_teste](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/09_teste.png) | Teste | Trio, baseline e linear nos mesmos 538.486 participantes. A linear tem RMSE menor que SVM e Random Forest. |
| [10_cv_teste](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/10_cv_teste.png) | Teste | CV em três dobras e teste em modelos reajustados no desenvolvimento completo; populações de treino distintas. |
| [11_observado_previsto](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/11_observado_previsto.png) | Teste | Todos os participantes; mesma escala de células e linha da previsão perfeita para o trio. |
| [12_distribuicao_residuos](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/12_distribuicao_residuos.png) | Teste | Intervalos comuns e todos os resíduos; a média global não descreve os erros extremos. |
| [13_faixas](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/13_faixas.png) | Teste | Faixas fixadas no desenvolvimento e tamanhos dos grupos. Erros maiores nas notas extremas. |
| [14_escola](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/14_escola.png) | Teste | Códigos de TP_ESCOLA e contagens; associação observacional, sem inferência causal. |
| [15_uf](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/15_uf.png) | Teste | UF da prova não é necessariamente residência; contagens por UF na tabela. |
| [16_renda](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/16_renda.png) | Teste | Categorias de Q006; contagens na tabela. Diferenças não determinam a capacidade individual. |
| [17_residuos_previsto](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/figuras/17_residuos_previsto.png) | Teste | Todos os 538.486 participantes agregados em células, sem amostra ou corte de extremos. Resíduo negativo: superestimação. A dispersão remanescente limita a precisão individual. |

## Cobertura dos requisitos

| Requisito | Evidência na coleção |
|---|---|
| Comparação geral dos sete algoritmos | Figura 02: RMSE, MAE e R² com DP nas mesmas três dobras |
| Comparação dos três selecionados | Figura 03: detalhe da seleção inicial; figuras 09–10: avaliação final |
| Curvas de aprendizado | Figura 08: treino, validação e DP para o trio nas configurações finais |
| Resultados finais | Figuras 09–12 e 17; tabela `comparacao_teste.csv`, com cinco modelos, métricas e tempos |
| Erros por faixa e por grupos | Figuras 13–16; tabela `erros_grupos.csv`, com 260 linhas e contagens |
| Distribuição e zeros no desenvolvimento | Figura 01 e tabelas de distribuição/população |
| Modelos com baseline e antes/depois das buscas | Figuras 04, 06 e 07; tabelas de CV e das 60 configurações |
| Variância acumulada do PCA | Figura 05 e tabela com seis curvas completas dos 235 componentes |
| Observado versus previsto e padrões dos resíduos | Figuras 11, 12 e 17; linha de previsão perfeita e resíduo zero |
| Tabela acadêmica de métricas e tempo | `comparacoes_cv_completas.csv` e `comparacao_teste.csv`, separadas |

Os seis grupos de figuras exigidos pelo enunciado estão cobertos. A disposição desses painéis nas até dez páginas do artigo será realizada no Checkpoint 6. A regressão de uma nota contínua não requer matriz de confusão: foram usados resíduos, densidades e erros por grupo.

## Leitura crítica dos resultados

O Stacking permanece o melhor do trio e dos cinco avaliados pelo RMSE de teste: **76,190**, com redução de **13,38%** frente ao baseline. A linear de referência apresenta RMSE menor que SVM e Random Forest. As buscas trouxeram ganhos muito pequenos, sem demonstração de relevância prática ou significância estatística.

A distribuição do desenvolvimento contém **2.153.941 participantes**, incluindo **13.236 notas zero**. O PCA atingiu o limiar predefinido de 80% com 45 componentes em cada ajuste de Ridge e árvore. A figura apresenta os 235 componentes diagnosticados, com o ponto de escolha indicado; não houve novo ajuste do PCA.

Os gráficos do teste usam os **538.486 participantes**, mantendo **3.311 notas zero**. A faixa diagonal inferior no novo gráfico de resíduos corresponde aos zeros observados: nesse caso, observado − previsto = −previsto. Esses registros não foram removidos. Os erros maiores nos extremos das notas, já documentados no Checkpoint 4, permanecem visíveis. Diferenças entre grupos são descritivas e não demonstram causalidade.

As barras de erro e faixas representam DP populacional entre três dobras, não intervalos de confiança. Os tempos de CV somam execuções das dobras; os tempos de teste distinguem o reajuste completo e a previsão. Eles foram observados sob compartilhamento de recursos e não constituem um benchmark isolado.

## Código e reprodução

- [Gerador da coleção](../scripts/publicar_checkpoint5.py).
- [Validador dos arquivos reais](../scripts/validar_checkpoint5.py).
- [Catálogo das figuras e tabelas](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/catalogo.json).
- [Validação de integridade e cobertura](../resultados/ciencias_natureza/checkpoint-5-2026-11-07/validacao.json).

Executar na raiz do repositório. Para reproduzir a coleção, escolher um diretório novo; o gerador recusa sobrescrever uma saída existente:

```bash
.venv/bin/python scripts/publicar_checkpoint5.py \
  --output resultados/ciencias_natureza/checkpoint-5-reproducao

.venv/bin/python scripts/validar_checkpoint5.py \
  --collection resultados/ciencias_natureza/checkpoint-5-reproducao
```

Uma reprodução nova precisa de revisão visual antes de ser declarada aprovada. Para conferir a coleção já entregue, executar somente o validador com `--collection resultados/ciencias_natureza/checkpoint-5-2026-11-07`.

## Verificações executadas

Foram conferidos 149 hashes de entradas, 17 PNGs com resolução mínima de 300 dpi, 17 SVGs válidos e 90 links locais da galeria. Os gráficos foram inspecionados quanto a títulos, eixos, legendas, contagens, fontes e sobreposição. A galeria foi aberta no navegador e os filtros mostraram 17 figuras no total, 8 de desenvolvimento e 9 de teste.

As 18 comparações de CV foram verificadas contra suas 54 dobras; a coleção preserva as cinco linhas do teste separadas. As contagens do histograma e das células de resíduos cobrem as populações completas. Os gráficos copiados são idênticos às publicações aprovadas. Os relatórios e resultados selados dos Checkpoints 1–4 permanecem preservados.

Durante a preparação, a leitura do histograma foi otimizada para filtrar os IDs uma única vez. O publicador de PCA foi corrigido para distinguir os 235 componentes diagnosticados dos 45 selecionados. As tentativas incompletas foram preservadas em `historico/2026-11-07/`. Nenhuma dessas correções mudou os modelos ou resultados científicos. Não foram criados arquivos de testes automatizados nem resultados fictícios.

## Arquivos de origem e próximos passos

O CSV bruto e o ZIP original são, respectivamente, `MICRODADOS_ENEM_2023.csv` e `microdados_enem_2023.zip`. Continuam ausentes nesta cópia; a base limpa recuperada permanece disponível e conferida. [Explicação completa dos arquivos](origem-arquivos-enem.md).

O Checkpoint 5 está concluído. O próximo passo é o **Checkpoint 6: redação e formatação do artigo científico em ABNT**. Depois, o Checkpoint 7 produzirá os PDFs de acompanhamento e pitch. Esses documentos e sua apresentação ainda não estão concluídos. Não houve commit, push ou publicação externa.
