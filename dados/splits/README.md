# Desenvolvimento, teste e dobras

`ciencias-natureza-v1/particoes.parquet` persiste `NU_INSCRICAO`, `partition` e
`validation_fold`. `manifesto.json` registra alvo, fonte, semente e hashes.
São 2.692.427 participantes com `NU_NOTA_CN` observada:

| Partição | Participantes | Uso |
|---|---:|---|
| development | 2.153.941 | exploração, comparação e escolhas |
| test | 538.486 | avaliação final após congelar a solução |

Divisão aleatória 80/20, semente 42. O desenvolvimento possui três dobras:
0 (717.981), 1 (717.980), 2 (717.980). Na rodada k, treinar nas outras duas e
validar em k. O teste não pertence a nenhuma dobra. O ID é controle, nunca entrada.

Em uma instalação nova, depois de preparar os dados:

```bash
.venv/bin/python -m enem_base split --study configs/ciencias_natureza.toml
```

A função `save_splits` em `src/enem_base/splits.py` salva os IDs e verifica a fonte.
Não recriar partições entre modelos. O SHA-256 da serialização local atual é
`02b7f7a866e6a8ad40dd82711007b883bd4f5a6898d5cd84b9602059e9667873`.
A recuperação local preservou todos os IDs e dobras originais; outra serialização
pode ter hash diferente, que exige conferir a igualdade dos participantes.

O teste **já foi avaliado**. `avaliacao_final.json` registra a trava de avaliação.
Não apagá-la para testar novas escolhas na mesma partição. Os arquivos individuais
são grandes e ignorados pelo Git; obter a fonte e usar o comando acima os regenera.
