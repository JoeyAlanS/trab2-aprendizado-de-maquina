# Auditoria do Projeto 2 — ENEM 2023 / Ciências da Natureza

> Registro histórico preservado. Para o estado atual da comparação nacional, consulte [Checkpoint 1 — resultados de 06/11/2026](checkpoint-1-resultados.md).

## Atualização posterior à auditoria

Este documento preserva o diagnóstico anterior às correções. Depois dele, a cópia SQLite
original foi localizada fora do repositório, verificada pelo hash histórico e recuperada.
As métricas dos quatro modelos originais foram reproduzidas exatamente; seis variantes
foram implementadas e executadas na população nacional de desenvolvimento. Os artefatos
invalidados foram arquivados com hashes e retirados das entregas ativas.
O estado atual, as evidências e o que ainda falta estão no
[relatório de correção](relatorio-correcao-2026-11-05.md). Não interpretar as ausências
descritas na auditoria abaixo como uma nova constatação após a recuperação.

Data da revisão: 05/11/2026 (America/Fortaleza).
Revisão local: `e9f04552830fb12863b69ef7be5de0515619507a`.
Referência de requisitos: `docs/referencias/enunciado-projeto2.pdf`, 16 páginas.
Escopo: código, configurações, dados presentes, evidências, resultados, documentos, PDFs, pacotes ZIP e execução dos testes.

O projeto tem uma infraestrutura de preparação e exploração aproveitável e registros consistentes de uma comparação inicial de quatro modelos. **Não está pronto para entrega final.** A principal pendência é científica: parte dos arquivos apresentados como resultados finais é produzida por valores fixos e simulações aleatórias, sem treinamento dos modelos correspondentes.

A revisão não alterou código, dados ou entregáveis existentes. Este documento registra os achados. Arquivos não rastreados já existentes foram preservados.

## 1. Achados prioritários

| Prioridade | Achado | Evidência | Consequência |
|---|---|---|---|
| Crítica | Previsões de teste são sintéticas, inclusive a nota observada e os identificadores | `scripts/preencher_resultados_experimentos.py:622-650` | `resultados/previsoes_teste.csv` não comprova avaliação no ENEM |
| Crítica | Métricas adicionais, buscas, PCA, balanceamento, aprofundamentos e curva são números fixos | `scripts/preencher_resultados_experimentos.py:160-610` | O registro consolidado não comprova execução dos experimentos |
| Crítica | Figuras finais usam distribuições simuladas, funções arbitrárias ou listas fixas | `scripts/gerar_figuras_artigo.py:63-89,132-166,237-249,309-318,385-399,450-492` | Os gráficos não podem ser apresentados como medições empíricas |
| Alta | Artigo, pitch e TEX final apresentam esses resultados como concluídos | `docs/artigo.md:13,73-113,125-203`; `docs/pitch.md:69-89`; `relatorio/relatorio_final.tex:189-345` | Revisar a narrativa e regenerar os materiais a partir de execuções reais |
| Alta | Base nacional, dataset preparado, IDs das partições e SQLite não estão nesta cópia | Inventário de `dados/` e chamada a `verified_dataset` | Não é possível repetir ou certificar a execução nacional nesta pasta |
| Alta | Slides obrigatórios em PDF não foram encontrados; PDFs existentes são preliminares | Inventário de PDFs e leitura dos dois relatórios em `output/pdf/` | Entregas formais ainda incompletas |
| Média | Textos contêm inferências científicas não sustentadas, links divergentes e dados de autoria provisórios | `docs/artigo.md:3-6,201-203`; `docs/acompanhamento.md:87`; `docs/pitch.md` | Corrigir interpretação e identificação antes da apresentação |

## 2. O que está de fato implementado

O problema tratado é **regressão da nota NU_NOTA_CN usando perfil socioeconômico, escolar e demográfico**. O código não resolve questões de Física, Química ou Biologia, nem analisa o texto das respostas: estima a nota agregada a partir de informações tabulares.

