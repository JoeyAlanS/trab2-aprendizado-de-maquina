# Checkpoint 6 - Artigo científico e incorporação dos originais

Concluído e validado em **07/11/2026**. Autores: **Joey Alan de Freitas Solis** e
**Paulo Henrico**. Afiliação: **Universidade de Fortaleza (Unifor)**. Professor: **Tulio**,
conforme informado pelo usuário, sem acrescentar sobrenome ou curso não fornecidos.

## Entregáveis

- [Artigo em PDF, dez páginas](../output/pdf/artigo_ciencias_natureza.pdf), com cópia idêntica em [docs/artigo.pdf](artigo.pdf).
- [Artigo em Markdown, com tabelas e figuras](artigo.md).
- [Fonte editável da diagramação](artigo-fonte.md): texto com diretivas que vinculam figuras e tabelas reais; não é o arquivo de entrega.
- [Figuras do artigo](../resultados/ciencias_natureza/checkpoint-6-2026-11-07/figuras/): sete PNG a 300 dpi e sete SVG, adaptados para a largura da página.
- [Pacote de entrega do checkpoint](../output/checkpoint-6-artigo-2026-11-07.zip), sem microdados individuais, modelos ajustados ou arquivos de fontes proprietárias.
- [Validação documental](../resultados/ciencias_natureza/checkpoint-6-2026-11-07/validacao_artigo.json) e [revisão visual](../resultados/ciencias_natureza/checkpoint-6-2026-11-07/validacao_visual.json).

O PDF contém resumo, introdução, objetivos, fundamentação dos sete algoritmos,
metodologia, configurações, resultados, discussão, conclusão, trabalhos futuros e
oito referências. Inclui sete figuras, três tabelas e um quadro de configurações.
As tabelas são compostas diretamente dos CSVs persistidos. O texto distingue a
seleção entre os sete algoritmos do ranking do catálogo ampliado.

## Originais recebidos e base validada

Os dois ZIPs foram **movidos**, não apenas copiados, de Downloads para `dados/raw/`.
Os caminhos anteriores deixaram de conter esses arquivos. Todos os membros passaram
por CRC; foram extraídos 17 arquivos úteis, com proteção contra caminhos inseguros.

| Fonte local | Tamanho | SHA-256 |
|---|---:|---|
| `dados/raw/microdados_enem_2023.zip` | 549.511.687 bytes | `19512b7e29c9c8e940554396969722081341caa275c245a6c9d2d559c5d13a0a` |
| `dados/raw/MICRODADOS_ENEM_2023.csv` | 1.777.162.429 bytes | `c8b1fae0a97b6ac826d950d16696efa3d89c133b0165128aadd2997c2315b666` |
| `dados/raw/competencias_redacao_enem_2023.zip` | 377.423.159 bytes | `db3118c5908645a92d95e81a02b8474c561daf852602abf459d8952becf40a34` |

Os hashes nacionais coincidem com a coleta histórica. A verificação percorreu
**todas as 3.933.955 linhas e 76 colunas**, aplicando a mesma normalização da ingestão
e comparando cada célula com os **79 Parquets** existentes. Resultado: igualdade
integral, 2.692.427 notas CN observadas, 1.241.528 ausentes e 16.547 zeros.
A base preparada corresponde à fonte recebida. Não houve mudança de participantes,
IDs, partições, métricas ou receitas; não foi necessário reingerir ou treinar novamente.

O complemento tem CSV de 37 colunas com competências e resultados de redação por
avaliador. Foi extraído com sua documentação em
`dados/raw/complementos/COMPETENCIAS_REDACAO_2023/`, mas **não foi unido aos preditores**:
essas variáveis são excluídas pelo recorte de estimativa de CN a partir do perfil.
O dicionário e os documentos nacionais estão em `dados/raw/documentacao_enem2023/`.
Provas/gabaritos continuam no ZIP e não integram as entradas da modelagem.

[Registro da incorporação](../resultados/ciencias_natureza/checkpoint-6-2026-11-07/incorporacao_fontes.json)
e [comparação integral](../resultados/ciencias_natureza/checkpoint-6-2026-11-07/validacao_csv_parquets.json).
Os hashes comprovam identidade com a coleta histórica local; não se alega assinatura
oficial do Inep. Arquivos grandes seguem ignorados pelo Git. Os restos anteriores
`.zip.part` e trava foram preservados e não foram utilizados.

## Resultados efetivamente incorporados

| Modelo no teste | RMSE | MAE | R² |
|---|---:|---:|---:|
| Stacking | 76,189590 | 55,325018 | 0,249711 |
| Linear de referência | 76,516794 | 55,615726 | 0,243253 |
| SVM linear | 76,622171 | 55,537602 | 0,241167 |
| Random Forest | 76,657930 | 55,820771 | 0,240459 |
| Média do treino | 87,959294 | 66,285019 | -0,000002 |

