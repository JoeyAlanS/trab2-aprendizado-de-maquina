# Estimativa da nota de Ciências da Natureza no ENEM 2023

**Rascunho de andamento, ainda não apto à entrega como artigo final.**
Atualização de 07/11/2026: os sete algoritmos, a seleção do trio e suas curvas foram
concluídos nos [Checkpoints 1–3](checkpoints.md). Os [resultados das curvas](checkpoint-3-resultados.md)
usam as configurações iniciais. Buscas, curvas finais e teste foram concluídos
no [Checkpoint 4](checkpoint-4-resultados.md): Stacking teve RMSE 76,190 nos 538.486
participantes do teste, com erros maiores nos extremos das notas. A incorporação completa ao artigo pertence
ao Checkpoint 6; os resultados históricos abaixo não são a comparação final.
Autores: identificação da equipe pendente.
Repositório: https://github.com/JoeyAlanS/trab2-aprendizado-de-maquina

## Resumo provisório

O estudo investiga a previsão de NU_NOTA_CN a partir do perfil socioeconômico, escolar
e demográfico. A base limpa nacional contém 3.933.955 participantes, dos quais 2.692.427
têm alvo observado. O protocolo reserva 20% para o teste e utiliza três dobras nos 80%
de desenvolvimento, com semente 42. A comparação inicial registrada de média, linear,
Ridge e árvore encontrou RMSE aproximadamente 87,92, 76,48, 76,48 e 77,17 pontos.
A recuperação da base em 05/11/2026 preservou os participantes e as dobras. As variantes nacionais também foram concluídas: engenharia com Ridge teve RMSE 76,458;
PCA e ponderação pioraram o resultado global nas configurações avaliadas.
O teste final está documentado separadamente no Checkpoint 4; estes resultados
históricos não demonstram superioridade universal de ensembles nem teto preditivo.

## Problema e dados

A pergunta é quanto o perfil disponível permite estimar a nota de CN, não a capacidade
individual ou o efeito causal da renda/escola. A fonte é a edição nacional de 2023 do Inep.
Ausência de alvo e nota zero são distintas; zeros, treineiros e faixas etárias são mantidos.
NU_INSCRICAO é apenas controle. Não entram notas de outras áreas, presença, respostas,
gabaritos ou resultados da correção. UF da prova não é necessariamente residência.

## Metodologia implementada

A representação original contém Q005 numérica e 39 categóricas. A mediana, a escala e
as categorias são ajustadas no treino de cada dobra. Os modelos disponíveis e parâmetros
ficam em src/enem_base/modeling.py. Engenharia, seleção, PCA e ponderação são definidos
em src/enem_base/variants.py. O fluxo nacional do Checkpoint 4 usa tuning.py,
final_selection.py, frozen_curves.py e final_evaluation.py; workflow.py contém o fluxo legado.

As novas features são COMPUTADORES_POR_MORADOR, ACESSO_DIGITAL e ESCOLARIDADE_PAIS_MAX.
A categoria de quatro ou mais computadores usa quatro como limite inferior; escolaridade
não conhecida permanece ausente e recebe tratamento no treino, não nível intermediário.
Seleção usa F-regression no treino. PCA é centrado e conserva variância natural dos
indicadores one-hot; a quantidade de componentes é aprendida de novo em cada dobra.
Ponderação aprende dez intervalos de largura igual pelo mínimo/máximo das notas do treino.

## Resultados verificados no desenvolvimento

Até 05/11/2026, foram concluídas 33 avaliações por dobra e 11 resumos de modelo/representação, sobre
2.153.941 participantes. As métricas dos quatro modelos iniciais reproduziram exatamente
o histórico. Os números abaixo vêm dessas rodadas reais e usam DP populacional entre dobras.
O consolidado atualizado tem 54 avaliações e 18 resumos, incluindo o Checkpoint 1.

