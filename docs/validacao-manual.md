# Guia de validação manual com dados reais

Executar na raiz do repositório, com Python 3.13. Todos os nomes `manual-*` abaixo são
**diretórios novos de saída**, não dados de exemplo. Se já existirem, escolher outro nome.
Não apagar execuções anteriores para repetir um comando. Não executar os scripts do histórico.

Os dados nacionais e as partições foram recuperados de um SQLite cujo SHA-256 coincide com
o manifesto histórico. A rotina recusará entradas alteradas. O teste de 20% foi avaliado
no Checkpoint 4 com receitas fixadas previamente; preservar sua trava e seus resultados.
Os comandos de avaliação para uma única solução abaixo são históricos. Para conferir
a execução concluída do trio, usar o executor do Checkpoint 4 na seção final deste guia.
As verificações de código feitas com um subconjunto real são diagnósticos técnicos, não substituem
a comparação científica com todo o desenvolvimento.

## 1. Ambiente e CLI

**Objetivo:** confirmar interpretador, dependências, estilo e disponibilidade dos comandos.
**Pré-requisitos:** `.venv` existente ou instalação pelo README; sem credenciais.

**Procedimento:**

```bash
.venv/bin/python --version
uv pip check --python .venv/bin/python
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m enem_base --help
```

**Resultado esperado:** Python 3.13, dependências compatíveis, lint e formatação aprovados,
comandos de recuperação, comparação, buscas, curva e avaliação final listados.
**Critério de aprovação:** todos terminam com código 0.
**Possíveis erros:** ambiente ausente; pacote não instalado; intérprete fora de 3.13;
versão de scikit-learn inferior a 1.7, que não oferece o `tol` usado em LinearRegression.
Não interpretar uma falha de rede no instalador como incompatibilidade do código.

## 2. SQLite nacional e snapshots

**Objetivo:** conferir a identidade dos dados reais sem alterá-los.
**Pré-requisitos:** banco e manifesto em `dados/database/enem2023-v1/`.

**Procedimento:**

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
from enem_base.database import load_database, readonly_connection
p = Path('dados/database/enem2023-v1/enem2023.sqlite3')
d = load_database(p)
print('Linhas:', d.manifest['rows'], 'Colunas:', d.manifest['columns'])
with readonly_connection(p) as c:
    print('Integridade:', c.execute('PRAGMA quick_check').fetchone())
    print('Chaves:', c.execute('PRAGMA foreign_key_check').fetchmany(1))
    print('Partições:', c.execute('SELECT * FROM contagens_particoes').fetchall())
PY
```

**Resultado esperado:** 3.933.955 linhas, 76 colunas, `ok`, nenhuma falha de chave,
2.153.941 participantes de desenvolvimento e 538.486 de teste.
**Critério de aprovação:** hash, metadados, contagens e integridade aprovados.
**Possíveis erros:** arquivo faltante, nome diferente do manifesto, hash incorreto,
SQLite incompleto ou alterado. Não alterar o hash do manifesto para fazer o arquivo passar.

## 3. Recuperação de Parquet e partições

**Objetivo:** restaurar toda a base limpa e a divisão original a partir do banco.
**Pré-requisitos:** item 2 aprovado; saídas de dataset e partições ainda inexistentes.
Nesta máquina a recuperação já foi executada: não é necessário repeti-la.

**Procedimento em instalação sem essas saídas:**

```bash
.venv/bin/python -m enem_base --verbose recover-database \
  --study configs/ciencias_natureza.toml \
  --database dados/database/enem2023-v1/enem2023.sqlite3
