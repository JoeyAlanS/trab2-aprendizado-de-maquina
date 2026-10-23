# Banco de dados local do projeto

O banco SQLite fica em `enem2023-v1/enem2023.sqlite3`, dentro deste projeto.
Contém toda a base limpa nacional de 3.933.955 participantes e 76 colunas,
as partições e os resultados agregados já executados. Não são dados fictícios.

O arquivo binário é grande e está fora do Git. O manifesto e `schema.sql` acompanham
o banco. Não há senha ou serviço separado: SQLite faz parte da biblioteca padrão
do Python. O frontend o utiliza automaticamente quando presente. Para escolher
outro banco, defina `ENEM_DATABASE` com o caminho absoluto do arquivo SQLite.

## Geração a partir dos artefatos deste projeto

```powershell
.\.venv\Scripts\python.exe -m enem_base --verbose database --study configs/ciencias_natureza.toml --output dados/database/enem2023-v1 --dashboard resultados/ciencias_natureza/dashboard-v1 --relations resultados/ciencias_natureza/relacoes-v1
```

A fonte Parquet, os hashes e as partições são conferidos. A cópia é feita em lotes
sem concatenar a base inteira em memória. A saída é publicada apenas após validar
contagens, chave estrangeira, integridade SQLite e hash final. Uma versão existente
não é sobrescrita; escolha `enem2023-v2` para outra execução.

## Consultar sem modificar os dados

Exemplo em Python, a partir da raiz do projeto:

```python
from pathlib import Path
from enem_base.database import readonly_connection

path = Path("dados/database/enem2023-v1/enem2023.sqlite3")
with readonly_connection(path) as connection:
    print(connection.execute("SELECT * FROM contagens_particoes").fetchall())
    print(
        connection.execute(
            "SELECT variable, label, n, mean FROM perfis WHERE variable=?", ("Q006",)
        ).fetchall()
    )
```

`participantes` preserva todas as linhas limpas. `particoes` contém somente quem
tem alvo observado. A view `desenvolvimento` inclui as entradas aprovadas, o alvo
CN e a dobra para indivíduos do desenvolvimento. O teste é armazenado para manter
o conjunto completo, mas continua reservado e sem avaliação. As consultas do
frontend leem exclusivamente resultados agregados, nunca a tabela de indivíduos.
Não utilizar o banco para explorar o teste antes de congelar o modelo final.

Tabelas de análise: `agregados_desenvolvimento`, `resumo_cv`, `dobras_cv`,
`relacoes_alvo`, `associacoes_entradas`, `perfis` e `cruzamentos`. `dicionario`
documenta as 76 colunas e `metadados` registra fonte, protocolo e resultados.
