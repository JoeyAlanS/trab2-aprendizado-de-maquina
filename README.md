# Projeto 2 — Ciências da Natureza no ENEM 2023

Regressão de **NU_NOTA_CN** a partir do perfil socioeconômico, escolar e demográfico.
Fonte nacional: **Inep / ENEM 2023**, 3.933.955 participantes e 76 colunas.
Repositório: https://github.com/JoeyAlanS/trab2-aprendizado-de-maquina

## Estado atual e integridade científica

**Desenvolvimento em checkpoints (atualizado em 07/11/2026):** o Checkpoint 1 está concluído e validado:
sete algoritmos e 21 avaliações nacionais, sem uso do teste nessa etapa. O Checkpoint 2 selecionou
**Stacking, SVM linear e Random Forest** entre esses sete, pelo RMSE médio.
O Checkpoint 3 foi concluído e validado em 07/11/2026: 45 ajustes reais, curvas
e análise dos três modelos; consulte [os resultados](docs/checkpoint-3-resultados.md).
O [Checkpoint 4](docs/checkpoint-4-resultados.md) está concluído: buscas, receitas finais,
curvas e avaliação dos mesmos 538.486 participantes de teste em cinco modelos.
Stacking teve o menor RMSE (76,190), com redução de 13,38% frente ao baseline.
O [Checkpoint 5](docs/checkpoint-5-resultados.md) reúne 17 gráficos PNG/SVG, 14 tabelas
e uma [galeria local](resultados/ciencias_natureza/checkpoint-5-2026-11-07/index.html),
com validação numérica e visual. O [Checkpoint 6](docs/checkpoint-6-resultados.md)
concluiu o [artigo de dez páginas](output/pdf/artigo_ciencias_natureza.pdf), com autores,
resultados reais e referências. O [Checkpoint 7](docs/checkpoint-7-resultados.md) entrega o roteiro do pitch, o
acompanhamento e a versão LaTeX do artigo, com PDFs e [pacote Overleaf](output/overleaf-enem2023.zip).
Slides foram dispensados pelo pedido atual; ensaio e apresentação ainda dependem da equipe.
Consulte [a seleção e sua justificativa](docs/checkpoint-2-resultados.md),
[a comparação inicial](docs/checkpoint-1-resultados.md) e
[o protocolo e o acompanhamento](docs/checkpoints.md). O KNN utiliza busca euclidiana
exata com índice binário do Faiss para reduzir tempo e memória, com verificação contra
o scikit-learn. `uv sync --locked --extra dev` instala a dependência local necessária.

A correção de 05/11/2026 identificou resultados fixos/simulados em arquivos de entrega.
Esses arquivos foram preservados, com hashes, em `historico/2026-11-05/artefatos-nao-validados.zip`.
**Não são resultados científicos e não devem ser utilizados no artigo ou nas apresentações.**
Os geradores ativos agora exigem execuções concluídas e verificadas; não preenchem etapas ausentes.

A base limpa SQLite original foi localizada no ambiente, conferida pelo SHA-256 do manifesto
e recuperada em `dados/database/enem2023-v1/enem2023.sqlite3`. A recuperação exportou todas
as linhas para Parquet e comprovou que os IDs e as dobras coincidem com o protocolo original.
Os ZIPs nacional e de competências foram incorporados em 07/11/2026. O CSV bruto
normalizado foi comparado integralmente com os 79 Parquets, com igualdade em todos
os valores. Consulte a [identificação e validação das fontes](docs/origem-arquivos-enem.md). O banco e os dados grandes
não são versionados no Git. As instruções abaixo permitem obtê-los ou recuperar uma cópia válida.

| Parte | Situação |
|---|---|
| Preparação, partições, EDA e dashboard | Implementados; dados reais recuperados e verificações documentadas |
| Comparação inicial | Quatro referências em `cv-recuperado-v2` e sete algoritmos concluídos em `checkpoint-1-2026-11-06` |
| Seleção de três modelos | Checkpoint 2 concluído; configurações iniciais e ranking registrados, com escopo explícito dos sete algoritmos |
| Engenharia, seleção de atributos, PCA, ponderação e ablações | Executados na base nacional: 21 avaliações adicionais nas três dobras |
| Curvas dos três selecionados | Checkpoint 3 concluído: cinco tamanhos, três dobras, 45 pontos e três figuras PNG/SVG validados |
| Busca, congelamento e teste final | Checkpoint 4 concluído: 60 configurações, 180 avaliações CV, 45 pontos finais e cinco modelos avaliados no teste; [resultados e nove gráficos](docs/checkpoint-4-resultados.md) |
| Visualizações finais | Checkpoint 5 concluído: coleção com 17 figuras, galeria e tabelas verificadas |
| Artigo | Checkpoint 6 concluído: dez páginas, sete figuras, três tabelas, quadro de parâmetros e oito referências |
| Acompanhamento e pitch | Checkpoint 7: documentos de texto em LaTeX e PDF; roteiro oral sem slides, conforme solicitado |

