# Resultados da entrega

- `experimentos.csv`: registro consolidado de 437 linhas, com comparação de todos
  os modelos obrigatórios, variantes, buscas, curvas e teste final.
- `previsoes_teste.csv`: 538.486 participantes reais, ID de controle, nota observada,
  cinco previsões e campos dos grupos; arquivo local grande, ignorado pelo Git.
- `colunas.csv`: seleção de campos originais, três atributos criados e seleção por dobra.
- `figuras/`: figuras finais em PNG e SVG; `apresentacao/index.html` oferece a galeria.
- `manifesto_entrega.json`: fontes e hashes dos arquivos publicados.

Em `experimentos.csv`, `stage` distingue comparação, variantes, busca, curva inicial,
curva final e teste. `row_type=fold` é uma avaliação por dobra; `summary` é sua média
com DP populacional (`std_ddof=0`); `test_final` é avaliação única do teste reservado.
Filtrar ambos os campos para não contar resumos ou cálculos reutilizados como novos
ajustes. `evaluated_set=development_cv` e `test` nunca devem ser misturados em uma média.
Os nomes `rmse`, `mae`, `r2` guardam a métrica por dobra ou sua média conforme o tipo;
`*_std` existe nos resumos. `fraction` identifica o tamanho das curvas.

`hypothesis`, `features_json`, `preparation_json`, `parameters_json`, tempos,
`conclusion`, `source_path` e hashes documentam cada experimento. Campos com sufixo
`_json` são valores estruturados dentro do CSV. `diagnostics_json` preserva a seleção
codificada e os diagnósticos existentes. A preparação descrita é a dos regressores;
o baseline não utiliza X. Tempos têm escopos distintos, identificados em `time_scope`:
cache, reuso e cargas concorrentes impedem interpretar isso como benchmark de hardware.
As buscas fornecem tempo de ajuste por dobra e tempos médios do GridSearch; não foi
inventado tempo de predição por dobra onde não há esse registro.

As execuções científicas preservadas ficam em `ciencias_natureza/`. Seus nomes internos
históricos são mantidos porque manifestos, hashes e caches dependem desses caminhos.
Não são material obrigatório de leitura na apresentação. `evidencias/protocolos.zip`
guarda dois relatórios imutáveis exigidos pelos verificadores, sem espalhar antigos MDs.
`verificacao-2026-11-15/` contém a conferência independente atual. Nenhum treinamento
ou acesso para gerar novas previsões ocorreu nessa publicação.

Para conferir uma cópia local que contém os caches, modelos e previsões originais:

```bash
.venv/bin/python scripts/auditar_entrega.py --output resultados/nova-verificacao
.venv/bin/python scripts/organizar_entrega.py --verification resultados/nova-verificacao
```

O primeiro comando exige saída inexistente. O segundo atualiza apenas a entrega derivada;
preserva os experimentos originais. Confere IDs do teste e recompõe as cinco métricas.
Um clone não contém os grandes caches individuais: para uma nova execução usar a ordem
completa do README principal, em destinos novos. A ausência desses arquivos em um clone
não significa ausência dos experimentos registrados.