```

**Resultado esperado:** 79 partes Parquet, manifestos, relatório de qualidade preservado
com escopo histórico explícito, e `particoes.parquet` com os mesmos IDs/dobras do banco.
**Critério de aprovação:** `status=completed`, `partition_membership_verified=true`,
3.933.955 linhas e 2.692.427 IDs elegíveis.
**Possíveis erros:** diretório existente (recusa esperada), espaço insuficiente, inconsistência
entre o banco e a semente 42, ou corrupção. A recuperação não produz um CSV bruto fictício.

## 4. Fonte original, qualidade e EDA

**Objetivo:** obter e preparar a fonte bruta quando necessário e explorar somente o desenvolvimento.
**Pré-requisitos:** rede para o Inep, espaço em disco e ausência de outra transferência ativa.
Não repetir `prepare` sobre a recuperação já existente; para uma nova ingestão, criar uma
cópia do TOML com outros diretórios de saída e manter a fonte original preservada.

**Procedimento de obtenção em ambiente novo:**

```bash
.venv/bin/python -m enem_base fetch-enem --raw dados/raw
.venv/bin/python -m enem_base --verbose prepare --config configs/enem2023.toml
.venv/bin/python -m enem_base split --study configs/ciencias_natureza.toml
```

**Procedimento de EDA com a preparação atual:**

```bash
.venv/bin/python -m enem_base eda --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/manual-eda
```

**Resultado esperado:** arquivos íntegros, 76 colunas e população nacional completa;
EDA com 2.153.941 participantes, 13.236 zeros e `test_evaluated=false`.
**Critério de aprovação:** manifesto e diagnóstico concluídos; nenhuma nota ausente imputada.
**Possíveis erros:** servidor indisponível, download interrompido, trava antiga, CSV malformado,
CRC inválido, hash divergente ou saída existente. Investigar a trava antes de movê-la;
não remover uma trava de um processo em execução.

## 5. Modelos iniciais

Na cópia atual, o catálogo inicial já foi executado: quatro referências em
`cv-recuperado-v2` e os sete algoritmos no [Checkpoint 1](checkpoint-1-resultados.md).
Os comandos abaixo são para reprodução em novas saídas; não é necessário repetir
os treinamentos para conferir os resultados e seus hashes.

O [Checkpoint 2](checkpoint-2-resultados.md) também está concluído: seleciona Stacking,
SVM linear e Random Forest entre os sete algoritmos solicitados. Seu relatório contém
o comando de reprodução, critérios, verificações executadas e diferenças de escopo
frente ao catálogo ampliado usado pela busca legada. A reprodução usa uma nova pasta
de saída e reutiliza as métricas reais; não treina modelos nem consulta o teste.

**Objetivo:** comparar as onze entradas do catálogo, incluindo o baseline, nas mesmas dobras.
**Pré-requisitos:** dados e partições verificados; memória/CPU e tempo disponíveis.
A comparação principal utiliza todos os participantes do desenvolvimento.

**Procedimento:**

```bash
.venv/bin/python -m enem_base --verbose compare --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/manual-inicial \
  --models baseline linear ridge arvore svm knn bagging pasting random_forest boosting stacking
