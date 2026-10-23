# Validação local da fase 1

Data: **16/10/2026**, America/Fortaleza. Escopo: infraestrutura, contratos e procedimentos
gerais com dados fictícios. Nenhuma nota foi escolhida para a pesquisa.

## Ambiente efetivamente usado

| Item | Versão/estado |
|---|---|
| Sistema | Windows 11, x64 |
| Python | 3.13.7, `.venv` isolado |
| Pacote local | enem-base 0.1.0, instalação editável |
| pandas | 3.0.6 |
| PyArrow | 24.0.0 |
| scikit-learn | 1.9.1 |
| Matplotlib | 3.11.2 |
| pytest | 9.1.1 |
| Ruff | 0.17.1 |
| Dependências | 27 pacotes fixados em `requirements.lock.txt`, incluindo setuptools 82.0.1 |
| Git | Repositório local ainda sem commit; nenhuma publicação realizada |

O pacote foi instalado também com `--no-deps --no-build-isolation -e .`, conforme
instruções do README. O lock é um snapshot de versões, sem hashes de distribuição.
Não houve certificação de compatibilidade em Linux; o workflow foi apenas preparado.

## Checks executados

Comando final de verificação: `scripts/verificar.ps1`.

| Check | Resultado observado |
|---|---|
| Ruff lint | All checks passed |
| Ruff format --check | Todos os arquivos aprovados |
| pytest -q | **52 passed**, 5,48 s na execução final |
| pip check | No broken requirements found |
| CLI de preparação do exemplo | passed, 12 linhas, synthetic=true, target=null |
| CLI de figura de qualidade | PNG gerado e inspecionado visualmente; legível, sem sobreposição |
| Roteiro `notebooks/00_qualidade_exemplo.py` | Executado, contagens e categorias conferidas |
| Proteção contra sobrescrita | Exercitada na importação, coleta e partições |
| `.gitignore` | Ambiente, Parquet, temporários e figura local ignorados |
| PDF de origem | Cópia idêntica ao original por SHA-256 |

Os testes não acessam a rede nem treinam modelos. Cobrem preservação da fonte,
cabeçalhos/linhas malformados, número não finito, ausências, decimais, edição/ano,
duplicatas entre lotes, falha sem dataset parcial, coleta local, checksums, limite de
tamanho, cardinalidade de junções, bloqueios de features e partições reproduzíveis.
Um teste integrado lê o Parquet produzido e verifica o pré-processamento com tipos
anuláveis do pandas. Outro comprova que imputação e categorias são aprendidas somente
com o treino fictício e permanecem iguais após transformar a validação.

## Evidência da demonstração

Fonte: `exemplos/dados_ficticios.csv`, 12 registros, cinco colunas, três lotes de quatro.
SHA-256: `c74396d93bf2dedf0a0d48a36a3401c0731cca00934b95a4ec808f408375d869`.

Saída local: `dados/processed/exemplo-v1/`, com três partes Parquet, relatório e manifesto.
Como são artefatos locais ignorados, podem ser reproduzidos pelo contrato do exemplo.
A repetição exige outro nome de saída para não sobrescrever a evidência existente.

| Verificação | Resultado |
|---|---|
| Linhas de entrada/saída | 12 / 12 |
| Linhas removidas / colunas removidas ou criadas | 0 / nenhuma |
| Identificadores ausentes ou repetidos | 0 |
| Duplicatas de conteúdo | 0 |
| Conversões numéricas inválidas | 0 |
| Espaços externos normalizados | 1 célula |
| Marcadores declarados convertidos para ausência | 4 células |
| Ausências em categoria / medida_a / medida_b | 1 / 1 / 2 |
| Zeros observados em medida_a / medida_b | 1 / 1 |
| Código textual preservado | `001` |
| Alvo / modelos treinados | null / false |

Figura local: `resultados/figuras/qualidade-exemplo.png`. Ela identifica dados fictícios
no título e na fonte. Demonstra somente a geração de figura técnica, sem inferência
sobre participantes ou notas do ENEM.

O PDF fornecido foi lido nas 16 páginas por extração textual e conferência visual do
conjunto de páginas. A cópia em `docs/referencias/enunciado-projeto2.pdf` tem SHA-256
`bfcf3dcd560ada4e137ab46467e33b7edaf818c1488d396c6a75ba2f807743bd`.
O original em Downloads permaneceu inalterado.

## Limites e pendências

- Não houve download, importação ou validação do pacote oficial e do dicionário de 2023.
  As 3.933.955 linhas e 76 colunas são o contrato do enunciado, não medição local.
- Download HTTPS foi implementado, mas não exercitado com a base oficial. A coleta
  foi validada com arquivo local, limite de tamanho, checksum e rejeição de HTTP.
- Não foram medidos RAM, disco e tempo em escala nacional. O custo e o crescimento
  do SQLite e das codificações devem ser avaliados antes dos experimentos reais.
- Partições e pré-processamento foram exercitados apenas em cenários fictícios. Não
  existem partições oficiais nem valores aprendidos usados para a pesquisa.
- Não há baseline, regressores, seleção, PCA, balanceamento, buscas, curva de aprendizado,
  métricas ou previsões reais. Os registros CSV têm apenas cabeçalhos.
- Os roteiros de artigo e slides não são documentos finais e não foram certificados
  como formatação ABNT. Prazos, integrantes e alvo ainda precisam ser registrados.
- O CI não foi executado remotamente; não houve commit, push ou criação de repositório remoto.
