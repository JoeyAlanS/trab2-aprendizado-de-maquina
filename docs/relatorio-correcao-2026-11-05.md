# Relatório técnico de correção e validação — 05/11/2026

> Registro histórico preservado. Para o estado atual da comparação nacional, consulte [Checkpoint 1 — resultados de 06/11/2026](checkpoint-1-resultados.md).

Revisão iniciada em 05/11/2026 e consolidada em 06/11/2026 (America/Fortaleza).
Os nomes dos arquivos de evidência mantêm a data de início da intervenção.

O projeto voltou a usar uma base nacional íntegra e resultados calculados de verdade.
Foram corrigidos os geradores que produziam números sem treinamento e implementadas
etapas científicas ausentes. **O trabalho acadêmico ainda não está pronto para entrega:**
faltam sete famílias da comparação inicial, buscas, solução final, curva, teste e PDFs finais.

A análise usou o enunciado Markdown fornecido como referência dos requisitos e o pedido
colado como autorização para corrigir código. Não foram criados dados fictícios, novos
arquivos de testes automatizados, credenciais ou autores. A suíte sintética histórica não
foi executada nesta intervenção. Não houve commit, push, publicação externa ou alteração
do banco original em Downloads.

## A. Diagnóstico inicial

| Gravidade | Problema confirmado | Arquivos / impacto |
|---|---|---|
| Crítica | Métricas finais fixadas manualmente e 50 mil previsões sintéticas | Os antigos scripts `preencher_resultados_experimentos.py` e `gerar_figuras_artigo.py`, CSVs da raiz e seis figuras não demonstravam execução científica |
| Crítica | Narrativa de conclusão sem evidência | `docs/artigo.md`, `docs/pitch.md`, `docs/acompanhamento.md`, TEX final e pacote Overleaf declaravam buscas, PCA, curva e teste não comprovados |
| Alta | Base completa ausente dos caminhos do projeto | A existência de manifestos não permitia executar treinamento; havia apenas download bruto parcial |
| Alta | Etapas obrigatórias sem implementação executável | Não havia fluxo real de engenharia/seleção/PCA/pesos, buscas, congelamento, curva e avaliação final |
| Alta | Catálogo confundido com experimentos concluídos | Só quatro modelos tinham três dobras reais; HistGradientBoosting anunciado no texto não era o boosting implementado |
| Média | Dependência mínima incompatível com parâmetro usado | `LinearRegression(tol=...)` exige scikit-learn ≥1.7; o projeto aceitava ≥1.6 |
| Média | Documentação desatualizada e instrução destrutiva de recuperação | Aviso de proveniência recomendava checkout; páginas misturavam templates, fase antiga e resultados atuais |
| Média | Obtenção da fonte com verificação insuficiente de extração existente | Validação por tamanho não detectava conteúdo alterado do mesmo tamanho; orientação da trava era pouco clara |

A auditoria anterior permanece em [auditoria-2026-11-05.md](auditoria-2026-11-05.md),
com atualização que distingue o estado anterior da recuperação posterior.

## B. Correções realizadas

### Base real e preservação

Foi localizada a cópia `enem2023-004.sqlite3` em Downloads. Seu tamanho é 2.237.792.256 bytes
e o SHA-256 coincide exatamente com o manifesto histórico do projeto:
`b56dbfd746ddb9de089605e39909f1293e94e7dc440a725d17ad7d43350ed1e5`.
A cópia original foi preservada e outra foi colocada no caminho configurado.

O novo `src/enem_base/recovery.py`, exposto por `recover-database`, abre o SQLite somente
para leitura, verifica integridade, exporta todas as linhas em 79 partes Parquet e confronta
cada ID/partição/dobra com o protocolo original. O novo manifesto registra a recuperação.
O hash binário de `particoes.parquet` mudou pela serialização; a composição dos conjuntos
não mudou. Os hashes anterior e atual foram registrados explicitamente.

