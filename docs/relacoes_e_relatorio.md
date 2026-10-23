# Relações e relatório técnico — 23/10/2026

O frontend está disponível em `http://127.0.0.1:8501`. A quinta página,
**Relações e relatório**, reúne a análise sistemática e o download do PDF.
O relatório técnico tem dez páginas em A4, produzido de fonte LaTeX editável.

## Escopo executado

Foram utilizados todos os **2.153.941 participantes do desenvolvimento**, com
proveniência conferida por `study.load_development`. O teste de 538.486 permanece
reservado. Nenhuma família de modelos adicional foi treinada nesta continuação.

| Evidência gerada | Cobertura |
|---|---:|
| Entradas em relação à nota CN | 40 |
| Pares de entradas | 780, sem repetição e sem diagonal |
| Pares categóricos / pares mistos | 741 / 39 |
| Perfis de categorias/quantidades | 254 |
| Células não vazias nos cruzamentos | 29.709 |

“Todas as relações” foi operacionalizado como todos os efeitos univariados e pares
das entradas já aprovadas no contrato. Não significa enumerar todas as interações
de três ou mais variáveis ou identificar efeitos causais.

## Métodos e interpretação

- Nota CN por perfil: contagem, média, desvio amostral e zeros. Eta² é a soma de
  quadrados entre médias de grupos dividida pela variação total da nota.
- Q005 por nota CN: Pearson e Spearman nas quantidades originais, sem atribuir
  números arbitrários às outras categorias. Eta² também descreve seus grupos discretos.
- Duas entradas categóricas: V de Cramér, calculado a partir do qui-quadrado de
  Pearson, sem correção de continuidade. É uma medida sem direção, de zero a um.
- Entrada numérica por categórica: Eta² da quantidade de moradores entre grupos.
  O resultado não se refere à nota CN e fica separado de V no painel.
- Os efeitos principais excluem ausências por variável/par. As contagens observadas
  são explícitas. Grupos ausentes permanecem nos perfis/cruzamentos e há uma medida
  adicional com ausência como categoria para conferir sensibilidade.
- As alternativas “Não respondeu” e similares são respostas codificadas e continuam
  como categorias. Não se confundem com células nulas.
- Os gráficos usam mínimo inicial de 30 participantes por grupo/célula. Esse mínimo
  é ajustável e não remove registros dos resultados ou das tabelas de exportação.

Não foram calculados valores-p nem alegada significância a partir das centenas de
comparações. As medidas descrevem este desenvolvimento; Eta² não é R² preditivo,
e os efeitos univariados não devem ser somados. Categoria, cobertura e confundimento
precisam ser considerados ao comparar os efeitos.

## Resultados que merecem leitura

Renda familiar tem Eta²=0,142975; computadores, 0,125902; escolaridade do pai,
0,087731; escolaridade da mãe, 0,080041. Essas entradas têm cobertura integral.
A dependência administrativa chega a 0,172200 entre 579.550 observados, mas tem
73,09% de ausência: seu valor não deve ser apresentado como superioridade global.
As médias dos extremos de renda são 452,98 (nenhuma renda) e 577,34 (acima de
R$ 26.400 em valores do questionário de 2023). São diferenças brutas, não efeitos
de aumentar renda. Os resultados completos estão nas tabelas e no PDF.

O par conclusão do ensino médio × treineiro apresenta V=1 nos observados, refletindo
uma relação determinística entre categorias deste conjunto. O código e a medida
foram conferidos por testes independentes; não se interpreta isso como causalidade.

## Arquivos e reprodução

`resultados/ciencias_natureza/relacoes-v1/` contém:

- `alvo.csv`: as 40 entradas, Eta², correlações numéricas, observados e ausências;
- `pares.csv`: os 780 pares, método, efeito, cobertura e sensibilidade a ausências;
- `perfis.parquet`: estatísticas de todas as alternativas de cada entrada;
- `cruzamentos.parquet`: células de todos os pares, sem indivíduos ou identificadores;
- `manifesto.json`: hashes dos ativos e da fonte, contrato, partições e dicionário.

O painel valida os hashes e a compatibilidade com o snapshot anterior. O cache é
limitado e leva em conta alterações nos ativos. Para uma nova execução, use outro
nome de saída; não se sobrescreve o resultado científico existente.

```powershell
.\.venv\Scripts\python.exe -m enem_base --verbose relations --study configs/ciencias_natureza.toml --output resultados/ciencias_natureza/relacoes-v2
$env:ENEM_RELATIONS_DIR = (Resolve-Path 'resultados/ciencias_natureza/relacoes-v2').Path
.\.venv\Scripts\python.exe -m streamlit run app/app.py
```

