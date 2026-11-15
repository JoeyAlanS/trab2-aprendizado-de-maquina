# Dados preparados

`enem2023-v1/` contém 79 partes Parquet, `qualidade.json` e `manifesto.json`.
A ingestão preserva 3.933.955 linhas e 76 colunas: a ausência do alvo é contabilizada
antes de excluir participantes da modelagem supervisionada.

```bash
.venv/bin/python -m enem_base prepare --config configs/enem2023.toml
```

Executar em destino novo: não editar ou sobrescrever as partes existentes.
O código `src/enem_base/cleaning.py` normaliza ausências e tipos; `ingestion.py`
valida o contrato, grava lotes e seus hashes. As features e suas transformações são
selecionadas depois, dentro do pipeline de cada treinamento.
`resultados/colunas.csv` registra os campos criados, utilizados e excluídos de X,
e as features codificadas selecionadas em cada dobra. Campos excluídos de X
continuam preservados nos originais e na importação.

A base local foi recuperada do SQLite original e posteriormente confrontada,
célula a célula, com o CSV nacional fornecido: conteúdo normalizado idêntico.
Não se usaram dados artificiais nos experimentos nacionais. As pequenas bases
fictícias estão restritas a `tests/fixtures/`, para testes de software.

Para leitura, selecionar explicitamente `part-*.parquet`, pois a pasta também
contém metadados. Em análises nacionais, ler apenas as colunas necessárias.
Os arquivos grandes são ignorados pelo Git e regenerados pelos comandos acima.