| Parte | Implementação encontrada | Limite da evidência |
|---|---|---|
| Obtenção da fonte | Download oficial com retomada, trava, verificação do ZIP e hashes | Download local atual incompleto |
| Importação | CSV nacional em lotes de 50 mil; latin-1; separador ponto e vírgula; Parquet comprimido | Dataset nacional preparado ausente |
| Qualidade | Contagens, ausências, zeros, duplicatas, identificadores, conversões e ano | Relatório nacional histórico presente; não recalculado da fonte nesta revisão |
| Seleção de população | Elegibilidade só por alvo observado; mantém zeros, treineiros e faixas etárias | Implementação e testes conferidos; IDs nacionais ausentes |
| Protocolo | 80/20 com semente 42; KFold de três dobras embaralhadas com semente 42; persistência de IDs | Código correto para esse protocolo; arquivos efetivos precisam ser recuperados |
| Entradas | 40 atributos: Q005 numérico e 39 categóricos | Sem os três atributos derivados prometidos no texto final |
| Pré-processamento | Mediana, indicador de ausência e escala no bloco numérico; categoria explícita de ausência e one-hot no categórico | Ajustado no treino de cada dobra pelo Pipeline |
| Proteção contra vazamento | Bloqueia notas, competências, respostas, gabaritos, presença, status da redação, IDs, ano e códigos de prova | Não substitui revisão semântica de futuros atributos |
| Comparação | Treino e predição por dobra; RMSE, MAE, R², tempos, avisos, médias e desvios | Registros estruturados disponíveis apenas para quatro modelos iniciais |
| Exploração | Distribuição, ausências, médias por escola, perfis, associações com o alvo e entre entradas | Análise descritiva, sem interpretação causal |
| Dashboard | Cinco páginas Streamlit/Plotly, filtros e exportações de agregados | Funciona pelos snapshots; SQLite nacional ausente |
| Relatório preliminar | Geração de figuras e tabelas com snapshots verificados | Não equivale ao artigo final exigido |
| Integração externa | Função genérica de junção com controle de ano, cardinalidade e cobertura | Nenhuma fonte externa efetivamente integrada; integração é opcional no enunciado |

Referências centrais: `src/enem_base/ingestion.py`, `splits.py`, `study.py`, `preprocessing.py`, `features.py`, `modeling.py`, `relations.py`, `dashboard.py`, `database.py` e `reporting.py`.

A configuração utiliza **SG_UF_PROVA**, que descreve a UF de realização da prova. Não há município na lista efetiva de features, embora o TEX final mencione “município/UF”. UF de prova não deve ser tratada como residência.

### Modelos: existência de código versus execução

| Modelo | Implementação disponível | Registro por dobra na execução nacional entregue |
|---|---|---|
| Média — DummyRegressor | Sim | Sim: 3 dobras |
| Regressão linear sem regularização | Sim | Sim: 3 dobras |
| Ridge | Sim | Sim: 3 dobras |
| Árvore de decisão | Sim | Sim: 3 dobras |
| SVM — LinearSVR | Sim | Não |
| KNN | Sim | Não |
| Bagging | Sim | Não |
| Pasting | Sim | Não |
| Random Forest | Sim | Não |
| Boosting | Sim, **GradientBoostingRegressor** | Não |
| Stacking | Sim, com pipelines nas dobras internas | Não |

**HistGradientBoostingRegressor**, apresentado como vencedor no artigo, não é implementado no catálogo atual. O boosting disponível é outro estimador. Não foram encontrados pipelines ou rotinas executáveis para PCA, seleção, três features novas, ponderação de treino, GridSearchCV/RandomizedSearchCV, curva de aprendizado, ablação, modelo de dez atributos ou avaliação final do teste. As ocorrências desses nomes nos scripts de resultados são descrições e números, não chamadas de treinamento.

## 3. A base está correta?

**A escolha da fonte e do alvo está adequada. A integridade da base nacional local não pôde ser confirmada porque seus arquivos não estão presentes.**

O portal oficial do Inep lista a edição de 2023 e o endereço registrado no projeto corresponde ao pacote dessa edição:
[Microdados do ENEM — Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).

O enunciado exige 3.933.955 participantes e 76 colunas. O contrato de importação exige exatamente esses números, ano 2023 e diagnóstico sem filtros. Os relatórios históricos informam:

| População | Quantidade registrada |
|---|---:|
| Fonte nacional | 3.933.955 |
| Alvo CN observado | 2.692.427 |
| Alvo CN ausente | 1.241.528 |
| Desenvolvimento | 2.153.941 |
| Teste | 538.486 |
| Zeros entre todos os elegíveis | 16.547 |
| Zeros no desenvolvimento | 13.236 |

