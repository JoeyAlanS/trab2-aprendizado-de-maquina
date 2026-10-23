# Arquitetura e contratos

O pacote `enem_base` usa layout `src/`, com instalação editável no ambiente isolado.
A CLI coordena módulos pequenos; não há lógica de negócio em notebooks.

```text
arquivo local / URL explícita
  -> acquisition.collect -> raw + manifesto da fonte
  -> config.load_config -> contrato do CSV
  -> ingestion.prepare
       cabeçalho e largura das linhas
       hash antes/depois
       leitura textual em lotes
       cleaning.normalize_chunk (sem estatísticas aprendidas)
       quality.QualityTracker (contagens + SQLite temporário)
       Parquet em área temporária
       validação global
  -> dataset aprovado + qualidade.json + manifesto.json

DEPOIS DA DEFINIÇÃO DO ALVO:
  identificador + alvo -> splits -> desenvolvimento / teste reservado + dobras
  desenvolvimento -> EDA e decisões
  treino de cada dobra -> Pipeline(preprocessing + etapas futuras + regressor)
  validação da dobra -> comparação; sem reajustar transformações
  solução congelada -> reajuste no desenvolvimento -> avaliação final do teste
```

## Módulos

| Módulo | Responsabilidade | Não executa |
|---|---|---|
| `acquisition.py` | Cópia/download com limite, checksum opcional e manifesto | Extração de ZIP, busca de fontes, download automático |
| `config.py` | Contrato TOML, caminhos, edição e tamanho esperado | Escolha de features ou alvo |
| `cleaning.py` | Espaços externos, marcadores explícitos e conversão numérica | Imputação, recodificação de alternativas, filtros |
| `quality.py` | Contagens globais, zeros, ausências e duplicatas entre lotes | Exclusão automática de duplicatas |
| `ingestion.py` | Validação e publicação do dataset completo em partes | Seleção de participantes ou amostragem |
| `provenance.py` | Hashes, versões, Git e serialização | Reprodução do estado não commitado do código |
| `features.py` | Alvos possíveis e bloqueios comuns de vazamento | Garantia semântica de toda futura coluna derivada |
| `preprocessing.py` | Fábrica sklearn não ajustada | Ajuste prévio no dataset inteiro |
| `splits.py` | IDs 80/20, dobras e persistência após alvo explícito | Treinamento e avaliação |
| `integration.py` | Junção many-to-one com cobertura e ano informado | Validação automática da credibilidade da fonte |
| `visualization.py` | Figura de qualidade em dados fictícios | EDA real global antes de reservar o teste |

## Dados e integridade

Todos os campos são lidos inicialmente como texto. Só as colunas declaradas numéricas
são convertidas para `float64` anulável; identificadores e códigos mantêm zeros à esquerda.
Cada parte Parquet usa o mesmo schema. A máscara de ausência é explícita e sensível a
maiúsculas; categorias como desconhecimento e não informação não são inferidas como nulas.

`qualidade.json` traz contagens e não inclui registros individuais. `manifesto.json`
contém a identidade da fonte e da configuração, parâmetros efetivos, partes, hashes,
versões, duração, alvo nulo e `models_trained=false`. O hash da configuração complementa
os parâmetros: versionar o TOML e o código antes de associar resultados científicos.

Um dataset só é publicado se todas as verificações passarem. A publicação renomeia
o diretório temporário na mesma unidade. Duplicatas e erros numéricos não são corrigidos
silenciosamente. Ao reprovar a qualidade, a CLI imprime o relatório JSON em stderr;
para arquivá-lo: `... prepare --config ... 2> resultados/falhas/execucao.json`
(criar antes a pasta e usar nome novo). Falhas estruturais de CSV produzem mensagem
de erro com linha, sem incluir o conteúdo do participante.

As saídas aprovadas são imutáveis por convenção e recusam sobrescrita. O projeto não
é um serviço concorrente: usar apenas uma execução por destino. A coleta tem escrita
exclusiva do arquivo final; interrupção do processo ou falta de espaço durante essa
cópia pode deixar um arquivo incompleto sem manifesto. Nesse caso, não o utilizar;
conferir o hash e escolher novo destino para repetir. Não há retomada de download.

## Volume e custo

A importação mantém em memória um lote, as contagens das colunas e a lista de partes.
Os índices de identificadores e hashes de linhas ficam em SQLite temporário, com
crescimento proporcional ao número de registros. A detecção de conteúdo repetido usa
SHA-256 sobre a linha normalizada; colisões são teoricamente possíveis. Repetição de
identificador usa igualdade textual no banco. Isso detecta repetições entre lotes.

A verificação percorre a fonte para hash, validação estrutural e importação, e verifica
o hash novamente ao final. Planejar disco para CSV, saída Parquet, ZIP opcional e índices
temporários. `chunksize=50000` é ponto de partida configurável, sem benchmark nacional.
A validação de largura é deliberadamente uma passada adicional, pois linhas curtas
podem ser aceitas pelo leitor CSV como células ausentes sem representar a fonte.

O pré-processamento sklearn não é out-of-core. One-hot pode crescer com cardinalidades
altas; sua saída esparsa evita uma densificação global por padrão, mas não garante que
todo regressor posterior aceite a representação. Planejar PCA/IncrementalPCA, algoritmos
permitidos, cache e `n_jobs` depois do diagnóstico. Evitar paralelismo aninhado de busca,
dobras e estimadores. O particionamento recebe só IDs e alvo; não carregar todas as
76 colunas para essa operação. As partições ocupam memória proporcional às linhas.

Não reduzir a comparação principal a uma amostra por conveniência. Uma limitação de
hardware deve ser medida, documentada e resolvida com representação, lotes ou algoritmo
permitido; subconjuntos de curva de aprendizado têm finalidade diagnóstica específica.

## Extensão

Adicionar etapas novas como funções ou estimadores sklearn, com configuração explícita
e testes do contrato. Para modelagem futura, colocar cada transformação aprendida no
Pipeline e usar os índices de `validation_fold` já persistidos. Para stacking, cada
modelo base precisa de seu próprio Pipeline dentro das dobras internas. Não executar
um único pré-processamento ajustado no desenvolvimento antes da CV.
