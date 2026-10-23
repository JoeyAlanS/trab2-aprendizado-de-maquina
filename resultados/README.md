# Resultados futuros e evidências técnicas

**Estudo atual:** `ciencias_natureza/` contém os resultados reais de 21/10/2026:
`eda-v1/` (desenvolvimento), `cv-inicial-v1/` (quatro modelos, três dobras) e
`evidencias/` (diagnóstico nacional e auditoria de partições). Consulte o relatório
`docs/andamento_ciencias_natureza.md`. Nenhum resultado de teste foi produzido.

Os arquivos na raiz descritos abaixo são os esquemas históricos da fase 1.

`experimentos.csv` e `previsoes_teste.csv` têm **somente cabeçalho**. Não há métricas,
previsões ou experimentos científicos nesses dois templates. Os esquemas podem ser ampliados
quando o alvo e as hipóteses forem definidos, mantendo os campos do enunciado.

Cada linha de experimento futuro identifica hipótese, features, preparação, modelo,
parâmetros, conjunto, dobra, métricas, tempos, fonte, partições, código e conclusão.
Resultados por dobra usam `row_type=fold`; resumos CV usam `cv_summary`, com média e
desvio explícitos; avaliação final usa `test`. Não misturar teste à média CV.
Campos JSON devem ser CSV corretamente escapado, escritos pelo módulo `csv`/pandas.

`previsoes_teste.csv` guardará ID de controle, nota observada e previsões de baseline,
linear sem regularização e solução final nos mesmos registros. O nome genérico
`registro_id` no cabeçalho deverá ser mapeado explicitamente para NU_INSCRICAO.
Resultados só devem ser inseridos depois da execução real, com alvo registrado.

Figuras fictícias locais em `figuras/` validam renderização, sem responder à pesquisa.
O relatório técnico verificável fica em `docs/validacao-fase1.md`.
