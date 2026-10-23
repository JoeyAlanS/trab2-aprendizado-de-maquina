# Projeto 2 - Ciências da Natureza no ENEM 2023

**Tema definido em 21/10/2026: Ciências da Natureza e suas Tecnologias. Alvo: NU_NOTA_CN.**
A fase 1 estabeleceu a estrutura geral; a fase atual inicia o estudo com dados oficiais.
O estado verificável e as pendências ficam em `docs/andamento_ciencias_natureza.md`.
Os dados de demonstração em `exemplos/` continuam fictícios e separados da pesquisa.

O enunciado determina ENEM **2023 nacional completo**, regressão e protocolo de
avaliação. A escolha de Ciências da Natureza foi informada pelo usuário. A pergunta
e as hipóteses propostas estão em [docs/pesquisa_ciencias_natureza.md](docs/pesquisa_ciencias_natureza.md).
As demais exigências estão mapeadas em
[docs/requisitos.md](docs/requisitos.md), com distinção entre implementado e futuro.

## Frontend com os dados preparados

O dashboard em **Streamlit + Plotly**, no padrão de organização do Projeto 1,
apresenta visão geral, exploração com filtros, modelos e qualidade/metodologia.
Nesta pasta, o snapshot oficial do desenvolvimento já foi gerado. Para abrir:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

Acesse **http://127.0.0.1:8501**. Não é necessário repetir o download nem o treinamento.
O painel usa agregados dos 2.153.941 participantes de desenvolvimento e mantém o teste
reservado. Consulte [o guia do frontend](docs/frontend.md) para navegação, exportações,
arquitetura e atualização dos dados. Alternativa: `scripts/iniciar_frontend.ps1`.

**Ampliação em 23/10/2026:** a página **Relações e relatório** inclui as 40 entradas
em relação à nota, todos os 780 pares, 254 perfis e 29.709 células de cruzamento.
O relatório em LaTeX está em `relatorio/`, e o PDF de dez páginas em
`output/pdf/relatorio_ciencias_natureza.pdf`. Consulte
[o registro da análise ampliada](docs/relacoes_e_relatorio.md).

O **banco SQLite com a base limpa completa** também está no projeto existente,
em `dados/database/enem2023-v1/enem2023.sqlite3`. O frontend usa esse banco
automaticamente, em modo somente leitura, consultando seus resultados agregados.
Veja [as tabelas e instruções do banco](dados/database/README.md).

## Começar no Windows PowerShell

Requisito: Python **3.13** e Git. Execute a partir da raiz do repositório.
Não é necessário ativar o ambiente nem alterar a política de execução do Windows.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .

.\.venv\Scripts\python.exe -m enem_base --verbose prepare --config configs/exemplo.toml
.\.venv\Scripts\python.exe -m enem_base plot-quality --report dados/processed/exemplo-v1/qualidade.json --output resultados/figuras/qualidade-exemplo.png
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Em Linux/macOS, substitua `.\.venv\Scripts\python.exe` por `.venv/bin/python`.
O lock foi gerado no ambiente registrado em `docs/validacao-fase1.md`. O CI está
preparado para Windows e Linux, mas execução remota só poderá ser confirmada após
publicação. Em instalação nova sem lock, use `python -m pip install -e '.[dev]'`;
isso permite resolver novas versões dentro dos limites do `pyproject.toml`.

A demonstração lê 12 linhas em três lotes, normaliza espaços e marcadores declarados
de ausência, valida o contrato e gera um **dataset Parquet particionado** em
`dados/processed/exemplo-v1/`, `qualidade.json` e `manifesto.json`. Códigos como
`001` continuam sendo texto. Zeros são preservados. Não há imputação nessa etapa.
O código recusa sobrescrever saídas: para repetir, altere `output` em uma cópia do
TOML e escolha outro nome de execução. O diretório de uma saída reprovada é descartado;
erros de qualidade saem como JSON no stderr e o comando retorna código 2.

## Organização

```text
configs/                contratos de importação (exemplo e ENEM 2023)
app/                    frontend Streamlit com quatro páginas
.streamlit/             tema e configuração local do frontend
dados/
  raw/                  originais preservados; instruções de obtenção
  processed/            Parquet e metadados por execução; fora do Git
  splits/               identificadores e dobras quando o alvo for definido
docs/                   requisitos, decisões, metodologia e roteiros de entregas
exemplos/               CSV fictício pequeno e versionado
notebooks/              exploração técnica e roteiro para análise futura
src/enem_base/          módulos reutilizáveis e CLI
tests/                  contratos, regressões e execução integrada
resultados/             esquemas de experimentos, previsões e figuras
scripts/                verificação local reproduzível
.github/workflows/      qualidade e testes automáticos
```

## Procedimentos implementados

- Coleta explícita de arquivo local ou URL HTTPS, com limite de tamanho, SHA-256,
  manifesto e proteção contra sobrescrita; sem download automático da base nacional.
- CSV com separador, codificação, decimal, marcadores de ausência e tipos declarados.
  Rejeição de cabeçalhos ambíguos, linhas com quantidade incorreta de campos e
  conversões numéricas inválidas; não há descarte silencioso de linhas.
- Processamento completo em lotes e armazenamento Parquet com compressão Zstandard.
  Não concatena os lotes em memória, não amostra e não filtra por nota ou perfil.
- Diagnóstico de ausências, valores numéricos, zeros, duplicatas de conteúdo e
  identificadores repetidos entre lotes. SQLite temporário mantém os índices em disco.
- Rastreabilidade por hash da fonte, configuração, partes Parquet, versões, duração
  e estado do Git. Original e configurações são preservados.