| Verificação | Resultado observado |
|---|---:|
| Participantes nacionais | 3.933.955 |
| Colunas | 76 |
| IDs distintos | 3.933.955 |
| Registros de outro ano | 0 |
| Alvo CN observado | 2.692.427 |
| Alvo CN ausente | 1.241.528 |
| Notas zero nacionais | 16.547 |
| Desenvolvimento | 2.153.941 |
| Teste reservado | 538.486 |
| Zeros no desenvolvimento | 13.236 |
| Integridade SQLite / chaves estrangeiras | `ok` / nenhuma violação |

**Conclusão sobre a base:** a base limpa está íntegra, completa e consistente com os
manifestos e as partições históricos; reproduziu exatamente as métricas originais.
Isso não é uma nova certificação do CSV bruto: o CSV e o ZIP completo continuam ausentes,
e não foi realizado novo download/ingestão da fonte do Inep nesta intervenção. O hash do
CSV na cadeia de proveniência é o registrado na ingestão histórica, não recalculado de
um CSV inexistente. Ausências reais continuam ausentes, sem criação de notas.

### Código científico e publicação

| Arquivos | Alteração e motivo |
|---|---|
| `src/enem_base/variants.py` | Engenharia de três atributos, seleção F-regression, PCA centrado, Ridge ponderado e duas ablações; tudo aprendido no treino da dobra |
| `src/enem_base/modeling.py` | Comparações de variantes, diagnósticos aprendidos, métricas por faixa/grupo, avisos e hashes dos resultados |
| `src/enem_base/workflow.py` | Busca nos três melhores de todo o catálogo, 12 configurações por modelo; congelamento preservando também os candidatos originais; curva de 15 pontos; teste único após os pré-requisitos |
| `src/enem_base/evidence.py` | Leitura de execuções completas, conferência de hashes, proveniência, três dobras e cobertura integral |
| `src/enem_base/exports.py` e dois scripts de publicação | Removidas métricas literais e geração de notas/previsões aleatórias; exportação de evidências reais, recálculo de métricas finais, gráficos com fonte e pendências explícitas |
| `src/enem_base/study.py` | Categorias pandas na leitura para reduzir memória sem retirar participantes |
| `src/enem_base/provenance.py` | Hashes do código Python e orientação de recuperação que preserva alterações locais |
| `src/enem_base/official.py` | Validação por CRC dos membros extraídos e bloqueio mais claro de downloads concorrentes/saídas existentes |
| `src/enem_base/cli.py` | Novos comandos científicos e recuperação, com erros explícitos |
| `README.md`, `docs/`, READMEs de dados/resultados | Estado real, decisões, requisitos, comandos e limitações atualizados |
| `relatorio/relatorio_final.tex`, pacote Overleaf | Passaram a identificar o relatório preliminar verificável; nenhuma afirmação de artigo final concluído |

Os 28 arquivos substituídos que continham artefatos invalidados foram preservados em
[arquivo histórico](../historico/2026-11-05/artefatos-nao-validados.zip), incluindo os dois
scripts antigos, os CSVs, as figuras e as versões de entrega. O manifesto interno guarda
os hashes individuais; todos foram reconferidos. Dados e resultados históricos válidos
foram mantidos. O `previsoes_teste.csv` sintético saiu da entrega ativa e não recebeu
substituto fictício: só existirá versão científica após a avaliação final real.

### O que o código aborda de fato

O estudo estima **NU_NOTA_CN** pelo perfil tabular. Usa Q005 numérica e 39 categóricas,
com bloqueio de notas, presença, correção, respostas, gabaritos, ID e ano nas entradas.
UF significa local da prova. Não há integração externa nem inferência causal.

As novas variáveis investigam disponibilidade de computadores por morador, acesso digital
e escolaridade máxima dos responsáveis. “Quatro ou mais computadores” usa quatro como
limite inferior; escolaridade exige duas respostas conhecidas. Denominadores inválidos
permanecem ausentes. O registro de desconhecimento original não é tratado como um nível
intermediário de escolaridade.