```

Alternativa: usar uma rodada para quatro modelos e outra para as sete famílias restantes,
sem repetir modelos nos diretórios passados conjuntamente à busca.

**Resultado esperado:** três registros por modelo, resumo de RMSE/MAE/R², tempos, avisos,
erros por grupos e manifesto com hashes. Não é exigido um valor específico de R².
**Critério de aprovação:** 33 avaliações para o catálogo completo; cada modelo cobre
2.153.941 participantes nas validações; `status=completed`, `test_evaluated=false`.
**Possíveis erros:** falta de RAM, custo elevado do KNN, avisos de convergência ou interrupção.
Uma execução `running`/`failed` não atende ao requisito. Não reduzir a base para obter sucesso.

## 6. Engenharia, seleção, PCA, ponderação e hipóteses adicionais

**Objetivo:** comparar representações e estratégias preservando o protocolo.
**Pré-requisitos:** mesma preparação e mesmas partições do item 5.

**Procedimento:**

```bash
.venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --variant engineered --models ridge --output resultados/ciencias_natureza/manual-engineered
.venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --variant selected --models ridge --output resultados/ciencias_natureza/manual-selected
.venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --variant pca --models ridge arvore --output resultados/ciencias_natureza/manual-pca
.venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --variant weighted --models ridge --output resultados/ciencias_natureza/manual-weighted
.venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --variant without_socio --models ridge --output resultados/ciencias_natureza/manual-without-socio
.venv/bin/python -m enem_base compare --study configs/ciencias_natureza.toml --variant without_uf --models ridge --output resultados/ciencias_natureza/manual-without-uf
```

**Definições:** computadores por morador trata a alternativa “quatro ou mais” como limite
inferior; acesso digital soma presença de computador e internet; escolaridade parental
máxima exige as duas respostas conhecidas. Valores ausentes passam pelo tratamento da dobra.
A seleção considera os 75% com maior estatística F. PCA centra as colunas e usa a variância
natural dos indicadores one-hot, com Q005 previamente padronizada. Pesos inversos são
aprendidos em dez faixas de largura igual definidas pelo alvo do treino.

**Resultado esperado:** três dobras por modelo/variante; seis registros para PCA; diagnósticos
com componentes/variância, colunas selecionadas ou faixas/pesos efetivamente aprendidos.
As ablações investigam contribuição do bloco socioeconômico e da UF da prova.
**Critério de aprovação:** cobertura integral, parâmetros aprendidos no treino, métricas
recalculadas e comparação com os modelos originais; melhorias não são obrigatórias.
**Possíveis erros:** categorias inválidas, memória da representação densa do PCA, conjunto
sem variância ou combinação não implementada. Stacking com seleção/PCA é recusado, pois
transformar antes das dobras internas produziria vazamento. O stacking original é preservado.

## 7. Busca nos três melhores

**Objetivo:** escolher automaticamente os três melhores regressores iniciais distintos e
avaliar doze configurações de cada um usando GridSearchCV com as dobras persistidas.
**Pré-requisitos:** catálogo inicial completo, sem duplicações e com a mesma proveniência.

**Procedimento:**

```bash
.venv/bin/python -m enem_base --verbose search --study configs/ciencias_natureza.toml \
  --cv resultados/ciencias_natureza/manual-inicial \
  --output resultados/ciencias_natureza/manual-busca
```

Se os modelos foram separados em rodadas, listar todos os diretórios depois de `--cv`.
**Resultado esperado:** ranking inicial, três arquivos `busca_MODELO.csv`, métricas por dobra,
parâmetros, tempos e `melhores.json`; nenhum acesso ao teste.
**Critério de aprovação:** exatamente os três melhores do ranking, pelo menos dez configurações
válidas de cada um e manifesto completo. A configuração de erro é `raise`, sem falha silenciosa.
**Possíveis erros:** falta de famílias, proveniências diferentes, configurações inválidas ou
recursos insuficientes. A recusa de buscar em apenas quatro modelos é comportamento esperado.

## 8. Congelamento da solução

**Objetivo:** escolher a configuração exclusivamente pelo desenvolvimento e registrar a decisão.
**Pré-requisitos:** itens 5–7 completos, incluindo as seis variantes exigidas.

**Procedimento:**

```bash
.venv/bin/python -m enem_base freeze-solution --study configs/ciencias_natureza.toml \
  --cv resultados/ciencias_natureza/manual-inicial \
  --search resultados/ciencias_natureza/manual-busca \
  --variants resultados/ciencias_natureza/manual-engineered resultados/ciencias_natureza/manual-selected resultados/ciencias_natureza/manual-pca resultados/ciencias_natureza/manual-weighted resultados/ciencias_natureza/manual-without-socio resultados/ciencias_natureza/manual-without-uf \
  --output resultados/ciencias_natureza/manual-solucao