Esses resultados já haviam sido obtidos no Checkpoint 4, para os mesmos 538.486
participantes. O artigo não apresenta uma nova avaliação. A redução de RMSE do
Stacking frente à média é 13,38%; a vantagem frente à linear é pequena. As buscas
têm ganhos mínimos, sem demonstração de significância. Engenharia, seleção, PCA,
ponderação e as duas ablações foram incluídas com os resultados favoráveis e
negativos. As curvas mostram pequenos afastamentos treino/validação; isso não
prova ausência de vieses ou generalização fora de 2023. Erros por faixa e escola
expõem a maior dificuldade nos extremos das notas.

## Formatação e validação

Foi utilizado o [Guia de normalização da Unifor, edição 2025](https://unifor.br/documents/d/guest/guia-de-normalizacao),
consultado em 07/11/2026. O guia orienta ABNT, citações autor-data e referências.
O artigo tem A4, Times New Roman incorporada, corpo de 12 pontos, entrelinha 18
pontos (1,5), recuo inicial de 1,25 cm, corpo justificado, títulos numerados,
legendas/fontes de 10 pontos e referências à esquerda. Resumo e referências têm
espaçamento simples. A paginação está no alto à direita.

As margens seguem literalmente o guia institucional, p. 14-15: **superior/direita
3 cm; esquerda/inferior 2 cm**. Esse detalhe é registrado porque a disposição difere
da orientação ABNT genérica frequentemente reproduzida. O limite de dez páginas
inclui todas as figuras, tabelas e referências, sem capa separada. Não foi fornecido
um modelo específico adicional do professor. A versão da documentação técnica citada
é a 1.9.1, lançada em setembro de 2026, segundo o
[registro oficial](https://scikit-learn.org/stable/whats_new/v1.9.html).

Foram aprovadas as seguintes conferências:

- Dez páginas no PDF; cópias de saída idênticas; sete figuras e três tabelas presentes.
- Métricas do artigo conferidas contra os CSVs reais e ausência de diretivas não resolvidas no PDF.
- 259 hashes de entradas, código numérico, artefatos e relatórios conferidos; preservação dos checkpoints anteriores.
- Todos os caracteres textuais usam Times New Roman; limites de página/margens conferidos.
- PNGs a 300 dpi; tabelas, legendas, eixos, fontes, acentuação e paginação inspecionados nas dez páginas renderizadas.
- Ruff aprovado nos cinco scripts novos, sem criar arquivos de testes nem repetir treinamentos.

O Markdown anterior foi preservado em `historico/2026-11-07/pre-checkpoint6/artigo.md`.
Os relatos de ausência dos originais nos checkpoints antigos permanecem como registros
históricos. As páginas de acompanhamento atuais foram atualizadas para o estado resolvido.
As versões LaTeX/PDF preliminares também foram preservadas e identificadas como anteriores.

## Reprodução da publicação

A geração de figuras usa o ambiente numérico já existente; a composição/validação
usa ReportLab, pypdf e pdfplumber do runtime de documentos, sem modificar `uv.lock`.
É possível usar um ambiente de publicação separado com essas dependências.

```bash
# Na raiz do repositório, com fontes Times New Roman em tmp/fonts/:
.venv/bin/python scripts/figuras_checkpoint6.py

# Executar estes dois comandos em um Python com reportlab, pypdf, pdfplumber e Pillow:
python scripts/publicar_checkpoint6.py --font-dir tmp/fonts
python scripts/validar_checkpoint6.py

# Conferência visual obrigatória após qualquer edição:
pdftoppm -scale-to 1100 -png output/pdf/artigo_ciencias_natureza.pdf tmp/pdfs/artigo-revisao
```

Os arquivos de fonte esperados são `Times.TTF`, `Timesbd.TTF`, `Timesi.TTF` e
`Timesbi.TTF`. Nesta execução foram extraídos do pacote Microsoft Core Fonts
`https://downloads.sourceforge.net/corefonts/times32.exe`, sem executar seu instalador.
Os arquivos proprietários não são distribuídos no pacote do projeto. A geração do
PDF recusa falta de fonte; não faz substituição silenciosa. O registro de ambiente
contém versões e hashes. O texto editável é `docs/artigo-fonte.md`; o publicador
atualiza `docs/artigo.md`, as duas cópias do PDF e a evidência de diagramação.
Revisões posteriores exigem nova conferência e atualização do encerramento do checkpoint.

Para repetir a validação integral dos dados, usar `scripts/validar_fontes_2023.py`
com outro caminho de saída, preservando a evidência aprovada. A movimentação já foi
concluída; não repetir `incorporar_fontes_2023.py` sobre os destinos existentes.

## Próximo checkpoint

O **Checkpoint 7 não foi iniciado**. Faltam os PDFs de acompanhamento e pitch,
a distribuição das falas e o ensaio da apresentação. Prazos e submissão no AVA
continuam dependentes da equipe. O artigo do Checkpoint 6 está pronto nesta cópia local.
