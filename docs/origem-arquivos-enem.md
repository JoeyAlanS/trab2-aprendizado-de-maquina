# Originais do ENEM 2023 incorporados

Em 07/11/2026 os dois ZIPs fornecidos pelo usuário em Downloads foram movidos para
`dados/raw/`, validados por CRC e preservados. A pendência dos originais foi resolvida.

| Arquivo | Conteúdo e uso |
|---|---|
| `dados/raw/microdados_enem_2023.zip` | Pacote nacional: CSV, dicionário, documentação, provas e gabaritos |
| `dados/raw/MICRODADOS_ENEM_2023.csv` | Tabela de 3.933.955 registros e 76 colunas; fonte da regressão de Ciências da Natureza |
| `dados/raw/competencias_redacao_enem_2023.zip` | Notas por competência e avaliador; complemento preservado, excluído dos preditores |

O ZIP nacional tem 549.511.687 bytes e SHA-256
`19512b7e29c9c8e940554396969722081341caa275c245a6c9d2d559c5d13a0a`.
O CSV tem 1.777.162.429 bytes e SHA-256
`c8b1fae0a97b6ac826d950d16696efa3d89c133b0165128aadd2997c2315b666`.
Ambos coincidem com o [manifesto histórico](referencias/fonte_enem2023.json).
Isso confirma identidade com a coleta anterior, sem alegar checksum oficial assinado.

O complemento tem 377.423.159 bytes e SHA-256
`db3118c5908645a92d95e81a02b8474c561daf852602abf459d8952becf40a34`.
Seu CSV, dicionário e documentação estão em
`dados/raw/complementos/COMPETENCIAS_REDACAO_2023/`.
Suas 37 colunas incluem identificadores e resultados da redação. Como o projeto
prevê CN por perfil, as notas de redação e suas competências não entram na modelagem.

A conferência integral normalizou todas as linhas e colunas do CSV principal e
comparou os valores com os 79 Parquets usados no estudo: **igualdade aprovada**.
Foram confirmados 2.692.427 alvos observados, 1.241.528 ausentes e 16.547 zeros.
Dados preparados, partições e resultados científicos permaneceram preservados.
Não foi necessário treinar novamente nem reavaliar o teste.

O [registro de incorporação](../resultados/ciencias_natureza/checkpoint-6-2026-11-07/incorporacao_fontes.json)
e a [validação integral](../resultados/ciencias_natureza/checkpoint-6-2026-11-07/validacao_csv_parquets.json)
permitem auditar a conclusão. Os relatórios anteriores descrevem corretamente o estado
histórico em que os originais estavam ausentes; não foram alterados retroativamente.

O [CSV de previsões](../resultados/ciencias_natureza/checkpoint-4-2026-11-07/avaliacao_final/previsoes_teste.csv)
é uma saída diferente: contém previsões dos cinco modelos para 538.486 participantes.
O ZIP do Checkpoint 5 contém figuras e tabelas, e também não é o ZIP de microdados.
Os arquivos individuais e bancos grandes continuam fora do Git.
