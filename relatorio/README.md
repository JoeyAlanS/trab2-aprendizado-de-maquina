# Entrega LaTeX para Overleaf

O pacote `output/overleaf-enem2023.zip` contém fontes independentes, figuras e este guia.
O roteiro do pitch é um documento de texto; não utiliza Beamer nem cria slides.

## Importar e compilar

1. No Overleaf, criar um projeto a partir de **Existing project (.zip)** e enviar o ZIP.
2. Selecionar **XeLaTeX** como compilador. Não é necessário executar Python no Overleaf.
3. Escolher o documento principal:
   - `main.tex` ou `pitch.tex`: roteiro oral, falas dos autores e perguntas/respostas;
   - `artigo.tex`: artigo científico, com dez páginas incluindo as referências;
   - `acompanhamento.tex`: andamento e auditoria das execuções.
4. Compilar e baixar o PDF. Os TEX e a pasta `figuras/` ficam na raiz do projeto.

As fontes foram compiladas localmente com **Tectonic 0.17.0**, que usa o motor XeTeX.
A importação/compilação dentro de uma conta Overleaf não foi executada. A conferência
local inclui uma compilação do `main.tex` extraído do ZIP, sem depender da árvore do repositório.

As fontes usam somente pacotes LaTeX comuns, codificação UTF-8 e a família Times
portável de `mathptmx`. Isso evita depender dos arquivos proprietários Times New Roman
que foram usados no PDF histórico do Checkpoint 6. Corpo de 12 pontos e margens seguem
o guia institucional utilizado; detalhes de formatação estão nos preâmbulos.

## Editar

É possível editar diretamente `pitch.tex`, `artigo.tex` e `acompanhamento.tex` no Overleaf.
O arquivo `main.tex` apenas seleciona o pitch. A compilação não modifica os TEX.
Os textos de trabalho estão em `docs/pitch.md`, `docs/acompanhamento.md` e
`docs/artigo-fonte.md`. O artigo LaTeX resume um parágrafo de resíduos para ajustar
sua diagramação; os resultados científicos são os mesmos da versão do Checkpoint 6.

Para regenerar os TEX a partir desses textos, executar explicitamente:

```bash
.venv/bin/python scripts/publicar_latex.py
```

Esse comando sobrescreve os TEX gerados. Portanto, preservar alterações feitas
diretamente no Overleaf antes de usá-lo. Para apenas compilar as fontes presentes:

```bash
.venv/bin/python scripts/compilar_latex.py --tectonic /caminho/para/tectonic
```

Saídas: `output/pdf/pitch.pdf`, `output/pdf/artigo_latex.pdf` e
`output/pdf/acompanhamento.pdf`. Auxiliares e logs ficam em `tmp/latex-build/`, fora do Git.
Para reconstruir o ZIP, compactar o conteúdo desta pasta com os TEX na raiz,
incluindo `figuras/` e este README, sem logs nem arquivos auxiliares.

## Evidências

A revisão científica está em `resultados/ciencias_natureza/checkpoint-7-2026-11-07/`:
`auditoria_experimentos.json`, `cobertura_execucoes.csv`, `validacao_buscas.json` e
`validacao_teste.json`. A suíte existente de software teve 81 testes aprovados,
registrados em `pytest.xml`. Testes unitários não substituem avaliações nacionais.

O teste reservado inclui Stacking, SVM linear, Random Forest, média e linear.
Os demais algoritmos possuem validação cruzada completa, mas não foram aplicados
ao teste final. As curvas finais reutilizam cálculos compatíveis, conforme registro
individual; não devem ser contadas como 45 treinamentos inteiramente novos.

Guia de importação: https://docs.overleaf.com/managing-projects-and-files/uploading-a-project
Repositório: https://github.com/JoeyAlanS/trab2-aprendizado-de-maquina
