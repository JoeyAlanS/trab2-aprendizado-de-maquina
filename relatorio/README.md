# Fontes LaTeX para Overleaf

O pacote `output/overleaf-enem2023.zip` contém os TEX, todas as figuras e este guia.
Não depende dos microdados, do Python nem de caminhos pessoais para compilar.

## Importar

1. Criar projeto no Overleaf usando **Existing project (.zip)**.
2. Enviar o ZIP e selecionar **XeLaTeX** como compilador.
3. Selecionar o documento principal:

| Fonte | Conteúdo | PDF da entrega |
|---|---|---|
| `main.tex` ou `slides_pitch.tex` | 20 slides; cerca de 12 minutos; Joey 1-10, Paulo 11-20 | `docs/pitch.pdf` |
| `slides_acompanhamento.tex` | 7 slides; retrospectiva do desenvolvimento, sem métricas de teste | `docs/acompanhamento.pdf` |
| `artigo.tex` | Artigo científico revisado, 10 páginas | `docs/artigo.pdf` |
| `pitch.tex` | Roteiro oral detalhado, sem slides | `output/pdf/pitch.pdf` |
| `acompanhamento.tex` | Texto de andamento e conferência | `output/pdf/acompanhamento.pdf` |

O tema compartilhado dos slides está em `slides_tema.tex`. Figuras ficam em
`figuras/`; não renomear ou remover sem atualizar os TEX. Os arquivos usam pacotes
LaTeX comuns e fontes portáteis. A compilação local usa Tectonic (motor XeTeX).
A importação dentro de uma conta Overleaf não foi executada.

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

Os TEX dos slides podem ser editados diretamente. O gerador legado
`scripts/publicar_latex.py` produz apenas os textos corridos e redefine `main.tex`
para o roteiro oral quando executado sem `--article-only`: não é necessário
executá-lo para compilar os slides desta entrega.
Preservar alterações feitas no Overleaf antes de regenerar qualquer fonte.
