# Coleção final de gráficos — Checkpoint 5

Abrir `index.html` em um navegador. PNGs em 300 dpi e SVGs com texto editável; densidades mantêm células rasterizadas para controlar o tamanho. Tabelas CSV preservam a precisão numérica. Nenhum treinamento ou nova avaliação do teste foi executado.

| Figura | Etapa | Interpretação |
|---|---|---|
| [01_distribuicao](figuras/01_distribuicao.png) | Desenvolvimento | Todos os 2.153.941 participantes do desenvolvimento; 13.236 notas zero preservadas. Ausência de nota não foi convertida em zero. Intervalos de 25 pontos. |
| [02_sete_algoritmos](figuras/02_sete_algoritmos.png) | Desenvolvimento | Mesmas três dobras e 40 entradas. Barras de erro: DP populacional entre dobras; não intervalos de confiança. |
| [03_trio_selecionado](figuras/03_trio_selecionado.png) | Desenvolvimento | Seleção do Checkpoint 2 entre os sete. Eixos ampliados, sem barras partindo de zero; a seleção não usa o teste. |
| [04_catalogo_variantes](figuras/04_catalogo_variantes.png) | Desenvolvimento | Inclui baseline e resultados sem melhoria. As variantes são comparações do modelo indicado, não novas buscas sobre o teste. Tempos completos estão na tabela. |
| [05_pca](figuras/05_pca.png) | Desenvolvimento | PCA centrado, ajustado apenas no treino de cada dobra. Ridge e árvore retiveram 45 componentes para alcançar pelo menos 80% da variância; as seis curvas quase coincidem. |
| [06_buscas](figuras/06_buscas.png) | Desenvolvimento | Cinco modelos, 12 configurações por modelo. Inclui o trio solicitado e os três melhores do catálogo ampliado. |
| [07_ganhos_buscas](figuras/07_ganhos_buscas.png) | Desenvolvimento | Ganhos muito pequenos; a mudança do Stacking não demonstrou relevância prática ou estatística. |
| [08_curvas_finais](figuras/08_curvas_finais.png) | Desenvolvimento | Treino e validação em cinco tamanhos, nas três dobras; receitas fixadas antes do teste. |
| [09_teste](figuras/09_teste.png) | Teste | Trio, baseline e linear nos mesmos 538.486 participantes. A linear tem RMSE menor que SVM e Random Forest. |
| [10_cv_teste](figuras/10_cv_teste.png) | Teste | CV em três dobras e teste em modelos reajustados no desenvolvimento completo; populações de treino distintas. |
| [11_observado_previsto](figuras/11_observado_previsto.png) | Teste | Todos os participantes; mesma escala de células e linha da previsão perfeita para o trio. |
| [12_distribuicao_residuos](figuras/12_distribuicao_residuos.png) | Teste | Intervalos comuns e todos os resíduos; a média global não descreve os erros extremos. |
| [13_faixas](figuras/13_faixas.png) | Teste | Faixas fixadas no desenvolvimento e tamanhos dos grupos. Erros maiores nas notas extremas. |
| [14_escola](figuras/14_escola.png) | Teste | Códigos de TP_ESCOLA e contagens; associação observacional, sem inferência causal. |
| [15_uf](figuras/15_uf.png) | Teste | UF da prova não é necessariamente residência; contagens por UF na tabela. |
| [16_renda](figuras/16_renda.png) | Teste | Categorias de Q006; contagens na tabela. Diferenças não determinam a capacidade individual. |
| [17_residuos_previsto](figuras/17_residuos_previsto.png) | Teste | Todos os 538.486 participantes agregados em células, sem amostra ou corte de extremos. Resíduo negativo: superestimação. A dispersão remanescente limita a precisão individual. |

As figuras 01, 04+06, 05, 08, 11+17 e 13+14 cobrem os seis grupos de evidências visuais do enunciado. A comparação dos sete está em 02; a seleção do trio em 03; o teste em 09–17. Tabelas de CV e teste permanecem separadas. A diagramação no artigo e os PDFs pertencem aos Checkpoints 6 e 7.

O CSV bruto `MICRODADOS_ENEM_2023.csv` e o pacote original `microdados_enem_2023.zip` estão ausentes nesta cópia. Os experimentos usam a base limpa recuperada e verificada. Este pacote de gráficos não contém os microdados individuais.
