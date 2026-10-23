# Andamento - Ciências da Natureza no ENEM 2023

Data: **21/10/2026**. Alvo: **NU_NOTA_CN**, definido diretamente pelo usuário.
A fase atual utiliza dados oficiais; os exemplos fictícios da fase 1 continuam separados.

## Fonte nacional e validação

Pacote obtido pelo link da edição de 2023 no portal do Inep. ZIP de 549.511.687 bytes,
verificado por CRC antes da extração. SHA-256 do ZIP:
`19512b7e29c9c8e940554396969722081341caa275c245a6c9d2d559c5d13a0a`.
Não havia digest do publicador para comparação externa; os hashes registram a identidade
do conteúdo obtido por HTTPS com verificação TLS.

O CSV nacional tem 1.777.162.429 bytes e SHA-256
`c8b1fae0a97b6ac826d950d16696efa3d89c133b0165128aadd2997c2315b666`.
O dicionário oficial foi conferido nas 76 colunas e preservado em XLSX e extrato JSON.
Código e decisões interpretam Q004 pelas alternativas A-F, apesar do tipo numérico
declarado nessa linha da documentação. O prefixo do CSV não é UTF-8 válido; a leitura
latin-1 e o separador ponto e vírgula foram conferidos com a fonte e o Leia-me.

| Controle | Resultado executado |
|---|---:|
| Registros nacionais processados | 3.933.955 |
| Colunas | 76 |
| Registros removidos na preparação | 0 |
| Identificadores ausentes ou repetidos | 0 |
| Duplicatas de conteúdo | 0 |
| Conversões inválidas nas colunas numéricas declaradas | 0 |
| Partes Parquet (lotes de até 50 mil) | 79 |
| Tamanho total das partes Parquet | 329.779.629 bytes |
| Tempo da preparação integral | 530,46 s (aproximadamente 8 min 50 s) |

O processo de importação tinha pico de memória registrado pelo Windows de 466.124.800
bytes em uma medição durante a execução. Esse é um valor observado do processo, não uma
garantia de consumo para todas as futuras execuções. O processamento não concatenou
todos os lotes nem substituiu a fonte por amostra.

## Elegibilidade e partições

| Conjunto/condição | Participantes |
|---|---:|
| Com NU_NOTA_CN observada, elegíveis ao supervisionado | 2.692.427 |
| Sem NU_NOTA_CN, mantidos no diagnóstico | 1.241.528 |
| Notas zero observadas na população elegível, preservadas | 16.547 |
| Desenvolvimento (80%) | 2.153.941 |
| Teste reservado (20%) | 538.486 |
| Validação da dobra 0 | 717.981 |
| Validação da dobra 1 | 717.980 |
| Validação da dobra 2 | 717.980 |

Partições com random_state=42 e três dobras KFold embaralhadas, também com 42. Os IDs
são únicos; a dobra do teste é nula. Hash das partições:
`3f18a7f6fce636b419b00333e4706a0e683e71317a49320629bd3edcb1306040`.
Não se exigiram notas das outras áreas. Não foram imputadas notas nem excluídos
treineiros, idades ou zeros. O teste ainda não foi avaliado.

## Exploração do desenvolvimento

Média de **495,77**, mediana de **493,9** e desvio padrão de **87,92** pontos. Há
**13.236 notas zero** no desenvolvimento. As três variáveis de contexto escolar
TP_DEPENDENCIA_ADM_ESC, TP_LOCALIZACAO_ESC e TP_SIT_FUNC_ESC têm **73,09%** de ausência;
TP_ENSINO tem **61,66%**. As outras 36 candidatas não têm células vazias, embora
algumas tenham alternativas de não informação, mantidas como categorias.

As médias por TP_ESCOLA são 473,60 (pública, n=666.620), 548,42 (privada, n=177.424)
e 499,93 (não respondeu, n=1.309.897). Essas são associações descritivas do
desenvolvimento, sem ajuste de confundidores e sem interpretação causal.

Relatórios e figuras em `resultados/ciencias_natureza/eda-v1/`:
distribuição da nota, ausências e nota por tipo de escola. As três figuras foram
inspecionadas visualmente; a figura de ausências foi ajustada para mostrar apenas
as quatro colunas afetadas, indicando que as outras 36 não têm células vazias.

## Comparação inicial

Representação: 40 candidatas, Q005 numérica e 39 categóricas. Cada Pipeline ajusta
mediana, escala e one-hot no treino de cada dobra. O baseline usa a média do treino,
sem usar as features. O campo features_json do registro lista a representação comum
da comparação; o DummyRegressor ignora essas entradas, conforme a implementação.

<!-- RESULTADOS_INICIAIS -->
Rodada concluída: **12 avaliações**, quatro modelos nas mesmas três dobras. Todos os
2.153.941 participantes de desenvolvimento foram usados nas validações correspondentes,
sem amostra e sem avaliar o teste. Nenhum aviso de convergência foi registrado.

| Modelo | RMSE (média ± DP) | MAE (média ± DP) | R² (média ± DP) | Tempo das três dobras (s) |
|---|---:|---:|---:|---:|
| Ridge (alpha=1) | 76,48 ± 0,05 | 55,62 ± 0,04 | 0,243251 ± 0,000488 | 89,33 |
| Linear sem regularização | 76,48 ± 0,05 | 55,62 ± 0,04 | 0,243247 ± 0,000491 | 118,26 |
| Árvore (profundidade 12) | 77,17 ± 0,04 | 56,29 ± 0,02 | 0,229672 ± 0,000539 | 556,22 |
| Baseline pela média | 87,92 ± 0,08 | 66,24 ± 0,04 | -0,000002 ± 0,000001 | 0,09 |