A seleção mantém 75% das colunas codificadas pela estatística F; PCA substitui a matriz
codificada por componentes que conservem ≥80% da variância do treino. Q005 é padronizada;
one-hot mantém sua variância natural. Essa escolha de escala é parte do experimento,
não uma afirmação de que seja a única forma válida de aplicar PCA.

A ponderação usa dez faixas de largura igual definidas pelo alvo do treino; não altera
participantes nem distribuição da validação. As ablações investigam a contribuição do
bloco Q001–Q025 e da UF da prova, mantendo o mesmo Ridge. O stacking original preserva
pipelines dentro das dobras internas; combinações ainda sem esse protocolo são recusadas.

## C. Dependências e configurações

O ambiente existente foi aproveitado, sem instalação global e sem novos pacotes.
O requisito mínimo de scikit-learn passou de 1.6 para 1.7 em `pyproject.toml` e `uv.lock`.
`uv lock --offline` inicialmente não conseguiu resolver um item de cache para outra
plataforma; `uv lock` com rede concluiu. O diff do lock altera a restrição declarada,
sem troca de versões dos pacotes. A verificação final `uv lock --check --offline` passou.

Versões usadas: Python 3.13.17, pandas 3.1.0, pyarrow 24.0.0, scikit-learn 1.9.1,
scipy 1.18.1 e matplotlib 3.11.2. As demais estão no registro de ambiente abaixo.
`requirements.lock.txt` foi preservado como ambiente histórico; não foi reescrito nem
apresentado como idêntico ao lock uv atual.

Não são necessárias credenciais ou variáveis obrigatórias no fluxo local.
`ENEM_DATABASE`, `ENEM_DASHBOARD_DIR` e `ENEM_RELATIONS_DIR` são caminhos opcionais do painel.
A configuração do alvo e das partições permanece em `configs/ciencias_natureza.toml`.
A paralelização interna usa duas threads; operações pareadas usam o limite de memória
configurado de 64 MiB. Isso controla blocos de trabalho, não o consumo total do processo.

## D. Validação realmente executada

### Execuções científicas nacionais

Foram executadas **33 avaliações por dobra**, abrangendo quatro modelos originais e sete
combinações de modelo/variante. Cada combinação usa os 2.153.941 participantes em validação
fora da dobra, uma vez por participante ao combinar as três dobras. Não são 11 famílias
iniciais distintas. As 12 avaliações dos quatro modelos originais reproduziram **exatamente**
RMSE, MAE e R² do histórico. Todos os sete manifestos terminaram em `completed`, sem avisos.

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

Fonte: `resultados/experimentos.csv`, com hashes em `resultados/manifesto_publicacao.json`.
DP usa `ddof=0`; tempos somam ajuste e previsão nas três dobras, conforme o registro.
Não incluem toda a preparação de disco e não constituem benchmark entre máquinas.

A engenharia melhorou o RMSE do Ridge em aproximadamente 0,026 ponto, diferença pequena
frente ao desvio entre dobras; isso não sustenta superioridade prática conclusiva.
Seleção e PCA pioraram o erro nesta configuração. O PCA aprendeu **45 componentes nas
seis avaliações**, com as razões de variância persistidas por dobra; os números antigos
38/65 não eram evidência válida para este experimento.

Remover o bloco socioeconômico aumentou o RMSE do Ridge de 76,484 para 80,351; remover UF,
para 76,661. Essas comparações indicam contribuição preditiva no modelo/protocolo usados,
sem demonstrar causalidade nem permitir ordenar isoladamente variáveis correlacionadas.

A ponderação piorou fortemente o resultado global, mas reduziu o erro nas duas faixas
extremas. A tabela abaixo reúne as três validações fora da dobra, ponderando pelo número
de participantes; não é média simples de RMSE por dobra e não utiliza o teste.