```

**Resultado esperado:** `solution.json` com receita, estimador, hashes das evidências, critério,
faixas e grupos a manter no teste. A implementação escolhe o menor RMSE entre configurações
originais, buscas e variantes, preservando o original se uma busca piorar seu resultado.
**Critério de aprovação:** pré-requisitos satisfeitos e somente evidências do desenvolvimento.
**Possíveis erros:** PCA em apenas um regressor, busca incompleta, variante sem Ridge, entrada
alterada ou seleção do conjunto de teste. Não editar a receita depois de consultar o teste.

## 9. Curva de aprendizado

**Objetivo:** medir ajuste/validação em 10%, 25%, 50%, 75% e 100% do treino de cada dobra.
**Pré-requisitos:** solução congelada e inalterada.

**Procedimento:**

```bash
.venv/bin/python -m enem_base --verbose learning-curve --study configs/ciencias_natureza.toml \
  --solution resultados/ciencias_natureza/manual-solucao \
  --output resultados/ciencias_natureza/manual-curva
```

**Resultado esperado:** quinze avaliações, validação fixa, subconjuntos progressivos com
semente 42 e reajuste de todas as etapas. Não inclui teste nem nova busca por tamanho.
**Critério de aprovação:** cinco frações em cada dobra, métricas finitas, contagens e hash
da mesma solução; gráfico mostra média e desvio das três dobras.
**Possíveis erros:** solução alterada, falta de variância em um treino ou recurso insuficiente.
Curvas próximas não provam “generalização perfeita”.

## 10. Avaliação final e previsões

**Objetivo:** avaliar baseline, linear e solução final nos mesmos participantes reservados.
**Pré-requisitos:** solução congelada, curva completa, todas as decisões já encerradas.
Este comando não é uma verificação de interface: ele realiza a avaliação científica final.

**Procedimento, uma única vez após atender os pré-requisitos:**

```bash
.venv/bin/python -m enem_base evaluate-final --study configs/ciencias_natureza.toml \
  --solution resultados/ciencias_natureza/manual-solucao \
  --curve resultados/ciencias_natureza/manual-curva \
  --output resultados/ciencias_natureza/manual-teste-final
```

**Resultado esperado:** ajuste em todo o desenvolvimento, 538.486 linhas reais de previsões,
IDs originais, métricas e resíduos por faixa/escola/UF/renda; trava persistente por partição.
**Critério de aprovação:** IDs únicos, cobertura integral, métricas calculadas do CSV e hashes;
nenhum ajuste de escolha depois de observar o teste.
**Possíveis erros:** execução final já iniciada, curva/solução incompatíveis ou falha de recursos.
Se houver interrupção, preservar a trava e o estado; investigar antes de autorizar retomada.
Não apagar a trava para experimentar várias soluções no teste.

## 11. Exportação de resultados e figuras

**Objetivo:** comprovar que tabelas e gráficos derivam dos registros calculados.
**Pré-requisitos:** pelo menos uma comparação concluída. Etapas ausentes permanecem pendentes.

**Procedimento inicial:**

```bash
.venv/bin/python scripts/preencher_resultados_experimentos.py \
  --runs resultados/ciencias_natureza/cv-recuperado-v2 \
  --output resultados/manual-publicacao
.venv/bin/python scripts/gerar_figuras_artigo.py \
  --dashboard resultados/ciencias_natureza/dashboard-v1 \
  --runs resultados/ciencias_natureza/cv-recuperado-v2 \
  --output resultados/figuras/manual-verificadas
