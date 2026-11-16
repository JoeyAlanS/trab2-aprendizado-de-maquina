# Aprendizado de Máquina com Dados do ENEM 2023

Estudo nacional de **regressão** para estimar a nota de Ciências da Natureza
(`NU_NOTA_CN`) a partir do perfil socioeconômico, escolar e demográfico.

**Autores:** Joey Alan de Freitas Solis e Paulo Henrico.
**Instituição:** Universidade de Fortaleza (Unifor). **Professor:** Tulio.

## Organização e entregas

```text
.
├── README.md
├── requirements.txt / requirements.lock.txt / uv.lock
├── configs/                  # contratos da fonte e do estudo
├── dados/
│   ├── raw/                  # originais imutáveis e instruções de obtenção
│   ├── processed/            # importação nacional em Parquet
│   └── splits/               # IDs de desenvolvimento/teste e três dobras
├── notebooks/                # análise dos resultados reais, sem treinamento implícito
├── src/enem_base/             # preparação, modelos, treinamento e avaliação
├── app/                      # dashboard e dependências para o Streamlit
├── scripts/                  # execução, conferência e publicação
├── tests/                    # verificações de software e fixtures isoladas
├── resultados/
│   ├── experimentos.csv       # registro completo, separando desenvolvimento e teste
│   ├── previsoes_teste.csv    # arquivo individual local; regenerável
│   ├── comparacao_modelos.csv # ranking inicial completo
│   ├── colunas.csv            # campos criados, utilizados e excluídos de X
│   ├── figuras/               # PNG e SVG finais
│   ├── ciencias_natureza/     # execuções científicas preservadas
│   └── evidencias/            # documentos imutáveis exigidos pela proveniência
├── docs/
│   ├── acompanhamento.pdf
│   ├── artigo.pdf
│   ├── pitch.pdf
│   └── referencias/           # enunciado e dicionário
├── relatorio/                 # fontes LaTeX, figuras e instruções de compilação
├── apresentacao/              # galeria comentada para apresentação
├── output/                    # apresentação e pacote editável para Overleaf
└── .gitignore
```