| Faixa CN | n | RMSE Ridge original | RMSE Ridge ponderado |
|---|---:|---:|---:|
| [0,400) | 229.381 | 154,641 | 136,357 |
| [400,500) | 907.786 | 48,768 | 115,238 |
| [500,600) | 801.370 | 55,265 | 134,148 |
| [600,700) | 190.421 | 97,577 | 118,901 |
| [700,+inf) | 24.983 | 166,800 | 115,096 |

A estratégia foi mantida como resultado negativo válido; não se recomenda escolhê-la
pelo RMSE global observado. O detalhamento está em
`resultados/ciencias_natureza/evidencias/comparacao_faixas_2026-11-05.csv`.

### Verificações técnicas

| Verificação executada | Resultado e evidência |
|---|---|
| Hash, integridade, unicidade, ano e contagens do SQLite | Aprovados; `evidencias/revalidacao_integral_2026-11-05.json` |
| Recuperação integral e igualdade dos IDs/dobras | Aprovadas; manifestos locais do dataset/partições e `partition_membership_verified=true` |
| Pipeline das seis variantes em registros reais | Ajuste em 10.000 e previsão em 2.000 registros reais do desenvolvimento, sem teste; `validacao_variantes_reais_2026-11-05.json`; depois executadas nacionalmente |
| Cobertura das dobras e contagens por grupos | Todos os manifestos/ativos verificados; totais por grupo conciliados com as validações; `revalidacao_integral_2026-11-05.json` |
| Catálogo e grades | Clones e nomes de parâmetros válidos; 12 configurações por regressor; `catalogo_2026-11-05.json`. Não comprova treinamento dessas buscas |
| Bloqueios do protocolo | Busca incompleta, saída existente, recuperação existente e solução não congelada recusadas com código 2; sem criar teste/trava final; `bloqueios_reais_2026-11-05.json` |
| Streamlit com SQLite nacional | AppTest percorreu visão geral, filtro CE, limpeza, exploração, modelos, método e quatro vistas de relações; sem exceções; banco inalterado; `frontend_real_2026-11-05.json` |
| Downloads do painel | Botões presentes; arquivos baixados pela UI não foram abertos manualmente nesta rodada. Não declarar esse fluxo completo aprovado |
| Exportação real | 44 linhas: 33 dobras e 11 resumos, sem previsões finais; `publicacao-corrigida-v3/manifesto.json` |
| Figuras | Três gráficos gerados de dados reais; inspeção visual identificou e corrigiu sobreposição do rodapé; versão vigente `figuras-corrigidas-v4` |
| Preservação dos artefatos invalidados | 28 hashes e CRC do ZIP conferidos; cópia original mantida |
| PDFs e demais pacotes | Dois PDFs preliminares A4 com dez páginas; CRC dos três ZIPs ativos válido, sem as seis figuras invalidadas; `entregaveis_2026-11-05.json` |
| Ruff, dependências, lock, compilação Python e diff | Todos código 0; `ambiente_e_estatica_2026-11-05.json` |

Os nomes curtos de evidência acima estão em
[`resultados/ciencias_natureza/evidencias/`](../resultados/ciencias_natureza/evidencias/).
`ruff format --check .` aprovou a formatação; `uv pip check` conferiu 53 pacotes instalados.
Foram executados ainda `ruff check .`, `uv lock --check --offline`, `git diff --check`,
`python -m compileall -q src scripts app` e a ajuda da CLI. São verificações estáticas e
de ambiente, não substitutos da execução dos fluxos científicos pendentes.

Os PDFs históricos `output/pdf/main.pdf` e `output/pdf/relatorio_ciencias_natureza.pdf`
têm dez páginas e conteúdo preliminar. A inspeção da auditoria confirmou esse escopo;
não foi compilado um artigo final novo. O pacote Overleaf foi reconstruído com os arquivos
preliminares válidos, sem recolocar as seis figuras invalidadas.