```

Quando existirem, acrescentar as comparações de variantes à lista `--runs`. O gerador de
figuras recebe `--search`, `--curve` e `--final`. O consolidado recebe `--final` para copiar
as previsões reais, recalculando suas métricas antes da exportação.

**Resultado esperado:** dobras e resumos reais; histograma com contagens observadas;
figuras adicionais somente quando houver evidência; pendências no manifesto.
**Critério de aprovação:** nenhuma métrica literal inventada, nenhuma nota aleatória,
nenhuma previsão sem execução final; inspeção visual de eixos, fontes, população e legendas.
**Possíveis erros:** manifesto incompleto/sem hashes, origem diferente, arquivo alterado,
CSV final com contagens ou métricas divergentes, diretório existente.

## 12. Dashboard, filtros, downloads e entregáveis

**Objetivo:** validar navegação e consultas ao banco sem modificar participantes.
**Pré-requisitos:** banco válido ou snapshots íntegros.

**Procedimento:**

```bash
.venv/bin/python -m streamlit run app/app.py --server.address 127.0.0.1
```

Abrir http://127.0.0.1:8501. Percorrer Visão geral, Explorar dados, Relações e relatório,
Modelos e Qualidade e método. Filtrar UF da prova, escola, sexo e treineiro; limpar filtros;
consultar as opções de relações; baixar tabelas/manifestos e o relatório preliminar.

**Resultado esperado:** sem exceções; sem filtro, 2.153.941 participantes; filtros coerentes;
modelos e método identificam a população global; a página de relações deixa claro seu escopo.
**Critério de aprovação:** contagens conciliam, downloads abrem, banco permanece inalterado,
nenhuma tela apresenta resultados sintéticos como evidência.
**Possíveis erros:** porta ocupada, pacote ausente, manifesto/hash inválido, filtro sem registros.
Um recorte vazio deve receber mensagem, não erro nem linhas inventadas.

Para os entregáveis, conferir autores reais, link do repositório, referências, artigo ABNT
com no máximo dez páginas, PDF do acompanhamento e PDF do pitch; ensaiar 10–15 minutos
e participação de todos. Esses requisitos não são satisfeitos somente pelo dashboard.

## O que foi executado nesta intervenção

### Curvas do trio selecionado — Checkpoint 3

O fluxo próprio de `scripts/executar_checkpoint3.py` consome a seleção validada do
Checkpoint 2. Os comandos e as regras de retomada estão em
[checkpoint-3-protocolo.md](checkpoint-3-protocolo.md). Esse fluxo amplia as curvas
para três modelos; não altera a avaliação final legada de uma única solução.

**Pré-requisitos:** Checkpoint 2 concluído, mesma base e partições, dependências e
código numérico do protocolo. Nenhum alvo do teste é carregado para estas curvas.

**Conferência:** examinar `protocolo.json`, os quinze JSONs em `pontos/` de cada
família, os três `curvas.csv` e seus manifestos concluídos. Conferir os cinco tamanhos,
três dobras, hashes dos IDs, composição cumulativa, métricas de treino/validação e
avisos. Os arquivos de modelos ajustados são locais e não entram no Git.

Após os 45 pontos estarem concluídos:

```bash
.venv/bin/python scripts/publicar_checkpoint3.py \
  --study configs/ciencias_natureza.toml \
  --selection resultados/ciencias_natureza/checkpoint-2-2026-11-06 \
  --root resultados/ciencias_natureza/checkpoint-3-2026-11-06 \
  --checkpoint1 resultados/ciencias_natureza/checkpoint-1-2026-11-06 \
  --output resultados/ciencias_natureza/checkpoint-3-2026-11-06/publicacao