As contagens são aritmeticamente compatíveis com o protocolo e o enunciado. Isso não substitui a conferência do CSV original.

### Inventário local

| Arquivo/conjunto esperado | Situação em 05/11/2026 |
|---|---|
| ZIP nacional completo | Ausente |
| `dados/raw/microdados_enem_2023.zip.part` | Presente: 34.844.672 bytes; não é um ZIP completo válido |
| `dados/raw/MICRODADOS_ENEM_2023.csv` | Ausente |
| `dados/processed/enem2023-v1/` | Ausente |
| `dados/splits/ciencias-natureza-v1/particoes.parquet` | Ausente |
| `dados/database/enem2023-v1/enem2023.sqlite3` | Ausente; há somente esquema e manifesto |
| Dicionário XLSX e extrato JSON | Presentes |
| Snapshots agregados e evidências históricas | Presentes |

O manifesto do banco declara aproximadamente 2,24 GB e status concluído, mas **um manifesto não substitui o arquivo SQLite**. A função de acesso à fonte nacional falha com `FileNotFoundError` para o manifesto do dataset preparado.

Arquivos grandes podem ficar fora do Git conforme o enunciado. O problema é a ausência nesta cópia e a documentação afirmar disponibilidade local, sem conseguir reproduzir a execução atual. Não é necessário versionar vários gigabytes; é necessário garantir obtenção, integridade, persistência e reprodução.

Não foi baixada novamente a base inteira nesta auditoria. Uma consulta HTTP HEAD ao servidor de download falhou por conexão reiniciada; a página oficial foi consultada. Não há certificado externo de hash do publicador nos metadados do projeto.

### O que foi possível verificar diretamente

- Os seis ativos do dashboard e os quatro ativos da análise de relações correspondem aos SHA-256 dos respectivos manifestos.
- O dashboard contém 54.516 grupos agregados que somam **2.153.941 participantes** e **13.236 zeros**.
- A média recalculada pelos agregados é **495,774199** e o desvio padrão é **87,921084**, coerentes com a EDA.
- Os 40 perfis de variáveis, ao agrupar suas categorias, totalizam cada um 2.153.941 participantes e 13.236 zeros.
- Cada um dos 780 pares, ao somar as células de cruzamento, totaliza 2.153.941 participantes.
- Os resultados de relações contêm 40 relações com o alvo, 780 pares, 254 categorias/perfis e 29.709 células de cruzamento.
- O XLSX tem SHA-256 igual ao registrado no manifesto histórico da fonte.
- O extrato JSON lista 76 variáveis; as definições utilizadas pelo dashboard coincidem com esse extrato.
- O hash do JSON atual difere do registrado nas execuções históricas **apenas pela convenção de fim de linha**: converter virtualmente LF para CRLF reproduz exatamente o hash histórico. Não foi encontrada mudança semântica nas variáveis comparadas. A rastreabilidade deve ser harmonizada sem falsificar o histórico.

Assim, os agregados são internamente consistentes. **Não permitem auditar individualmente os participantes, a ausência de sobreposição treino/teste ou a correspondência integral com o CSV original** sem recuperar os arquivos de origem e de partições.

## 4. Resultados disponíveis e resultados inválidos para entrega

### Comparação inicial

`resultados/ciencias_natureza/cv-inicial-v1/experimentos.csv` contém 12 linhas: quatro modelos nas três dobras. Recalculei as médias e os desvios; todos correspondem ao resumo existente. Cada modelo soma 2.153.941 participantes avaliados nas três validações.

| Modelo | RMSE médio | Desvio entre dobras |
|---|---:|---:|
| Ridge | 76,483610 | 0,054371 |
| Linear sem regularização | 76,483799 | 0,054269 |
| Árvore | 77,166774 | 0,042393 |
| Baseline | 87,921068 | 0,077557 |

Esses registros são coerentes com a implementação. Não foram reproduzidos pelo treinamento nacional durante esta revisão, dada a ausência da base. A diferença entre linear e Ridge é desprezível frente à variação das dobras; não sustenta alegar superioridade relevante nem diagnosticar multicolinearidade como “moderada e bem comportada”.