- Fábrica de pré-processamento **não ajustada**: imputação numérica configurável,
  indicador de ausência, padronização e codificação categórica esparsa. Deve integrar
  um `Pipeline` ajustado somente no treino de cada dobra; não é executada no ENEM.
- Funções para partições 80/20, semente 42 e três dobras no desenvolvimento. Exigem
  alvo explícito e salvam só identificadores, conjunto e dobra; não avaliam modelos.
- Junção opcional de contexto com chave única, cardinalidade `many_to_one`, referência
  2023, cobertura e perdas. Nenhuma fonte externa foi escolhida ou integrada.
- Figura técnica de ausências, permitida nesta fase apenas para dados fictícios.

## Estudo de Ciências da Natureza

Em 21/10/2026 foram concluídas obtenção/validação da fonte nacional, partições,
exploração do desenvolvimento e comparação inicial de quatro modelos em três dobras.
Consulte [o relatório de andamento](docs/andamento_ciencias_natureza.md) e
[o rascunho do artigo](docs/artigo_ciencias_natureza_rascunho.md).
Os comandos de obtenção e as saídas v1 já foram executados nesta pasta; não é necessário
repetir o download para consultar os resultados. Para percorrê-los:

```powershell
.\.venv\Scripts\python.exe notebooks/01_ciencias_natureza.py
```

Contrato: `configs/ciencias_natureza.toml`. Os comandos abaixo devem seguir esta ordem.
Saídas existentes são preservadas; a segunda execução exige novos nomes de saída.

```powershell
.\.venv\Scripts\python.exe -m enem_base fetch-enem --raw dados/raw
.\.venv\Scripts\python.exe -m enem_base --verbose prepare --config configs/enem2023.toml
.\.venv\Scripts\python.exe -m enem_base split --study configs/ciencias_natureza.toml
.\.venv\Scripts\python.exe -m enem_base eda --study configs/ciencias_natureza.toml --output resultados/ciencias_natureza/eda-v1
.\.venv\Scripts\python.exe -m enem_base --verbose compare --study configs/ciencias_natureza.toml --output resultados/ciencias_natureza/cv-inicial-v1
```

O download usa HTTPS com verificação TLS pelo curl do sistema, retomada de `.part`,
trava contra execução simultânea e CRC do ZIP antes de publicar. Só extrai CSV nacional,
dicionário e Leia-me; mantém o ZIP. Após uma interrupção abrupta do processo, investigar
uma eventual trava remanescente antes de tentar novamente.

`split` utiliza somente ID e NU_NOTA_CN, sem exigir outras notas. `eda` e `compare`
verificam os hashes da fonte preparada e das partições e filtram IDs de desenvolvimento
antes de ler as features. O teste não é avaliado nesses comandos. A comparação padrão
tem quatro referências: média, linear sem regularização, Ridge e árvore. O catálogo
adicional aceita `--models svm knn bagging pasting random_forest boosting stacking`;
sua existência não prova execução ou atendimento de todas as exigências acadêmicas.

## Fonte nacional

O [portal oficial do Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem)
lista a edição de 2023. Consulte [dados/raw/README.md](dados/raw/README.md) para obter
o arquivo e o dicionário. A fonte e os tipos deverão ser conferidos no pacote recebido.
O contrato `configs/enem2023.toml` exige os **3.933.955 registros e 76 colunas citados
no enunciado**; uma divergência deve ser investigada e registrada, sem ajustar esses
números apenas para fazer o processamento passar.

```powershell
# Somente após obter e conferir o CSV nacional:
.\.venv\Scripts\python.exe -m enem_base --verbose prepare --config configs/enem2023.toml
```

O diagnóstico geral contabiliza todos os registros; a exploração que orienta decisões
de modelagem deverá ocorrer no desenvolvimento, após definir o alvo e reservar o teste.
Não imputar o alvo nem exigir outras notas. Não remover treineiros, idades ou notas zero.
O módulo `features.py` bloqueia notas, respostas, gabaritos, presença, situação da
redação, identificadores e ano como entradas. Códigos de prova também ficam bloqueados
conservadoramente; eventual revisão exige justificativa explícita pelo dicionário.
Essa barreira não substitui a revisão semântica das futuras features.

## Próxima fase e documentação

Alvo registrado em [docs/decisoes.md](docs/decisoes.md). Conferir o dicionário,
gerar e congelar as partições e explorar o desenvolvimento antes das comparações.
Criação de atributos, seleção, PCA, balanceamento, buscas e avaliação final seguem
[docs/metodologia.md](docs/metodologia.md), distinguindo execução real de planejamento.
Os roteiros em `docs/templates/` não são o artigo nem os slides finais.

Consulte também [docs/arquitetura.md](docs/arquitetura.md),
[docs/boas-praticas.md](docs/boas-praticas.md),
[docs/referencias.md](docs/referencias.md) e
[docs/validacao-fase1.md](docs/validacao-fase1.md).

## Limites desta entrega

O histórico da validação sintética está em `docs/validacao-fase1.md`; o progresso real
do estudo atual está em `docs/andamento_ciencias_natureza.md`. O índice SQLite cresce
com o número de registros e exige espaço em disco.
A importação faz leituras adicionais para validar o CSV e verificar a integridade;
ela privilegia rastreabilidade e detecção de erros. Os transformadores e o particionamento
trabalham com seus dados em memória: antes do uso nacional, planejar recursos conforme
`docs/arquitetura.md`. A preparação de comandos e roteiros não é uma entrega científica
final; conferir as etapas executadas e ainda pendentes no relatório de andamento.
