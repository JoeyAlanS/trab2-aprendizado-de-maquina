# Frontend em Python — Ciências da Natureza

O frontend utiliza **Streamlit 1.66.1** e **Plotly 6.9.0**, seguindo a organização
do dashboard do Projeto 1: barra lateral com filtros, cartões de indicadores,
gráficos interativos e tabelas. A implementação é local, na pasta deste projeto.

## Abrir

Na raiz do projeto, execute no PowerShell:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

Acesse **http://127.0.0.1:8501**. Para encerrar, use `Ctrl+C` no terminal do servidor.
Como alternativa, execute `scripts/iniciar_frontend.ps1`; o parâmetro `-Porta 8502`
permite escolher outra porta. O comando direto de Python não depende da política
de execução de scripts do Windows. Não é necessário ativar a `.venv`.

Em uma instalação nova, siga os comandos de ambiente do README. O lock inclui o
frontend. O servidor escuta apenas em `127.0.0.1`, para acesso neste computador.

## Telas e operação

1. **Visão geral**: participantes, média, desvio amostral e zeros no recorte;
   distribuição de notas, comparação por escola e contagens do protocolo nacional.
2. **Explorar dados**: comparação por UF da prova, escola, renda familiar, sexo
   informado ou condição de treineiro; escolha entre média e participantes, tabela
   e CSV do recorte. Renda usa as alternativas A–Q do questionário de 2023.
3. **Modelos**: quatro modelos já executados, RMSE, MAE e R²; desvio entre dobras,
   tempos, resultados completos para download e consulta das três dobras.
4. **Qualidade e método**: contagens de ingestão, ausências do desenvolvimento,
   dicionário pesquisável com alternativas oficiais, protocolo, limites e manifesto.
5. **Relações e relatório** (23/10): as 40 entradas em relação à nota, todos os
   780 pares, cruzamentos, matrizes, CSV, ZIP e relatório técnico em PDF.
   Esses resultados são globais e não usam os filtros laterais. Guia e evidências
   em `docs/relacoes_e_relatorio.md`.

Os filtros laterais se combinam por interseção: UF da aplicação da prova, tipo de
escola, sexo informado e treineiro. Sem seleção de UF significa **todas as UFs**.
“Limpar filtros” retorna ao desenvolvimento completo. Recortes sem participantes
mostram uma mensagem e mantêm os filtros acessíveis para correção.

Os filtros afetam a visão geral e a exploração. As contagens nacionais do protocolo,
os resultados de modelos e os diagnósticos de qualidade são globais, explicitamente
identificados na interface. Não há treinamento nem previsão individual pelo painel.

Os CSVs usam UTF-8 com BOM, separador `;` e decimal `,`. O CSV do recorte acrescenta
conjunto, alvo, filtros e data do snapshot, para preservar o contexto da exportação.
Os gráficos permitem consultar valores ao passar o mouse e exportar uma figura PNG
pela barra de ferramentas do Plotly. Tabelas complementam os gráficos.

## Dados utilizados

O snapshot padrão fica em `resultados/ciencias_natureza/dashboard-v1/`:

- `agregados.parquet`: 54.516 grupos com estatísticas dos **2.153.941 participantes
  de desenvolvimento**, sem identificadores nem linhas individuais;
- `diagnostico.json`, `qualidade.json` e `dicionario.json`: metadados e diagnósticos;
- `resumo_cv.csv` e `dobras.csv`: métricas já executadas em validação cruzada;
- `manifesto.json`: proveniência, contagens e SHA-256 de todos os ativos.

O Parquet agregado tem 989.247 bytes. A interface não relê o CSV de 1,77 GB nem
as partições de indivíduos a cada clique. O carregamento usa cache limitado a duas
entradas e uma hora, invalidado também pelo tamanho/data de alteração dos ativos.
Os hashes do snapshot são conferidos em uma nova carga. Não existe fallback fictício:
fonte ausente ou alterada interrompe o painel com orientação de recuperação.

As notas originais geram contagem, soma, soma dos quadrados, mínimo, máximo e zeros
por UF, escola, sexo, treineiro, renda e intervalo de nota. A média de um recorte é
`soma das notas / participantes`, e não a média das médias dos grupos. O desvio usa
`ddof=1`. O histograma usa intervalos **[início, fim), de 25 pontos**; somente o
histograma é agrupado por faixa, sem aproximação da média ou do desvio.