### CSV consolidado

`resultados/experimentos.csv` possui 30 registros: 22 resumos, cinco pontos de curva e três linhas de teste. **Nenhuma linha tem a dobra preenchida.** O identificador de revisão é a string `local-reproducible-v1`, não o hash de um commit.

O script lê o CSV inicial em `df_init`, mas não usa essa tabela para construir os registros; escreve manualmente todas as métricas. Os resultados iniciais podem ser recuperados de seus arquivos originais. Os números posteriores não comprovam execução.

Não há histórico de pelo menos dez configurações válidas por regressor, métricas de cada busca ou melhores estimadores ajustados.

### Previsões de teste

Reproduzi **somente em memória**, sem sobrescrever arquivos, a sequência aleatória das linhas 622–650 do script. As notas observadas, previsões lineares e previsões finais reproduzem **exatamente** as 50 mil linhas do CSV entregue.

Os IDs são inteiros sequenciais de 1 a 50.000, não os identificadores nacionais persistidos. O arquivo contém 305 zeros. Essas linhas não constituem a avaliação dos 538.486 participantes reservados.

| Modelo | RMSE publicado como teste | RMSE recalculado do CSV entregue | R² recalculado do CSV |
|---|---:|---:|---:|
| Baseline | 87,9412 | 95,846462 | -0,001051 |
| Linear | 76,5120 | 73,847912 | 0,405735 |
| Final | 75,8410 | 73,363086 | 0,413512 |

Essa tabela **não apresenta desempenho válido no ENEM**. Demonstra que nem as métricas publicadas correspondem ao conteúdo do CSV sintético.

### Figuras finais

| Figura | Origem encontrada | Situação |
|---|---|---|
| Distribuição do alvo | Amostra normal simulada a partir de média/desvio, acrescida de zeros; a barra de zeros é deslocada para x=100 e multiplicada por 8 | Substituir pelo histograma dos dados/agregados reais; já existe versão aproveitável na EDA |
| Comparação e buscas | Listas fixas de RMSE e desvios | Regenerar a partir dos resultados reais por dobra e buscas |
| Variância do PCA | Autovalores artificiais `1/k**0.65` | Nenhum PCA é ajustado |
| Curva de aprendizado | Cinco valores fixos para treino/validação e desvios | Nenhum pipeline é reajustado nos cinco tamanhos |
| Observado versus previsto/resíduos | 25 mil notas simuladas e previsões calculadas diretamente da nota simulada | Não é avaliação de um modelo treinado |
| Erros por faixa/grupo | Contagens e RMSE fixos no código | Não decorrem de agrupamento das previsões reais |

Há inconsistência adicional no PCA: a função sintética atinge 80% em **65 componentes**, mas os textos e experimentos declaram **38**. Na própria função, 38 componentes representam cerca de **63,46%**. O gráfico afirma redução de 65,5% de 110 para 65, quando a redução seria cerca de 40,9%.

Mesmo os números fixos do CSV contradizem a seleção dos “três melhores”: o ranking inicial apresentado seria HistGradientBoosting, Random Forest e **Stacking**, mas a busca declarada inclui **Ridge**.

As alegações de “generalização perfeita”, “inexistência de sobreajuste” e “teto estrutural” do R² não são sustentadas. Mesmo curvas reais próximas não demonstrariam perfeição nem identificariam causalmente a origem do erro residual.

## 5. Conferência de todos os entregáveis