| Entrega | Acesso |
|---|---|
| Dashboard no Streamlit | [Abrir aplicativo](https://enem2023-ciencias-natureza.streamlit.app/) · estado da implantação abaixo |
| Acompanhamento | [PDF](docs/acompanhamento.pdf) |
| Artigo científico (10 páginas) | [PDF](docs/artigo.pdf) |
| Pitch em LaTeX (23 slides; meta de 13 minutos) | [PDF](docs/pitch.pdf) · [Fonte](relatorio/slides_pitch.tex) |
| Apresentação final no Canva (23 slides) | [Editar no Canva](https://www.canva.com/design/DAHbBYEq0BQ/NpBSvagoxA2EQUM0qQ8hSg/edit) |
| Resultados dos 11 modelos/configurações iniciais | [Tabela](resultados/comparacao_modelos.csv) · [Gráfico](resultados/figuras/18_comparacao_completa.png) |
| Registro de experimentos | [CSV](resultados/experimentos.csv) · [Formato e evidências](resultados/README.md) |
| Seleção e criação de colunas | [CSV](resultados/colunas.csv) |
| Galeria com explicações | [Abrir](apresentacao/index.html) |
| Fontes para Overleaf | [Guia](relatorio/README.md) · [ZIP](output/overleaf-enem2023.zip) |

A dashboard apresenta o catálogo completo de validação e os cinco resultados do
teste final na página **Modelos**. Ela lê as tabelas publicadas e confere seus hashes,
sem treinar novamente. Exploração e filtros usam exclusivamente o desenvolvimento;
o snapshot exploratório histórico e seus manifestos permanecem preservados.

O PDF do pitch em LaTeX acompanha a sequência temática dos 23 slides do Canva e
possui design próprio. A exposição
deve durar **10 a 15 minutos**, conforme o enunciado; a meta de ensaio é 13 minutos,
com 6min30 por autor.

### Publicação no Streamlit Community Cloud

Endereço criado: [enem2023-ciencias-natureza.streamlit.app](https://enem2023-ciencias-natureza.streamlit.app/).
O compartilhamento está público. Na verificação de 16/11/2026, a instalação das
dependências e a inicialização do servidor terminaram, mas o endereço permaneceu
na tela de carregamento mesmo após uma reinicialização. **A navegação pública
ainda precisa ser confirmada.** As cinco páginas passaram na conferência local
de um clone sem microdados ou SQLite; isso não substitui a verificação na nuvem.

A configuração está preparada para execução sem os arquivos individuais locais.
Após entrar em [share.streamlit.io](https://share.streamlit.io/), criar o aplicativo
com os seguintes campos:

| Campo | Valor |
|---|---|
| Repositório | `JoeyAlanS/trab2-aprendizado-de-maquina` |
| Branch | `master` |
| Arquivo principal | `app/app.py` |
| Python, em configurações avançadas | `3.13` |

As dependências da interface estão em `app/requirements.txt`; os agregados e
resultados necessários já estão no Git. O aplicativo usa os snapshots quando o
banco SQLite local está ausente. Não enviar microdados, modelos ajustados,
previsões individuais ou credenciais. O dashboard não executa treinamentos.

Se o login apresentar erro, tentar a opção de entrada por e-mail descrita na
[documentação oficial](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-account/sign-in-sign-out).
O erro de autenticação ocorre antes do processo de implantação do código.

### Correspondência com o documento de entrega

| Exigência | Evidência no repositório |
|---|---|
| Originais, preparação e partições separados | `dados/raw/`, `dados/processed/`, `dados/splits/`; instruções e comandos de reprodução |
| Diagnóstico e regras de preparação | `src/enem_base/`, `resultados/colunas.csv`, figuras e artigo |
| Dez regressores e média nas mesmas três dobras | `resultados/comparacao_modelos.csv` e linhas de comparação em `experimentos.csv` |
| Engenharia, seleção, PCA em dois modelos, ponderação e duas ablações | Linhas de variantes em `experimentos.csv`; código em `variants.py` |
| Busca nos três melhores e curvas do modelo final | Buscas em cinco modelos, incluindo o trio global; curvas e tabelas em `resultados/` |
| Avaliação final, previsões e erros por grupos | Cinco receitas no teste; `previsoes_teste.csv` local; tabelas e figuras agregadas no Git |
| Acompanhamento, artigo de até dez páginas e pitch | Os três PDFs em `docs/`; fontes em `relatorio/` |
| Material editável para apresentação | Slides no Canva e fontes LaTeX no ZIP do Overleaf |

Essa correspondência documenta os arquivos e experimentos. Comparecimento,
participação na apresentação e submissão no AVA dependem da equipe.

Os dados e modelos grandes permanecem locais. Um clone contém código, configurações,
tabelas agregadas, documentos e figuras. Os nomes históricos das execuções científicas
foram preservados: mudar esses caminhos invalidaria referências dos manifestos.
Não é necessário navegar nessas pastas para apresentar o trabalho.

## Fonte, participantes e alvo

Fonte: [microdados oficiais do ENEM 2023, Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
O treinamento nacional usa **somente registros reais**. Dados fictícios em
`tests/fixtures/` servem exclusivamente aos testes de software.

| Etapa | Participantes |
|---|---:|
| Base original, 76 colunas | 3.933.955 |
| Sem nota de Ciências da Natureza, excluídos da supervisão | 1.241.528 |
| Alvo observado, incluindo 16.547 notas zero | 2.692.427 |
| Desenvolvimento (80%) | 2.153.941 |
| Teste reservado (20%) | 538.486 |

Nota ausente não é imputada nem convertida em zero. O complemento de competências
de redação foi preservado em `dados/raw/`, mas não é unido à base de modelagem.
Notas de outras provas, respostas, presença e gabaritos não são preditores.
`NU_INSCRICAO` controla participantes e partições; não é entrada do modelo.

## Features e preparação

As 40 entradas originais estão fixadas em [ciencias_natureza.toml](configs/ciencias_natureza.toml):

- **Numérica:** `Q005` (quantidade de moradores).
- **Demográficas e escolares:** `TP_FAIXA_ETARIA`, `TP_SEXO`, `TP_ESTADO_CIVIL`,
  `TP_COR_RACA`, `TP_NACIONALIDADE`, `TP_ST_CONCLUSAO`, `TP_ANO_CONCLUIU`,
  `TP_ESCOLA`, `TP_ENSINO`, `IN_TREINEIRO`, `TP_DEPENDENCIA_ADM_ESC`,
  `TP_LOCALIZACAO_ESC`, `TP_SIT_FUNC_ESC`, `SG_UF_PROVA`, `TP_LINGUA`.
- **Questionário:** `Q001` a `Q025`, exceto `Q005`, já numérica. Inclui escolaridade
  e ocupação dos responsáveis, renda, bens e acesso digital, conforme o dicionário.

Códigos categóricos são representados por one-hot, sem presumir distâncias entre
categorias. A ausência vira `__MISSING__`; códigos de desconhecimento existentes no
dicionário continuam distintos. Q005 recebe mediana, indicador quando necessário
e padronização. Essas estatísticas são aprendidas **somente no treino de cada dobra**.
A codificação original teve 235 dimensões nos ajustes registrados; Q005 continua
numérica, portanto a representação não é inteiramente binária.

A ingestão remove espaços externos, normaliza tokens de ausência e valida tipos,
ano, colunas, IDs e contagens. Os originais nunca são editados. O registro
[colunas.csv](resultados/colunas.csv) distingue campos fora de X de campos apagados:
as 76 colunas permanecem na importação.

Também foram avaliadas, separadamente da receita original:

- Três features: computadores por morador; acesso digital (computador + internet);
  máximo da escolaridade dos responsáveis. Fórmulas e limites em `variants.py`.
- Seleção de 75% das colunas codificadas por `f_regression`, dentro do treino.
- PCA: limiar de 80% da variância, 45 de 235 componentes em cada ajuste registrado
  de Ridge e árvore. Não foi aplicado à receita vencedora.
- Pesos inversos à frequência de dez faixas do alvo, calculados no treino; houve piora.
- Ablações de informações socioeconômicas e de UF; ambas aumentaram o erro do Ridge.

## Modelos obrigatórios e resultados efetivamente executados

O enunciado exige regressão linear **sem e com regularização**, árvore e as outras
sete famílias. Todos estão implementados e possuem três dobras completas:

| Modelo | Configuração inicial principal | RMSE médio ± DP |
|---|---|---:|
| Stacking | Linear + árvore; combinador Ridge; três dobras internas | 76,175 ± 0,049 |
| Ridge | alpha=1; solver lsqr | 76,484 ± 0,054 |
| Regressão linear | sem regularização; tol=1e-6 | 76,484 ± 0,054 |
| SVM linear | LinearSVR, C=1; epsilon=0 | 76,577 ± 0,059 |
| Random Forest | 30 árvores; profundidade 12; folha mínima 100 | 76,643 ± 0,046 |
| Árvore de decisão | profundidade 12; folha mínima 100 | 77,167 ± 0,042 |
| Bagging | 20 árvores; 70% do treino, com reposição | 77,484 ± 0,029 |
| Gradient Boosting | 60 etapas; profundidade 2; taxa 0,1 | 77,589 ± 0,068 |
| Pasting | 20 árvores; 70% do treino, sem reposição | 77,609 ± 0,043 |
| KNN | 25 vizinhos; ponderação por distância | 77,896 ± 0,042 |
| Média (baseline) | DummyRegressor(strategy='mean') | 87,921 ± 0,078 |

O KNN usa busca euclidiana **exata**, com implementação específica em `neighbors.py`
e backend Faiss para viabilizar a população nacional. Não usa vizinhos aproximados
nem amostra substituta. No Stacking, inclusive o pré-processamento das bases é
reajustado nas dobras internas; Ridge aprende com previsões fora da dobra.

O trio inicial **do catálogo completo** é Stacking, Ridge e linear, antes do
arredondamento. O trio Stacking/SVM/Random Forest pertence ao recorte de sete
algoritmos solicitado ao longo do desenvolvimento. Foram realizadas buscas na
união dos dois grupos: **cinco modelos × 12 configurações × três dobras = 180 avaliações**.
Não se deve apresentar linear, Ridge ou árvore como famílias que deixaram de ser testadas.

## Protocolo, curvas e teste final

Separação aleatória 80/20 com semente 42; KFold de três dobras embaralhadas com a
mesma semente no desenvolvimento. Na rodada 0, treinar em 1+2 e validar em 0;
na rodada 1, treinar em 0+2 e validar em 1; na rodada 2, treinar em 0+1 e validar em 2.
Todos usam os mesmos IDs e métricas: **RMSE principal; MAE e R² complementares**.
Os resumos de CV mostram média e DP populacional (ddof=0); o teste é resultado separado.

As curvas usam 10%, 25%, 50%, 75% e 100% do treino de cada dobra, validação fixa e
subconjuntos progressivos com semente 42. Há 45 pontos iniciais e 45 finais para
Stacking, SVM e Random Forest. Os pontos finais registram reuso compatível de ajustes
ou bases; isso não representa 45 treinamentos inteiramente novos. A curva obrigatória
do modelo final está presente. Curvas adicionais não comprovam generalização para outro ano.

A solução foi congelada no desenvolvimento. O teste contém a solução final, a média
e a regressão linear sem regularização exigidas pelo enunciado, mais SVM e Random Forest:

| Modelo no teste (mesmos 538.486 participantes) | RMSE | MAE | R² |
|---|---:|---:|---:|
| Stacking | 76,190 | 55,325 | 0,2497 |
| Regressão linear de referência | 76,517 | 55,616 | 0,2433 |
| SVM linear | 76,622 | 55,538 | 0,2412 |
| Random Forest | 76,658 | 55,821 | 0,2405 |
| Média | 87,959 | 66,285 | -0,000002 |

Stacking reduziu o RMSE em 13,38% em relação à média. As diferenças pequenas entre
regressores não foram submetidas a teste de significância. Ridge, árvore, KNN,
Bagging, Pasting e Boosting têm CV completa, mas não previsões no teste reservado.
Não é obrigatório aplicar todo o catálogo ao teste. O ranking do teste é descritivo;
não foi usado para voltar à seleção. Os erros maiores nos extremos, as diferenças
entre grupos e a ausência de avaliação temporal limitam as conclusões.

## Ambiente e ordem de execução

Ambiente dos experimentos: Python 3.13, pandas 3.1.0, scikit-learn 1.9.1,
PyArrow 24.0.0, matplotlib 3.11.2 e Faiss 1.15.1. As versões completas estão no lock.
Executar os comandos na **raiz do repositório**; não há dependência de caminhos pessoais.

```bash
uv sync --locked --extra dev
# Alternativa: Python 3.13 + venv, pip install -r requirements.txt e pip install -e . --no-deps
.venv/bin/python -m enem_base --help
```

**1. Obter, preparar e dividir os dados, em uma instalação nova:**

```bash
.venv/bin/python -m enem_base fetch-enem --raw dados/raw
.venv/bin/python -m enem_base prepare --config configs/enem2023.toml
.venv/bin/python -m enem_base split --study configs/ciencias_natureza.toml
```

Ver instruções e hashes em [raw](dados/raw/README.md),
[processed](dados/processed/README.md) e [splits](dados/splits/README.md).
Não executar novamente em destinos preenchidos. A modelagem completa nacional,
especialmente KNN e Stacking, exige tempo e memória substanciais.

**2. Nova comparação dos 11 regressores/configurações e referências:**

```bash
.venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --models baseline linear ridge arvore svm knn bagging pasting random_forest boosting stacking --output resultados/execucoes/original
```

**3. Representações e hipóteses, nas mesmas partições:**

```bash
for variante in engineered selected weighted without_socio without_uf; do
  .venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --variant "$variante" --models ridge --output "resultados/execucoes/$variante"
done
.venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --variant pca --models ridge arvore --output resultados/execucoes/pca
```

**4. Busca nos três melhores do catálogo completo, congelamento e curva:**

```bash
.venv/bin/python -m enem_base search --study configs/ciencias_natureza.toml --cv resultados/execucoes/original --output resultados/execucoes/busca
.venv/bin/python -m enem_base freeze-solution --study configs/ciencias_natureza.toml --cv resultados/execucoes/original --search resultados/execucoes/busca --variants resultados/execucoes/engineered resultados/execucoes/selected resultados/execucoes/pca resultados/execucoes/weighted resultados/execucoes/without_socio resultados/execucoes/without_uf --output resultados/execucoes/solucao
.venv/bin/python -m enem_base learning-curve --study configs/ciencias_natureza.toml --solution resultados/execucoes/solucao --output resultados/execucoes/curva
```

Esse fluxo é uma **nova execução** do protocolo completo: busca o trio global e produz
a curva do vencedor. A execução histórica também pesquisou SVM e Random Forest e
produziu curvas adicionais. Seus comandos especializados estão em `scripts/` e suas
configurações, parâmetros, origens e hashes permanecem nos registros científicos.

**5. Teste final da nova execução, somente depois de congelar a solução:**

```bash
.venv/bin/python -m enem_base evaluate-final --study configs/ciencias_natureza.toml --solution resultados/execucoes/solucao --curve resultados/execucoes/curva --output resultados/execucoes/teste
```

Esse comando avalia média, linear e solução final e salva as previsões individuais.
Na cópia local atual o teste já está encerrado: a trava impede repetir a avaliação.
Não removê-la para escolher outro modelo. Para conferir os resultados existentes,
usar a auditoria abaixo, que recompõe métricas das previsões já salvas.

**6. Conferência e organização da entrega existente:**

```bash
# Conferência portátil, inclusive em um clone sem os arquivos individuais:
.venv/bin/python scripts/verificar_publicacao.py
# Auditoria integral dos experimentos, quando os caches locais estiverem disponíveis:
.venv/bin/python scripts/auditar_entrega.py --output resultados/nova-verificacao
.venv/bin/python scripts/organizar_entrega.py --verification resultados/nova-verificacao
.venv/bin/python notebooks/01_analise_resultados.py
.venv/bin/python -m pytest -q
.venv/bin/ruff check src scripts tests notebooks
```

A auditoria completa exige os caches, modelos e previsões locais, que não vão ao Git.
Não altera os resultados originais, não treina e não gera novas previsões.
O organizador produz `resultados/experimentos.csv`, `previsoes_teste.csv`, `colunas.csv`
e figuras, com hashes. O CSV de previsões fica local por seu tamanho; inclui
`registro_id`, `nota_observada` e `previsao_*` dos cinco modelos efetivamente avaliados.
A validação da publicação atual está em `resultados/verificacao-2026-11-15/`.

**7. Apresentar e compilar documentos:**

```bash
.venv/bin/python -m http.server 8765
# Abrir http://127.0.0.1:8765/apresentacao/index.html
# Dashboard, em outro terminal:
.venv/bin/python -m streamlit run app/app.py
```

Para LaTeX/Overleaf, seguir [relatorio/README.md](relatorio/README.md). Os PDFs e
fontes não precisam dos microdados para compilar. Os testes de software são separados
dos experimentos nacionais: um não demonstra a execução do outro.