Consulte [o relatório de correção](docs/relatorio-correcao-2026-11-05.md),
[o guia de validação manual](docs/validacao-manual.md) e
[a auditoria anterior](docs/auditoria-2026-11-05.md). A auditoria retrata a pasta antes
que o banco em Downloads fosse localizado; o relatório de correção registra a recuperação.

O consolidado real contém 54 avaliações por dobra e 18 resumos em
`resultados/experimentos.csv`. As figuras do Checkpoint 1 estão em
`resultados/ciencias_natureza/checkpoint-1-2026-11-06/publicacao-v2/`;
distribuição e PCA anteriores permanecem em `figuras-corrigidas-v4/`. A engenharia com Ridge obteve
RMSE 76,458; a ponderação piorou para 125,202. Esses valores são de desenvolvimento. A escolha final e o teste estão
registrados no Checkpoint 4 e integrados ao artigo no Checkpoint 6. Entre os sete modelos do Checkpoint 1, Stacking teve o menor RMSE médio: 76,175. Isso não é resultado de teste.
O Checkpoint 2 não adicionou treinamentos ao consolidado. Linear e Ridge permanecem
como referências fora da seleção dos sete; o relatório explicita que o ranking do
catálogo ampliado difere do trio solicitado. As buscas foram executadas posteriormente no Checkpoint 4. Suas tabelas e os resultados
de teste permanecem separados do consolidado inicial, em
`resultados/ciencias_natureza/checkpoint-4-2026-11-07/`; a publicação final é `publicacao-v2/`.

## Ambiente

Python **3.13**. Executar os comandos na raiz do repositório.
O ambiente local existente pode ser utilizado sem reinstalação:

```bash
.venv/bin/python --version
.venv/bin/python -m enem_base --help
.venv/bin/python -m streamlit run app/app.py --server.address 127.0.0.1
```

Instalação nova com o lock do projeto:

```bash
uv sync --locked --extra dev
```

Alternativa com pip e o lock histórico:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
```

No Windows, substituir `.venv/bin/python` por `.venv\Scripts\python.exe`.
`requirements.lock.txt` preserva o ambiente histórico; `uv.lock` é o lock usado pela
instalação com uv. Não misturar as duas formas para alegar reprodução exata do ambiente.
Não há credenciais nem variáveis de ambiente obrigatórias para o estudo local.

## Dados reais e recuperação

Fonte: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem

Se o CSV original não estiver disponível, mas houver o SQLite original e seu manifesto
válido, colocá-los em `dados/database/enem2023-v1/`. O nome esperado do banco é `enem2023.sqlite3`.
Somente quando os diretórios de dataset e partições **ainda não existirem**:

```bash
.venv/bin/python -m enem_base --verbose recover-database \
  --study configs/ciencias_natureza.toml \
  --database dados/database/enem2023-v1/enem2023.sqlite3
```

Isso recupera a base limpa; não fabrica o CSV bruto nem declara recuperar seu conteúdo byte a byte.
Os hashes novos de Parquet/partições são registrados junto aos hashes históricos, mantendo
os mesmos participantes e as mesmas dobras. O SQLite é aberto somente para leitura.

Para obter a fonte original do Inep em um ambiente sem a preparação:

```bash
.venv/bin/python -m enem_base fetch-enem --raw dados/raw
.venv/bin/python -m enem_base --verbose prepare --config configs/enem2023.toml
.venv/bin/python -m enem_base split --study configs/ciencias_natureza.toml
```

As saídas existentes não são sobrescritas. Uma trava de download abandonada deve ser
investigada antes de nova transferência; o arquivo `.part` não é uma base válida.

## Protocolo e entradas

Dos registros nacionais, 2.692.427 têm CN observada; os demais entram no diagnóstico.
O desenvolvimento tem 2.153.941 participantes e o teste reservado, 538.486.
Zeros, treineiros e faixas etárias são preservados. Não se exigem notas de outras áreas.

A configuração lista Q005 numérica e 39 categóricas. Inclui UF **da prova**, não residência.
Notas, competências, respostas, gabaritos, presença, status da redação, ID, ano e códigos
de prova são bloqueados como entradas. Transformações aprendem somente no treino de cada dobra.

As três novas features implementadas são computadores por morador (contagem superior
limitada), acesso digital e escolaridade máxima dos responsáveis quando ambos são conhecidos.
Desconhecimento não recebe nível escolar intermediário. Definições e limitações estão no guia.

## Execução científica

Escolher um nome de saída novo para cada rodada. Os comandos não usam amostras para a
comparação principal. Modelos como KNN, ensembles e buscas podem exigir execução prolongada.

```bash
.venv/bin/python -m enem_base --verbose compare --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/cv-nova \
  --models baseline linear ridge arvore svm knn bagging pasting random_forest boosting stacking
