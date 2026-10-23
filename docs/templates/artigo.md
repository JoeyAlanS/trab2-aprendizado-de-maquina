# Roteiro do artigo - não é artigo concluído

PDF final: `docs/artigo.pdf`, até 10 páginas incluindo figuras, tabelas e referências.
Aplicar o padrão ABNT de artigos/citações/referências com o guia da biblioteca Unifor.
Não inserir resultados fictícios como resultados da pesquisa.

1. Título, equipe, alvo atribuído e link do repositório, na primeira página.
2. Resumo: problema, método, principais resultados reais e conclusão.
3. Introdução/contextualização: relevância, pergunta e objetivo.
4. Metodologia: fonte, contagens e elegibilidade; features, transformações, modelos,
   PCA, balanceamento, buscas, curva, partições, sementes e prevenção de vazamento.
5. Resultados: comparações informativas e teste final separado da validação cruzada.
6. Discussão: ganhos ou ausência deles, resíduos, grupos, ajuste, complexidade e limites.
7. Conclusão: resposta à pergunta amparada nas evidências.
8. Referências: todas as fontes citadas no ponto de uso, incluindo dados, métodos,
   documentação, código adaptado e figuras externas.

## Checklist das evidências obrigatórias (enunciado, p. 14)

- [ ] Distribuição do alvo no desenvolvimento, identificando zeros quando existirem.
- [ ] Comparação inicial com baseline; três regressores antes/depois da busca.
- [ ] Variância explicada acumulada, componentes escolhidos e justificativa do PCA.
- [ ] Curva do modelo final: RMSE treino/validação e variação nas três dobras,
      nos cinco tamanhos de treino prescritos.
- [ ] Observado versus previsto no teste com linha de previsão perfeita.
- [ ] Resíduos no teste com representação que revele padrões.
- [ ] Erros no teste por faixa de nota e pelo menos um grupo de perfil/localização, com n.
- [ ] Tabela RMSE, MAE, R² e tempo; CV com média/desvio separada do teste.
- [ ] No teste, baseline, linear sem regularização e solução final nos mesmos participantes.
- [ ] Fonte, conjunto avaliado, eixos, unidades, legendas e interpretação de cada figura.

Definir faixas/grupos no desenvolvimento. É permitido agrupar gráficos em painéis
legíveis. Distinguir amostra visual documentada de cálculo de métricas sobre todos
os elegíveis. Revisar causalidade indevida e generalização além da edição de 2023.