### Não executado ou ainda não comprovado

- Treinamento nacional das sete famílias restantes, e treinamento das buscas.
- Caminho completo de congelamento, curva e avaliação final. Há implementação e bloqueios
  exercitados, mas os pré-requisitos científicos positivos ainda não existem.
- Novo download completo, extração e ingestão do CSV bruto após a correção do CRC.
- Instalação limpa em outra máquina/Windows e funcionamento de todo o fluxo nessa plataforma.
- Abertura manual de todos os downloads do painel e revisão visual em navegador real.
- Artigo final compilado, normalização ABNT final, slides PDF, ensaio e apresentações.
- Publicação no GitHub, acesso do professor e prazos do AVA.

## E. Guia de validação manual

O guia completo está em [validacao-manual.md](validacao-manual.md). Ele cobre doze áreas:
ambiente, banco, recuperação, fonte/EDA, modelos, variantes, busca, congelamento, curva,
teste final, exportação e painel/entregáveis. **Cada área contém objetivo, pré-requisitos,
procedimento, resultado esperado, critério de aprovação e possíveis erros**, com comandos
compatíveis com o ambiente e sem criação de participantes fictícios.

Para iniciar a conferência local, usar:

```bash
.venv/bin/python -m enem_base --help
uv pip check --python .venv/bin/python
.venv/bin/python -m streamlit run app/app.py --server.address 127.0.0.1
```

A recuperação e os experimentos já concluídos não precisam ser repetidos para consultar
o resultado. Se desejar uma nova execução, escolher diretório novo e preservar o anterior.
Nunca executar o teste como verificação rápida de interface nem apagar sua trava para
comparar soluções. Seus pré-requisitos são parte do protocolo científico.

## F. Pendências e ordem de conclusão

1. **Completar a comparação inicial** com SVM, KNN, bagging, pasting, Random Forest,
   GradientBoosting e stacking, em todas as linhas de desenvolvimento e nas mesmas dobras.
   São modelos disponíveis, ainda sem evidência nacional concluída. KNN e ensembles podem
   exigir execução prolongada; não substituir a população por uma amostra para declarar cumprimento.
2. **Executar as buscas** nos três melhores distintos do catálogo completo, registrar
   convergência, tempos e resultados antes/depois. O comando bloqueia a seleção prematura.
3. **Congelar a solução, produzir a curva e avaliar o teste uma vez**. Sem as etapas anteriores,
   não há seleção final válida; por isso não foram produzidos números finais nesta correção.
4. **Gerar as figuras finais e atualizar o consolidado**. Existem distribuição, PCA e
   comparação parcial; faltam o antes/depois das buscas, curva, resíduos e erros do teste.
   Os CSVs de busca e curva são saídas próprias; o consolidado atual agrega CV e, futuramente,
   teste final. Não confundir a existência de um consolidado com conclusão de todas as etapas.
5. **Concluir o artigo ABNT de até dez páginas**, inserir autores reais, citações no ponto
   de uso, resultados finais e limitações. O rascunho foi corrigido, mas não é entrega final.
6. **Produzir os PDFs do acompanhamento e do pitch**, distribuir falas e ensaiar 10–15 minutos.
   O conteúdo preliminar já sustenta o acompanhamento; a realização/entrega não foi comprovada.
7. **Conferir autoria, prazos e publicação**. Essas informações não estavam disponíveis
   para preenchimento seguro. Acessibilidade do repositório ao professor precisa ser verificada.
8. **Completar a reprodução a partir da fonte bruta**, quando necessária: concluir a obtenção
   oficial e validar instalação limpa, sem apagar a base recuperada nem o download parcial original.

A matriz completa de entregáveis está em [requisitos.md](requisitos.md). Não foi atribuída
uma porcentagem de conclusão ou uma nota presumida: critérios acadêmicos incluem análise,
artigo e participação, que não são demonstrados apenas pela presença de código.