```

**Aprovação:** 45 pontos sem duplicação, mesmos IDs entre modelos, nove avaliações em
100% reproduzindo CP1 com tolerância absoluta de 10⁻⁸, médias e DP (`ddof=0`) recompostos,
gráficos inspecionados e relatório com interpretação e limites. A publicação recusa
etapas incompletas e diretórios existentes; seu manifesto numérico não substitui a
validação visual nem o fechamento do checkpoint. Não misturar esses 45 pontos com
as comparações iniciais em `resultados/experimentos.csv`.

**Erros possíveis:** plano/código alterado, pacote com outra versão, modelo serializado
ausente ou modificado, ponto incompleto ou resultado em 100% divergente. Preservar as
evidências e investigar; não substituir métricas pela comparação anterior.

### Registro das intervenções

A lista exata, os resultados e os caminhos das evidências estão em
`docs/relatorio-correcao-2026-11-05.md`. Não transformar os procedimentos deste guia em
alegação de execução: comandos documentados e comandos realmente executados são distintos.
A suíte sintética legada não foi executada, e nenhum arquivo novo de testes foi criado.

## Checkpoint 4: buscas e fluxo do trio

**Objetivo:** conferir seleção, curvas e avaliação final dos três algoritmos, mantendo
baseline e linear de referência e atendendo também às buscas do catálogo ampliado.

**Pré-requisitos:** Checkpoints 1–3 concluídos, mesma base/partições/dicionário e versões
do ambiente; cache validado em participantes reais; cinco buscas completas e variantes
obrigatórias disponíveis para congelar as receitas. Os modelos locais serializados
precisam estar disponíveis para retomar sem novo ajuste.

**Procedimento:** executar os comandos explícitos de cada etapa no
[protocolo do Checkpoint 4](checkpoint-4-protocolo.md). A ordem é busca → congelamento
→ curvas finais → reajuste nos 80% → teste reservado → publicação e revisão visual.
Não executar o fluxo legado de uma única solução para substituir o fluxo atual do trio.

**Resultado esperado:** 60 configurações/180 avaliações nacionais, receitas identificadas
por hashes, 15 pontos por curva congelada e cinco modelos finais quando a solução
acadêmica coincidir com um dos três selecionados. O teste deve conter exatamente
538.486 participantes e uma previsão de cada modelo para cada participante.

**Critérios de aprovação:** métricas recalculadas das previsões, cobertura integral dos
IDs, parâmetros e fontes íntegros, zero avisos, reprodução da validação em 100% das
curvas, contagens e métricas por grupo conferidas, gráficos legíveis. A conclusão
exige o registro final do checkpoint; não basta existir o comando ou o arquivo CSV.

**Erros possíveis:** uma busca ou curva incompleta, alteração de código/ambiente/fonte,
ausência dos pesos locais, configurações diferentes na retomada ou tentativa de abrir
o teste antes da hora. Preservar os registros e investigar. Não apagar a trava
`dados/splits/ciencias-natureza-v1/avaliacao_final.json` para repetir a seleção.

**Executado até esta atualização:** cinco buscas concluídas; 180 avaliações recompostas,
sem avisos; receitas congeladas e dois gráficos de busca conferidos. As guardas que
recusam teste sem congelamento e reajuste sem curvas completas foram verificadas.
A exportação e recomposição dos erros por grupo passaram em 2.048 participantes reais
do desenvolvimento. As curvas finais foram concluídas e validadas: 45 pontos,
zero avisos, reprodução da CV em 100% e dois gráficos conferidos. Os cinco reajustes
completos e a avaliação dos 538.486 participantes foram concluídos. Foram recompostas
as cinco métricas globais e todas as métricas/contagens dos 260 registros por grupo.
Os nove gráficos finais foram revisados em `publicacao-v2/`.
[Relatório das buscas](checkpoint-4-buscas.md), [curvas finais](checkpoint-4-curvas.md)
e [avaliação final](checkpoint-4-resultados.md).

Para validar novamente a execução existente, sem novo ajuste nem novas previsões:

```bash
.venv/bin/python scripts/executar_checkpoint4.py \
  --study configs/ciencias_natureza.toml \
  --output resultados/ciencias_natureza/checkpoint-4-2026-11-07 --stage test
```

Com a trava em `completed`, esse comando apenas confere os pesos, a identidade
e os resultados salvos. Não remover a trava para fazer novas escolhas no teste.

## Checkpoint 5: galeria e coleção visual

Abrir `resultados/ciencias_natureza/checkpoint-5-2026-11-07/index.html` no navegador.
Conferir os filtros: Todos = 17, Desenvolvimento = 8, Teste = 9. Abrir PNG, SVG
e tabelas pelos links. Conferir títulos, eixos, legendas e a população indicada.

```bash
.venv/bin/python scripts/validar_checkpoint5.py \
  --collection resultados/ciencias_natureza/checkpoint-5-2026-11-07
```

A rotina confere hashes, resolução, cobertura e links com arquivos reais. Não treina
modelos nem recalcula previsões. Uma alteração em uma fonte ou artefato deve bloquear
a validação. Instruções de reprodução e mapeamento do enunciado no
[relatório do Checkpoint 5](checkpoint-5-resultados.md).