```

Também é permitido separar os modelos em rodadas, mantendo as mesmas partições. Para as
variantes, usar `compare --variant ... --models ...`, conforme o guia manual:

- `engineered`: três atributos derivados, por exemplo com Ridge;
- `selected`: mesmos atributos mais seleção de 75% das colunas codificadas;
- `pca`: PCA centrado, retendo pelo menos 80% da variância do treino; executar em Ridge e árvore;
- `weighted`: Ridge com pesos aprendidos da distribuição do alvo no treino;
- `without_socio` e `without_uf`: duas hipóteses adicionais de ablação, por exemplo com Ridge.

O boosting implementado é `GradientBoostingRegressor`. Não há evidência de um
HistGradientBoosting vencedor. O stacking original mantém o pré-processamento dentro das
suas dobras internas; variantes que ainda não preservam esse protocolo são recusadas.

Etapas finais, somente após concluir as comparações exigidas:

```bash
.venv/bin/python -m enem_base search --study configs/ciencias_natureza.toml \
  --cv resultados/ciencias_natureza/cv-nova --output resultados/ciencias_natureza/busca-nova
```

`freeze-solution` confere todas as famílias, busca nos três melhores e variantes obrigatórias;
`learning-curve` usa a solução congelada; `evaluate-final` exige a curva completa e cria uma
trava persistente por partição. Não execute o teste para decidir modelos ou parâmetros.
Comandos completos e critérios de aprovação estão em `docs/validacao-manual.md`.

## Resultados e figuras

Cada comparação grava dobras, resumo, erros por grupo, parâmetros, avisos e hashes.
O nome do arquivo não prova sucesso: conferir `status`, proveniência e ativos do manifesto.
Para publicar somente comparações concluídas:

```bash
.venv/bin/python scripts/preencher_resultados_experimentos.py \
  --runs resultados/ciencias_natureza/cv-recuperado-v2 \
  --output resultados/publicacao-nova
.venv/bin/python scripts/gerar_figuras_artigo.py \
  --dashboard resultados/ciencias_natureza/dashboard-v1 \
  --runs resultados/ciencias_natureza/cv-recuperado-v2 \
  --output resultados/figuras/execucao-nova
```

Os opcionais `--search`, `--curve` e `--final` no gerador de figuras adicionam somente
artefatos reais verificados. A ausência de uma etapa é registrada como pendência.
O consolidado só exporta previsões quando recebe `--final` de uma avaliação final válida.

## Dashboard e entregas

O dashboard consulta os agregados do SQLite em modo leitura; na ausência do banco,
utiliza os snapshots verificados. Não executa treinamento nem avaliação do teste.
`ENEM_DATABASE`, `ENEM_DASHBOARD_DIR` e `ENEM_RELATIONS_DIR` são substituições opcionais
de caminhos, não credenciais. Scripts de início estão em `scripts/iniciar_frontend.*`.

Entregas atuais, compiladas de fontes LaTeX:

- [Pitch: roteiro oral e perguntas](output/pdf/pitch.pdf), sem slides.
- [Acompanhamento e auditoria das execuções](output/pdf/acompanhamento.pdf).
- [Artigo em LaTeX, dez páginas](output/pdf/artigo_latex.pdf).
- [Pacote para importar no Overleaf](output/overleaf-enem2023.zip) e [instruções](relatorio/README.md).

Os relatórios preliminares e pacotes antigos foram retirados da área ativa e
preservados em `historico/2026-11-07/limpeza-pre-entrega.zip`. O artigo original do
Checkpoint 6 continua preservado para rastreabilidade; a entrega atual compilável
é a versão LaTeX indicada acima. Nomes: Joey Alan de Freitas Solis e Paulo Henrico,
Unifor, professor Tulio. A equipe deve ensaiar e consultar o prazo no AVA.

## Verificações de código e evidências científicas

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
uv pip check --python .venv/bin/python
```

A suíte existente em `tests/` usa fixtures técnicas e foi executada na revisão de
07/11/2026: **81 testes aprovados**. Isso é distinto das avaliações científicas com
os microdados nacionais. Na correção de 05/11 ela não havia sido executada; esse
registro histórico permanece verdadeiro. Não foram criados novos arquivos de testes.
A revisão atual também recompôs as 180 avaliações de busca e as métricas/grupos dos
cinco modelos no teste, sem novos treinamentos. [Cobertura e limites](docs/checkpoint-7-resultados.md).
Ruff ignora somente cópias históricas de código em `historico/` e `resultados/**/codigo`;
o código ativo em `src/`, `app/`, `scripts/` e `tests/` continua verificado.
