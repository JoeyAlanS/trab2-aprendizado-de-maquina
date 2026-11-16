# Fontes LaTeX para Overleaf

O pacote `output/overleaf-enem2023.zip` contém os TEX, todas as figuras e este guia.
Não depende dos microdados, do Python nem de caminhos pessoais para compilar.

## Importar

1. Criar projeto no Overleaf usando **Existing project (.zip)**.
2. Enviar o ZIP e selecionar **XeLaTeX** como compilador.
3. Selecionar o documento principal:

| Fonte | Conteúdo | PDF da entrega |
|---|---|---|
| `main.tex` ou `slides_pitch.tex` | 23 slides; meta de 13 minutos; Joey 1-10, Paulo 11-23 | `docs/pitch.pdf` |
| `slides_acompanhamento.tex` | 7 slides; retrospectiva do desenvolvimento, sem métricas de teste | `docs/acompanhamento.pdf` |
| `artigo.tex` | Artigo científico revisado, 10 páginas | `docs/artigo.pdf` |
| `acompanhamento.tex` | Texto de andamento e conferência | `output/pdf/acompanhamento.pdf` |

O tema compartilhado dos slides está em `slides_tema.tex`. Figuras ficam em
`figuras/`; não renomear ou remover sem atualizar os TEX. Os arquivos usam pacotes
LaTeX comuns e fontes portáteis. A compilação local usa Tectonic (motor XeTeX).
A importação dentro de uma conta Overleaf não foi executada.

O pitch em LaTeX segue a sequência temática dos 23 slides finais do
Canva, incluindo Linear, Ridge e Árvore nos slides 8, 9 e 10. O PDF em LaTeX tem
design próprio e usa os gráficos originais do projeto; não é uma exportação do Canva.
O enunciado prevê 10 a 15 minutos. A meta de ensaio é 13 minutos, divididos em
6min30 para cada autor.

Os slides de acompanhamento são uma **retrospectiva preparada agora**; não comprovam
que uma apresentação ou submissão ocorreu no passado. Apresentam apenas informações
e resultados do desenvolvimento, com os experimentos seguintes identificados como
posteriormente realizados. O pitch inclui os resultados finais reais.

## Compilar e empacotar localmente

Na raiz do repositório, com o executável Tectonic disponível:

```bash
.venv/bin/python scripts/compilar_slides.py --tectonic tectonic
```

Isso gera `output/pdf/slides_pitch.pdf` e `slides_acompanhamento.pdf`, publica cópias
em `docs/` e atualiza o ZIP independente. Logs e auxiliares ficam em `tmp/`, ignorada
pelo Git. Revisar as páginas renderizadas depois de alterações de diagramação.

Para regenerar e compilar somente o artigo, publicando a versão revisada em
`docs/artigo.pdf` e `output/pdf/artigo_latex.pdf`:

```bash
.venv/bin/python scripts/publicar_latex.py --article-only
.venv/bin/python scripts/compilar_latex.py --documents artigo --tectonic tectonic
```

O artigo revisado mantém as métricas e as figuras dos experimentos originais e
explicita o catálogo completo e a separação entre seleção e teste. A versão histórica
permanece em `output/pdf/artigo_ciencias_natureza.pdf`. Os PDFs das duas versões
não têm identidade binária. O ZIP contém a fonte LaTeX revisada.

Os TEX dos slides podem ser editados diretamente. O gerador
`scripts/publicar_latex.py` produz os textos do artigo e do acompanhamento,
preservando os slides e o documento principal `main.tex`. Não é necessário
executá-lo para compilar os slides desta entrega.
Preservar alterações feitas no Overleaf antes de regenerar qualquer fonte.