| Entregável | Existe? | Avaliação e pendência |
|---|---|---|
| Código-fonte | Sim | Preparação, exploração e comparação inicial implementadas; faltam rotinas científicas finais |
| README e dependências | Sim | Instruções úteis; corrigir disponibilidade da base, etapas antigas, caminhos e versões |
| Repositório remoto | Sim | `git ls-remote origin HEAD` respondeu com o mesmo commit local; acesso específico do professor não verificado |
| Partições persistidas | Não nesta cópia | Há código e evidências históricas; recuperar/gerar os IDs e conferir hashes |
| Registro de experimentos | Sim, dois conjuntos | Preservar o inicial por dobra; substituir o consolidado com números fixos |
| Previsões do teste | Sim, mas sintéticas | Gerar para todos os participantes reais do teste após fixar a solução |
| Figuras exploratórias preliminares | Sim | Aproveitáveis, com as limitações de proveniência desta revisão |
| Figuras finais obrigatórias | Sim, mas sem evidência empírica adequada | Regenerar as seis a partir dos experimentos e previsões reais |
| Dashboard | Sim | Cinco páginas executaram sem erro com os snapshots locais; é material complementar |
| Banco SQLite | Não nesta cópia | Código, esquema e manifesto presentes; recuperar/gerar se continuar anunciado como parte da entrega |
| Acompanhamento | Roteiro Markdown | Conteúdo preliminar útil; faltam slides PDF, nomes reais e evidência de realização/participação |
| Artigo | Rascunhos Markdown/TEX e relatórios preliminares PDF | Falta artigo final validado com experimentos reais, autores, referências e até dez páginas |
| Pitch | Roteiro Markdown | Faltam slides PDF e substituição dos resultados não executados; apresentação de 10–15 min depende da equipe |
| Pacote Overleaf | Sim, ZIP íntegro | TEX e seis figuras presentes, mas reproduzem os resultados problemáticos; não é PDF final |
| Fontes do relatório preliminar | Sim, ZIP íntegro | Contém TEX, tabelas, figuras e dados agregados; aproveitável como relatório de andamento |
| Exportação de relações | Sim, ZIP íntegro | Contém alvo, pares, perfis, cruzamentos e instruções; material complementar |
| Prazos e participação | Não verificáveis por arquivos locais | Consultar AVA e confirmar apresentação efetiva de todos os integrantes |

Não foram encontrados `docs/acompanhamento.pdf`, `docs/artigo.pdf` ou `docs/pitch.pdf`, nem slides equivalentes em PDF em outra pasta do repositório.

Os PDFs `output/pdf/main.pdf` e `output/pdf/relatorio_ciencias_natureza.pdf` têm **dez páginas cada**, mas se identificam como relatórios de desenvolvimento e dizem que o teste permanece reservado. A versão mais recente adiciona documentação do SQLite na página 9. A inspeção visual do relatório de dez páginas não identificou falhas grosseiras de layout; cumprir o limite de páginas não resolve a ausência dos resultados finais.

Não foi compilado um novo artigo final nesta auditoria; portanto, paginação, legibilidade e adequação normativa do TEX final ainda precisam de validação após a correção científica. O enunciado remete ao guia da biblioteca para o padrão ABNT.

O endereço usado no artigo, acompanhamento e pitch contém `github.com/joey/...`, enquanto o remoto configurado é `github.com/JoeyAlanS/trab2-aprendizado-de-maquina`. Corrigir e conferir o link destinado ao professor.

`output/overleaf_bundle/`, `output/relatorio_overleaf.zip` e `relatorio/relatorio_final.tex` já estavam não rastreados pelo Git antes da auditoria. Não assumir que foram publicados. O TEX da pasta Overleaf é idêntico ao TEX final local. Algumas imagens de curva/resíduos diferem em bytes das cópias de `resultados/figuras/`; padronizar a geração e a versão escolhida.

## 6. Checklist técnico contra o enunciado

| Requisito | Estado verificável |
|---|---|
| Regressão de CN na edição correta | Atendido na configuração e no código |
| Fonte nacional integral | Evidência histórica presente; arquivo ausente, não revalidado |
| Todos os elegíveis, zeros/treineiros preservados | Implementado; conferir execução nacional ao restaurar dados |
| 80/20, semente 42, três dobras fixas | Implementado; recuperar IDs nacionais |
| Transformações só no treino da dobra | Implementado na comparação disponível e no stacking |
| Baseline, linear, Ridge e árvore | Código e registros estruturados das três dobras |
| Demais famílias obrigatórias | Código disponível; execução nacional não comprovada |
| Três novas features | Não implementadas no pipeline |
| Seleção de features | Não implementada |
| PCA em pelo menos dois regressores | Não implementado |
| Balanceamento adequado à regressão | Não implementado |
| Busca nos três melhores, ≥10 configurações por modelo | Não implementada |
| Curva em 10%, 25%, 50%, 75% e 100% | Não implementada |
| Duas hipóteses adicionais | Descritas, sem execução verificável |
| Escolha final pelo desenvolvimento | Não comprovada |
| Avaliação final de baseline, linear e solução nos mesmos participantes | Não implementada; CSV sintético não atende |
| Resíduos e erros por faixa/grupo com n | Existem ilustrações, mas faltam cálculos reais |
| Artigo e slides finais | Incompletos |