| Modelo / representação | RMSE médio ± DP | MAE médio | R² médio | Tempo total (s) |
|---|---:|---:|---:|---:|
| arvore / original | 77.1668 ± 0.0424 | 56.2904 | 0.2297 | 397.74 |
| baseline / original | 87.9211 ± 0.0776 | 66.2396 | -0.0000 | 0.06 |
| linear / original | 76.4838 ± 0.0543 | 55.6232 | 0.2432 | 79.64 |
| ridge / original | 76.4836 ± 0.0544 | 55.6230 | 0.2433 | 57.84 |
| ridge / três atributos novos | 76.4580 ± 0.0527 | 55.5947 | 0.2438 | 66.43 |
| ridge / seleção de atributos | 76.5291 ± 0.0535 | 55.6429 | 0.2424 | 60.28 |
| arvore / PCA | 78.3278 ± 0.0371 | 57.3175 | 0.2063 | 269.15 |
| ridge / PCA | 77.7327 ± 0.0690 | 56.7475 | 0.2183 | 52.71 |
| ridge / ponderação | 125.2022 ± 0.1360 | 100.5626 | -1.0279 | 67.80 |
| ridge / sem bloco socioeconômico | 80.3509 ± 0.0491 | 59.0809 | 0.1648 | 20.08 |
| ridge / sem UF da prova | 76.6607 ± 0.0520 | 55.7793 | 0.2397 | 56.19 |

A engenharia melhorou o RMSE do Ridge em apenas 0,026 ponto. Seleção e PCA pioraram-no.
O PCA reteve 45 componentes nas seis avaliações, pelo critério de pelo menos 80% da
variância do treino. Retirar o bloco socioeconômico e a UF aumentou o erro, indicando
contribuição preditiva no modelo e protocolo usados, sem interpretação causal.

A ponderação reduziu o RMSE fora da dobra em [0,400), de 154,641 para 136,357 (n=229.381),
e em [700,+inf), de 166,800 para 115,096 (n=24.983), mas piorou fortemente as faixas
intermediárias e o erro global. Essas métricas por faixa agregam as três validações
pelo número de participantes e não são resultados de teste. A estratégia não deve
ser escolhida pelo RMSE global observado.

Dados detalhados, hashes, contagens, variantes e limitações estão em
`resultados/experimentos.csv` e `docs/relatorio-correcao-2026-11-05.md`.

## Etapas ainda pendentes

A seleção entre os sete foi concluída no [Checkpoint 2](checkpoint-2-resultados.md),
com a diferença para o catálogo ampliado documentada. As curvas das configurações
iniciais foram concluídas no [Checkpoint 3](checkpoint-3-resultados.md). Buscas,
congelamento, curvas finais e teste do trio com baseline e linear foram concluídos
no [Checkpoint 4](checkpoint-4-resultados.md). A organização da coleção
visual foi concluída no [Checkpoint 5](checkpoint-5-resultados.md). Permanecem
a incorporação dos resultados e a redação/formatação final
do artigo (Checkpoint 6), além dos PDFs (Checkpoint 7). As figuras finais do teste
estão em `checkpoint-4-2026-11-07/publicacao-v2/`. Resultados sem ganho devem permanecer.

## Discussão e limites

Diferenças muito pequenas frente à dispersão entre dobras não demonstram superioridade
relevante. R² baixo não prova subajuste; curvas próximas não asseguram generalização perfeita.
Os dados são observacionais e autodeclarados, com ausências escolares expressivas.
A divisão aleatória avalia novos participantes da mesma edição, não outras edições,
escolas inéditas ou efeitos de políticas educacionais.

## Referências e fechamento

- INEP. Microdados do ENEM, edição de 2023. https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem
- SCIKIT-LEARN. Documentação de pipelines, regressores, PCA e validação cruzada. https://scikit-learn.org/stable/user_guide.html
- UNIVERSIDADE DE FORTALEZA. Trabalhos acadêmicos e normalização. https://unifor.br/biblioteca/trabalhos-academicos

Antes da entrega: completar autores, citações no ponto de uso, resultados reais e discussão;
formatar segundo o guia da biblioteca, compilar, conferir legibilidade e limite de dez páginas.
A versão anterior com afirmações sem execução foi preservada em historico/2026-11-05/.
