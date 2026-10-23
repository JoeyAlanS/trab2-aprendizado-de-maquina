# Rastreabilidade dos requisitos

Fonte: `referencias/enunciado-projeto2.pdf`, fornecido pelo usuário. As páginas abaixo
são as páginas numeradas do documento (16 páginas). O pedido atual limita a execução
à preparação geral; as entregas finais do enunciado não são consideradas concluídas.

**Continuação em 21/10/2026:** o tema foi definido como Ciências da Natureza (NU_NOTA_CN).
A tabela abaixo preserva o registro da fase 1. A execução atual da fonte nacional,
partições, EDA e comparação inicial é documentada em `andamento_ciencias_natureza.md`.
Os resultados iniciais não comprovam, por si só, todas as exigências finais de modelagem.

| Exigência do documento | Referência | Atendimento na fase 1 | Próxima evidência |
|---|---|---|---|
| Regressão de uma das cinco notas do ENEM 2023 | p. 3 | `features.ENEM_TARGETS`; alvo não selecionado | Registro de atribuição da equipe |
| Fonte nacional completa: 3.933.955 linhas, 76 colunas | pp. 4-5 | Contrato `configs/enem2023.toml`, leitura de todos os lotes | Processamento e diagnóstico da fonte oficial |
| Diagnosticar todos; supervisionado só com alvo observado | p. 4 | Importação sem filtro; `splits.make_split_table` exige alvo | Contagens reais e manifesto das partições |
| Não imputar alvo, não converter ausência em zero, não exigir outras notas | p. 4 | Limpeza sem imputação; testes de zero e elegibilidade | Auditoria do conjunto elegível real |
| Manter treineiros, faixas etárias e zeros | p. 4 | Nenhum filtro por perfil, idade ou nota | Diagnóstico de cobertura e perdas |
| Proibir notas, competências, respostas, gabaritos e resultados em X | p. 5 | Barreiras em `features.validate_features` e revisão semântica documentada | Lista justificada de features e de derivados |
| Presença e situação da redação só para diagnóstico | p. 5 | Bloqueio na fábrica de pré-processamento | Revisão do X final |
| Identificador só para controle; ano constante | p. 5 | Identificador textual; ambos bloqueados nas features | Verificação das matrizes usadas pelos modelos |
| Integração externa: 2023, território correto, uma linha por participante | p. 5 | `integration.merge_context`, cardinalidade e cobertura | Fonte e significado da chave, se houver integração |
| Analisar tipos, ausências, categorias e duplicatas | pp. 5, 8 | Diagnóstico técnico incremental; categorias preservadas sem recodificação semântica | EDA do desenvolvimento pelo dicionário |
| 80/20, random_state=42, IDs persistidos | p. 6 | Funções de partição e persistência testadas com dados fictícios | IDs e hashes reais em `dados/splits/` |
| KFold(3, shuffle=True, random_state=42), mesmas dobras; sem outra validação fixa | p. 6 | `validation_fold` por participante do desenvolvimento | Uso dos índices em todas as comparações |
| Todo ajuste de transformação no treino da dobra | p. 7 | Fábrica não ajustada; teste de imputação e categoria inédita | Pipeline completo passado à CV e busca |
| Baseline pela média | pp. 5, 9 | Planejado; não treinado | DummyRegressor(mean) por dobra |
| Linear sem e com regularização, SVM, árvore, KNN, bagging, pasting, floresta, boosting, stacking | p. 9 | Plano metodológico, sem modelos instanciados | Comparação na base elegível completa |
| Pelo menos três features criadas e método de seleção | pp. 6, 8 | Campos de decisão e roteiro, sem features escolhidas | Hipóteses, fórmulas e comparação |
| PCA em pelo menos dois regressores | pp. 6, 9-10 | Interface futura descrita; escolha de componentes pendente | Variância explicada e comparação com/sem PCA |
| Balanceamento adequado à regressão só no treino | pp. 6, 10 | Plano e limites documentados | Mesmo regressor com e sem estratégia |
| Busca nos três melhores regressores distintos, ≥10 configurações válidas/modelo, três dobras | pp. 6, 10 | Registro de experimentos preparado | Espaços de busca e comparação antes/depois |
| RMSE principal; MAE, R², tempos, média e desvio por dobra | pp. 6-7 | Esquema `resultados/experimentos.csv` vazio | Métricas reais na escala original |
| Fixar solução pelo desenvolvimento e avaliar teste somente ao final | pp. 6-7 | Procedimento documentado, sem comando de treino/teste | Baseline, linear sem regularização e solução final nos mesmos participantes |
| Resíduos = observado − previsto; erros por faixa e por grupo com n | pp. 10, 14 | Esquema de previsões e plano de figuras | Análises reais de desenvolvimento e teste separadas |
| Curva do modelo final: 10%,25%,50%,75%,100% do treino de cada dobra | p. 10 | Roteiro; sem curva fictícia de desempenho | RMSE treino/validação, média e desvio nas três dobras |
| Duas hipóteses adicionais para aprofundamento integral | p. 11 | Possibilidades em `decisoes.md`; não escolhidas | Duas comparações justificadas e interpretadas |
| Repositório com README, dependências, código, partições e experimentos | pp. 8, 12 | Estrutura local, lock, testes e CI preparados | Publicação e acesso pelo professor, quando solicitados |
| Acompanhamento: slides PDF, todos participam, baseline + ≥1 regressor em CV, sem teste | p. 12 | Roteiro em `templates/acompanhamento.md` | Apresentação com resultados reais |
| Artigo ABNT em PDF, até 10 páginas, incluindo referências | pp. 12, 14-15 | Roteiro em `templates/artigo.md` | Documento e revisão conforme guia da biblioteca |
| Figuras e tabela obrigatórias do artigo | p. 14 | Checklist no roteiro do artigo | Gráficos com fonte, eixos, n e interpretação |
| Pitch presencial 10-15 minutos, participação de todos, slides PDF | pp. 12, 15 | Roteiro em `templates/pitch.md` | `docs/pitch.pdf` e apresentação |
| Prazos no AVA | pp. 12, 15 | Pendência explícita; nenhuma data inventada | Equipe consultar e registrar prazos |

## Fronteiras de interpretação

O tamanho e a quantidade de colunas são requisitos do enunciado, ainda não medições
locais da base oficial. A estrutura em `dados/` é uma adaptação permitida pela p. 8.
Os arquivos de resultados contêm só cabeçalhos e não comprovam atendimento de modelagem.
O gráfico fictício valida a rotina de geração de figuras e não serve como resultado do ENEM.
Zero desempenho, ausência de ganho ou R² negativo devem ser discutidos; o documento não
exige ranking nem R² mínimo. Redes neurais ficam fora do escopo da disciplina (p. 9).
