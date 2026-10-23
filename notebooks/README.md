# Exploração e experimentos

Para o tema definido, `01_ciencias_natureza.py` lê os relatórios agregados da exploração
e da comparação inicial, conferindo o estado concluído e a reserva do teste. Não lê
dados individuais nem executa nova avaliação. O código de pesquisa está no pacote;
esse roteiro serve para percorrer os resultados e sua interpretação.

`00_qualidade_exemplo.py` usa células `# %%`, executáveis como script ou em editor
compatível. Ele lê somente saídas fictícias, sem treinar regressores nem escolher alvo.
As dependências do pipeline não incluem Jupyter; se a equipe optar por `.ipynb`,
registrar essa dependência e remover saídas com dados individuais antes de publicar.

`01_roteiro_analise.md` orienta a exploração posterior do desenvolvimento. Colocar
lógica reutilizável em `src/enem_base/`, com configuração e testes. Notebooks devem
narrar hipóteses, execução e interpretação; não devem ser a única forma de reproduzir.
