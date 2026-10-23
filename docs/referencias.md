# Fontes e referências técnicas

Consultas da base: **16/10/2026**. Continuação do estudo e obtenção dos microdados:
**21/10/2026**. As referências sustentam requisitos, implementação e interpretação;
os resultados executados são registrados separadamente no relatório de andamento.

1. **Enunciado fornecido pelo usuário.** Projeto 2 - Aprendizado de Máquina com Dados
   do ENEM. 16 páginas. Cópia preservada em `referencias/enunciado-projeto2.pdf`; identidade
   em `referencias/enunciado.sha256`. Fonte da matriz de requisitos, dos tamanhos esperados
   e do protocolo. Autoria/data editorial não foram inferidas.
2. **Inep. Microdados do ENEM.** [Página oficial de obtenção](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
   A seção 2023 lista o pacote principal. Obtido em 21/10/2026; hashes e arquivos em
   `referencias/fonte_enem2023.json`. Dicionário conferido: cópia
   `referencias/dicionario-enem2023.xlsx`, aba MICRODADOS_ENEM_2023; extrato com
   as 76 variáveis em `referencias/dicionario_enem2023.json`.
3. **pandas. `read_csv`.** [Documentação oficial](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html).
   Usada em `ingestion.py`: leitura em lotes, dtype, ausência e codificação explícitos.
   A validação de largura por `csv.reader` complementa o comportamento do leitor.
4. **scikit-learn. Common pitfalls and recommended practices.**
   [Documentação oficial sobre vazamento e Pipeline](https://scikit-learn.org/stable/common_pitfalls.html).
   Usada na fábrica de pré-processamento e no protocolo: separar teste e ajustar
   transformações somente no treino, inclusive dentro da validação cruzada.
5. **scikit-learn. `Pipeline`.**
   [Referência oficial](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html).
   Complemento para incorporar a fábrica às etapas futuras.
6. **scikit-learn. `KFold` e `train_test_split`.**
   [KFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.KFold.html)
   e [train_test_split](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html).
   Implementação das partições exigidas nas pp. 6-7 do enunciado.
7. **Biblioteca Unifor. Trabalhos acadêmicos e normalização.**
   [Guia indicado no enunciado](https://unifor.br/biblioteca/trabalhos-academicos).
   Referência a consultar na etapa de redação; o roteiro atual não certifica formatação ABNT.
8. **GitHub Actions. `checkout` e `setup-python`.**
   [checkout](https://github.com/actions/checkout) e
   [setup-python](https://github.com/actions/setup-python). Documentação dos projetos
   consultada para preparar o workflow local com as actions v7 e Python 3.13.
9. **Inep. Leia-me dos Microdados do ENEM 2023.** Documento do pacote oficial, abril de
   2024, pp. 6-9 e 12. CSV por ponto e vírgula, significado da base publicada e modelo
   de referência para citação. Cópia local em `dados/raw/Leia_Me_Enem_2023.pdf`.
10. **scikit-learn. LinearRegression e DummyRegressor.**
    [LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)
    e [DummyRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyRegressor.html).
    Consultados em 21/10/2026 para a comparação inicial na mesma validação cruzada.

As referências adicionais de métodos deverão ser inseridas no ponto de uso no artigo
e nas figuras. Verificar versão da documentação quando atualizar o lock. Os fontes
do pacote usam as bibliotecas, sem copiar implementações de terceiros.
