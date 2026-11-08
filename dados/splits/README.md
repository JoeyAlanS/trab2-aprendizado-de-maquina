# Partições persistidas

Em 05/11/2026, os IDs foram recuperados do SQLite original e confrontados integralmente
com a divisão por semente 42. A serialização Parquet tem novo hash, mas todos os participantes
e dobras coincidem com o banco. O manifesto atual guarda o hash anterior e o atual,
com `partition_membership_verified=true`. Não houve nova escolha de participantes.

As partições oficiais de Ciências da Natureza foram criadas em 21/10/2026, em
`ciencias-natureza-v1/`: 2.153.941 participantes de desenvolvimento e 538.486 de teste.
Alvo: NU_NOTA_CN. O teste ainda não foi avaliado. `splits.save_splits` recebe uma tabela
apenas com identificador e alvo e exige o SHA-256 da fonte.

O resultado contém `particoes.parquet` e `manifesto.json` com alvo, fonte, hash das
partições e contagens. `partition` é development ou test. `validation_fold` é 0,1,2
para desenvolvimento e nulo para teste. Na dobra k, usar os outros valores para
treinar e k para validar. Não adicionar outra parcela fixa de validação.

Não incluir o identificador em X. Não regenerar partições entre modelos. São locais
e ignoradas por padrão; após a definição do alvo, planejar a entrega dos IDs/hashes
exigidos pelo documento e conferir o conteúdo antes da publicação.