O enunciado não exige atingir R² mínimo nem superar determinado modelo. Um resultado real sem ganho pode atender integralmente ao critério quando a execução, a comparação e a interpretação são corretas.

## 7. Verificações executadas

- `.venv/bin/python -m pytest -q`: **81 testes aprovados**, em 10,92 s.
- `.venv/bin/python -m ruff check .`: aprovado.
- `.venv/bin/python -m ruff format --check .`: 74 arquivos já formatados.
- `uv pip check --python .venv/bin/python`: 53 pacotes verificados, compatíveis.
- AppTest com os snapshots locais reais disponíveis: visão geral, exploração, modelos, método e relações sem exceções ou mensagens de erro.
- Conferência dos dez hashes de ativos do dashboard/relações.
- Recálculo das estatísticas aditivas, contagens e resumos da CV inicial.
- Recálculo das métricas do CSV entregue e reprodução exata de sua sequência sintética em memória.
- Leitura do enunciado e dos PDFs, inspeção visual das dez páginas do relatório mais recente, verificação do número de páginas e integridade dos três ZIPs.
- Inventário dos dados e verificação de acesso ao dataset: fonte preparada indisponível.
- Consulta à página oficial do Inep e ao HEAD do repositório remoto.

O ambiente atual tem Python 3.13.17, pandas 3.1.0, scikit-learn 1.9.1, pytest 9.2.0 e ruff 0.17.3. O lock histórico registra versões diferentes de Python/pandas/pytest/ruff. Compatibilidade dos pacotes e testes aprovados não provam reprodução exata do ambiente histórico.

Os testes cobrem comportamento de código e usam dados pequenos em vários cenários. **Eles não validam automaticamente a origem científica das métricas fixas, o conteúdo dos textos ou a execução sobre milhões de participantes.**

## 8. Ordem recomendada de conclusão

1. **Separar explicitamente simulações e resultados empíricos.** Retirar dos materiais de entrega as afirmações de execução que não têm evidência. Preservar os arquivos originais para rastreabilidade.
2. **Recuperar a base nacional e as partições**, conferir pacote, CSV, ano, colunas, registros, tipos, elegibilidade, zeros, IDs, disjunção dos conjuntos e hashes. Investigar a trava de download antes de retomá-lo; não remover uma trava sem conferir se existe processo ativo.
3. **Reproduzir a comparação inicial e completar as sete famílias restantes** nas mesmas três dobras, usando todos os participantes elegíveis do desenvolvimento. Registrar custo e falhas reais.
4. **Implementar engenharia, seleção, PCA e balanceamento** dentro do protocolo. Definir fórmulas e casos especiais pelo dicionário: renda superior aberta, moradores válidos, escolaridade desconhecida como categoria distinta e bens com contagens limitadas.
5. **Executar buscas nos três melhores regressores distintos** da comparação real, com pelo menos dez configurações válidas por modelo; guardar resultados de todas as configurações.
6. **Executar as duas hipóteses adicionais** e a curva obrigatória do modelo escolhido, com treino progressivo e validação fixa em cada dobra.
7. **Congelar a solução e avaliar o teste real**, reajustando baseline, regressão linear e modelo final em todo o desenvolvimento; salvar IDs e previsões de todos os 538.486 participantes, caso essa população seja reconfirmada.
8. **Recalcular métricas e gráficos exclusivamente desses resultados**, incluindo resíduos, faixas e grupos definidos no desenvolvimento.
9. **Reescrever e finalizar os entregáveis**: artigo ABNT de até dez páginas, slides do acompanhamento, slides do pitch, nomes reais, link correto, referências e instruções reproduzíveis.
10. **Conferir publicação e apresentações**: arquivos no GitHub, acesso do professor, prazos do AVA, duração do pitch e participação da equipe.

A próxima etapa não é somente formatar o artigo: é completar a execução científica e substituir os resultados simulados antes de fechar a entrega.
