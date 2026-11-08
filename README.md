# Aprendizado de Máquina com Dados do ENEM

Projeto acadêmico de regressão para estimar a nota de Ciências da Natureza
(`NU_NOTA_CN`) com informações socioeconômicas, escolares e demográficas do ENEM 2023.

**Autores:** Joey Alan de Freitas Solis e Paulo Henrico  
**Instituição:** Universidade de Fortaleza (Unifor); **professor:** Tulio

## Resultados

Foram comparados SVM linear, KNN, Bagging, Pasting, Random Forest, Gradient
Boosting e Stacking em três dobras de desenvolvimento. Stacking, SVM linear e
Random Forest foram selecionados para análise final. No teste reservado, Stacking
teve RMSE 76,190 e MAE 55,325. O teste também incluiu uma referência linear e a média.
KNN, Bagging, Pasting e Gradient Boosting não foram avaliados no teste final.

| Entrega | Arquivo |
|---|---|
| Roteiro oral do pitch, sem slides | [PDF](output/pdf/pitch.pdf) |
| Acompanhamento e auditoria dos experimentos | [PDF](output/pdf/acompanhamento.pdf) |
| Artigo científico | [PDF](output/pdf/artigo_latex.pdf) |
| Fontes LaTeX e figuras para Overleaf | [ZIP](output/overleaf-enem2023.zip) |
| Instruções de importação e compilação | [Guia](relatorio/README.md) |

O ZIP foi compilado localmente, com `main.tex` como documento principal e XeLaTeX
como compilador recomendado. Não requer os microdados para compilar. A importação
em uma conta Overleaf não foi testada.

## Dados e reprodução

Os microdados originais não são incluídos no repositório. Para executar os
experimentos, obtenha os arquivos oficiais do [Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem)
e consulte os READMEs nas pastas `dados/`. Resultados individuais e modelos treinados
permanecem locais.

Ambiente Python 3.13:

```bash
uv sync --locked --extra dev
.venv/bin/python -m enem_base --help
.venv/bin/python -m pytest -q
```

Os textos-fonte que alimentam os documentos LaTeX estão em `docs/`; o código de
geração e compilação está em `scripts/publicar_latex.py` e `scripts/compilar_latex.py`.