Desvio padrão com ddof=0. Os tempos incluem ajuste, previsão e métricas; não incluem
a carga inicial dos dados nem a preparação nacional. O R² do baseline é ligeiramente
negativo, próximo de zero, conforme a média do treino avaliada na validação.

Linear e Ridge ficaram muito próximos: a diferença entre seus RMSEs médios é menor
que 0,001 ponto e muito inferior ao desvio entre dobras. Ambos reduziram o RMSE em
aproximadamente 13,01% frente ao baseline. A árvore nesta configuração teve erro
maior e custo mais alto. Esses resultados iniciais não escolhem ainda a solução final.

Artefatos: `cv-inicial-v1/experimentos.csv`, `resumo_cv.csv`, `manifesto.json`,
`parametros_estruturados.json` e `comparacao_cv.png`, em `resultados/ciencias_natureza/`.
A figura comparativa também foi inspecionada visualmente.
<!-- FIM_RESULTADOS_INICIAIS -->

O catálogo também contém SVM linear, KNN, bagging, pasting, floresta, boosting e stacking.
Ele é código disponível, não comprovação de treinamento dessas famílias. A configuração
inicial da árvore tem max_depth=12 e min_samples_leaf=100; Ridge tem alpha=1.0.
Não houve busca de hiperparâmetros nesta rodada.

## Verificação técnica e materiais

- `scripts/verificar.ps1`: **71 testes aprovados** após o frontend (65 anteriores
  e seis novos), lint e formatação aprovados; dependências consistentes.
- Testes com dados fictícios validam importação, partições, categorias, exclusão do
  teste da EDA/CV, ajuste de transformações no treino e registro das três dobras.
- A execução nacional também foi conferida por contagens, hashes e auditoria das
  partições; os casos fictícios não substituem essa evidência real.
- Rascunho do artigo: `docs/artigo_ciencias_natureza_rascunho.md`, com introdução,
  metodologia executada, resultados preliminares e limitações; não é o PDF final.
- Código e ambiente são locais, com Python 3.13.7, pandas 3.0.6, scikit-learn 1.9.1
  e versões restantes no lock. O repositório ainda não tem commit; os manifestos
  registram Git sem revisão e alterações locais. Não houve publicação nem CI remoto.

Uma primeira transferência foi invalidada por sobreposição com retomada. O arquivo
inválido foi isolado e a obtenção refeita com uma única execução, trava e conferência
CRC. O CSV usado nesta análise vem do segundo ZIP validado, com hashes acima.

## Frontend do estudo

Dashboard local em Streamlit e Plotly, com visão geral, filtros combinados de UF da
prova/escola/sexo/treineiro, exploração por perfil, exportação de agregados, comparação
dos quatro modelos e página de qualidade, dicionário e metodologia.
O snapshot `resultados/ciencias_natureza/dashboard-v1/` foi gerado a partir de todo o
desenvolvimento: 54.516 grupos, conciliando contagens, média e notas zero com a EDA.
Não expõe linhas individuais e não avalia o teste. A interface mantém explícitas
as pendências científicas. Execução: `python -m streamlit run app/app.py` no ambiente.
Guia em `docs/frontend.md` e evidências em `docs/validacao-frontend.md`.

Continuação em **23/10/2026**: análise sistemática de todas as 40 entradas e de seus
780 pares, com 254 perfis e 29.709 células agregadas, usando o desenvolvimento
completo. Página de relações e relatório PDF em LaTeX com dez páginas acrescentados.
Os resultados principais são acompanhados da cobertura observada; ausências são
preservadas nos perfis. Ver `docs/relacoes_e_relatorio.md`. Verificação atual:
**80 testes aprovados**, lint/formatação e dependências aprovados. O teste permanece
reservado e as próximas etapas de modelagem abaixo continuam pendentes.

O banco SQLite foi incorporado ao mesmo projeto em
`dados/database/enem2023-v1/enem2023.sqlite3`: 3.933.955 registros, 76 colunas,
aproximadamente 2,24 GB, com integridade e chaves estrangeiras verificadas.
As partições, o dicionário e os resultados agregados estão no banco. O frontend
consulta seus agregados em modo leitura; cinco páginas e quatro opções da página
de relações foram verificadas com a base nacional. O PDF documenta essa integração.

## Próximas etapas para completar o trabalho

1. Executar as demais famílias exigidas, preservando todos os elegíveis e as mesmas dobras.
2. Criar pelo menos três features justificadas e avaliar seleção frente à representação inicial.
3. Testar PCA em pelo menos dois regressores, com variância explicada e componentes justificados.
4. Testar balanceamento para regressão somente no treino, comparando o mesmo regressor.
5. Buscar ≥10 configurações válidas em cada um dos três melhores regressores distintos da comparação completa.
6. Investigar as duas hipóteses adicionais registradas no plano de pesquisa.
7. Fixar a solução e executar a curva de aprendizado nos cinco tamanhos prescritos.
8. Avaliar baseline, linear sem regularização e solução final no teste, uma vez fixadas as decisões.
9. Analisar resíduos e erros por faixa/grupo com n; finalizar artigo ABNT (até dez páginas),
   acompanhamento e pitch, com autores e prazos informados pela equipe.

Não há conclusão final sobre precisão individual, causalidade, sub/sobreajuste ou
generalização fora da edição de 2023 nesta rodada inicial.