O PDF final fica em `output/pdf/relatorio_ciencias_natureza.pdf`. Fonte, imagens e
tabelas ficam em `relatorio/`. `scripts/gerar_relatorio.py` regenera as figuras e
tabelas dos snapshots verificados, preservando a narrativa em `main.tex`.
Para compilar com o Tectonic já disponível nesta sessão:

```powershell
.\scripts\compilar_relatorio.ps1
```

Em outro computador, pode-se abrir `relatorio/` no editor LaTeX do Codex ou instalar
Tectonic pelo [projeto oficial](https://github.com/tectonic-typesetting/tectonic).
O executável portátil utilizado é 0.17.0, obtido da distribuição oficial de Windows
e mantido em `tmp/tools/`, fora do versionamento. Não foi instalado globalmente.
O arquivo ZIP de fontes na pasta de saída permite transportar o projeto LaTeX.

## Banco de dados no projeto existente

O banco físico `dados/database/enem2023-v1/enem2023.sqlite3` contém todos os
3.933.955 registros e as 76 colunas da base tratada, com 2.237.792.256 bytes
(aproximadamente 2,24 GB). Não é uma amostra. Os valores nulos e as notas zero
continuam distintos. `manifesto.json` registra a origem, os hashes, as contagens
e a validação de integridade; `schema.sql` documenta tabelas, índices e views.

Além de `participantes`, o banco contém as partições persistidas, o dicionário e
as tabelas agregadas de desenvolvimento, CV e relações. A view `desenvolvimento`
restringe as entradas ao contrato do estudo e filtra a partição de desenvolvimento.
O teste continua identificado e reservado; sua presença no armazenamento não
constitui avaliação. O guia de consultas e reprodução está em `dados/database/README.md`.

O frontend seleciona esse banco automaticamente quando ele existe e consulta
somente os agregados, com conexão em modo leitura. `ENEM_DATABASE` permite indicar
outra versão explicitamente. O relatório inclui o banco na descrição da arquitetura
e nas instruções de reprodução. A base binária fica fora do Git pelo seu tamanho;
ela está disponível localmente no caminho acima.

## Verificação

`scripts/verificar.ps1`: **80 testes aprovados em 37,00 s**, lint e formatação
aprovados, dependências consistentes. Os novos casos conferem V contra SciPy,
simetria/reordenação, constantes/margens vazias, Eta² contra somas de quadrados,
todos os pares, orientação dos cruzamentos, integridade/proveniência e as quatro
opções da nova página no AppTest. Também verificam a publicação do SQLite, preservação
de nulos e zeros, bloqueio de escrita, rejeição de hash alterado e seleção do banco
pela interface. As fixtures fictícias só existem nos testes.

A geração nacional confere que cada um dos 40 perfis e dos 780 cruzamentos soma
2.153.941 participantes. Os ativos são verificados por hash antes da apresentação.
O frontend foi reiniciado após adicionar novos módulos para evitar importar funções
antigas mantidas em memória. A verificação visual atual complementa o histórico de
21/10, quando não havia navegador disponível. Nesta execução, o AppTest também
percorreu as cinco páginas e as quatro opções de relações usando o SQLite nacional.
O navegador confirmou a identificação do banco e os controles de cruzamentos,
matriz e relatório. Os downloads reais do PDF e do ZIP foram conferidos contra os
artefatos locais, incluindo as contagens das quatro tabelas exportadas. Evidências:
`resultados/ciencias_natureza/evidencias/frontend_sqlite_verificacao.json`,
`frontend_downloads_verificacao.json` e `frontend_sqlite.png` no mesmo diretório.

O PDF foi compilado com Tectonic, renderizado com Poppler e revisado nas dez páginas.
Foram corrigidos a quebra excedente da página demográfica, rótulos escolares próximos
e números sobrepostos na matriz. Os gráficos usam dados agregados completos.

## Limites da entrega

O documento explica o que já foi executado e registra as pendências do enunciado.
Não é o artigo final com todas as etapas de modelagem exigidas. Autores e GitHub
continuam não informados; não foram inventados. A exploração ampliada não substitui
PCA, buscas, curva de aprendizagem, análise de resíduos ou avaliação final do teste.

Referências primárias dos métodos: [Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html),
[Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html)
e [V de Cramér](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.contingency.association.html),
além do [Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