O teste de **538.486 participantes** permanece reservado. A interface só conhece
sua contagem de protocolo. As notas zero do desenvolvimento continuam incluídas.
“Não respondeu” é categoria própria; a UF representa a aplicação da prova.

## Atualizar o snapshot

O snapshot é uma fotografia dos resultados existentes, não um monitor de novas
execuções. Para atualizar após nova EDA/CV, gere outro diretório:

```powershell
.\.venv\Scripts\python.exe -m enem_base dashboard-data --study configs/ciencias_natureza.toml --eda resultados/ciencias_natureza/eda-v1 --cv resultados/ciencias_natureza/cv-inicial-v1 --output resultados/ciencias_natureza/dashboard-v2
$env:ENEM_DASHBOARD_DIR = (Resolve-Path 'resultados/ciencias_natureza/dashboard-v2').Path
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

O comando usa `load_development`: confere as partes Parquet e as partições e filtra
os IDs de desenvolvimento antes de retornar as variáveis. Exige que EDA e CV tenham
o mesmo alvo, fonte, partições, contrato e dicionário, com `test_evaluated=false`.
Confere também contagens, zeros e média contra a EDA. A geração usa o desenvolvimento
completo em memória, como a análise anterior; o frontend usa apenas seus agregados.
Uma saída existente não é sobrescrita. O diretório temporário só é publicado após
validar a leitura e os hashes. Para voltar ao snapshot padrão, remova a variável da
sessão com `Remove-Item Env:ENEM_DASHBOARD_DIR` e reinicie o servidor.

## Organização do código

| Caminho | Responsabilidade |
|---|---|
| `app/app.py` | Entrada, navegação, identificação do estudo e filtros compartilhados |
| `app/app_pages/` | Cinco páginas de apresentação, sem regras de modelagem |
| `src/enem_base/database.py` | Construção e leitura dos agregados do SQLite local |
| `src/enem_base/dashboard.py` | Agregação, geração, validação e consultas dos dados do painel |
| `src/enem_base/dashboard_ui.py` | Cache, rótulos oficiais, componentes e gráficos compartilhados |
| `.streamlit/config.toml` | Tema e configuração local, sem CSS ou fontes remotas |
| `tests/test_dashboard.py` | Contratos matemáticos, isolamento, integridade e interações AppTest |
| `scripts/iniciar_frontend.ps1` | Iniciar o servidor local, com porta opcional |

## Validação e limites

Os testes AppTest percorrem as páginas, filtros e reset, interseção vazia, escolha
de métrica, dicionário com e sem resultados, controles de exportação e erro de dados
ausentes. Testes de dados com fixtures fictícias conferem médias ponderadas, desvio,
zeros, rejeição de linhas de teste e integridade dos arquivos. As fixtures ficam
exclusivamente em diretórios temporários dos testes.

A conferência do snapshot real reconcilia os 2.153.941 participantes e a média
495,774199 com a EDA existente. As demais verificações e as limitações da sessão
estão em `docs/validacao-frontend.md`. O painel não completa as etapas científicas
pendentes: buscas, seleção final e avaliação do teste continuam no andamento do estudo.

## Banco SQLite local

Quando `dados/database/enem2023-v1/enem2023.sqlite3` existe, o frontend carrega
automaticamente as tabelas agregadas desse banco e informa a fonte na barra lateral.
São consultas somente leitura, sem acesso às linhas individuais pelo painel. O cache
confere tamanho, data de alteração e manifesto; uma nova carga valida o SHA-256.
Para selecionar outro banco, defina `ENEM_DATABASE` com o caminho absoluto.
As variáveis explícitas `ENEM_DASHBOARD_DIR` e `ENEM_RELATIONS_DIR` permitem usar
os snapshots em arquivos quando `ENEM_DATABASE` não está definido.

O banco nacional preserva todos os 3.933.955 participantes em 76 colunas. As relações
e os gráficos usam exclusivamente desenvolvimento. Estrutura, comandos e exemplos
de consulta estão em `dados/database/README.md`; as evidências atuais e o relatório
estão descritos em `docs/relacoes_e_relatorio.md`.
