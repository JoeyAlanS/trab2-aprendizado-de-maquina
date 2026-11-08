# Dados originais

**Estado local em 07/11/2026:** os dois ZIPs fornecidos pelo usuário foram movidos de
`/home/joey/Downloads/` para esta pasta. Ambos passaram por CRC integral. O ZIP nacional
e seu CSV têm os mesmos SHA-256 registrados na coleta histórica de 21/10/2026.
A comparação integral do CSV normalizado com os 79 Parquets existentes foi aprovada:
3.933.955 registros e 76 colunas iguais, sem alterar dados, partições ou modelos.

| Arquivo local | Uso |
|---|---|
| `microdados_enem_2023.zip` | Pacote nacional original, 549.511.687 bytes |
| `MICRODADOS_ENEM_2023.csv` | Fonte nacional, 1.777.162.429 bytes; separador `;`, codificação Latin-1 |
| `competencias_redacao_enem_2023.zip` | Complemento de correção da redação, 377.423.159 bytes |
| `documentacao_enem2023/` | Dicionário e documentos técnicos extraídos do pacote nacional |
| `complementos/COMPETENCIAS_REDACAO_2023/` | Oito arquivos extraídos do complemento, incluindo seu CSV de 37 colunas |
| `enem2023.source.json` | Metadados históricos acrescidos da incorporação local |
| `incorporacao_local_2026-11-07.json` | Movimentação, hashes, CRC e extrações |

O complemento **não é preditor nem é unido à base de modelagem de NU_NOTA_CN**:
seus campos são competências, notas e resultados da correção da redação, excluídos
pelo protocolo. Preservá-lo não exige repetir treinamento ou abrir novamente o teste.
Os arquivos de provas e gabaritos permanecem disponíveis dentro do ZIP principal;
não foram extraídos porque não integram as entradas do estudo.

Originais são imutáveis e ignorados pelo Git. A evidência versionável está em
`resultados/ciencias_natureza/checkpoint-6-2026-11-07/`, detalhada em
[Checkpoint 6](../../docs/checkpoint-6-resultados.md). O arquivo `.zip.part` e a trava
antiga que já existiam foram preservados como resíduos de uma tentativa anterior;
não são a fonte válida e não devem ser usados no lugar do ZIP completo.

## Reprodução em outra cópia

Obter o pacote nacional e, se desejado, o complemento no
[portal do Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
Conferir ano, tamanho, dicionário, CRC e hashes antes de preparar a base.
`collect` copia uma fonte explicitamente indicada, sem extrair ZIPs; `fetch-enem`
automatiza a obtenção do pacote desta edição. Nenhum original existente deve ser sobrescrito.

A movimentação deste ambiente foi executada por `scripts/incorporar_fontes_2023.py`;
não repetir esse comando com o destino já preenchido. Para uma nova conferência
integral, sem reingerir nem treinar, usar uma saída de evidência ainda inexistente:

```bash
.venv/bin/python scripts/validar_fontes_2023.py --output tmp/nova-validacao-fontes.json
```

A validação exige o contrato nacional de linhas, colunas, ano e alvos e compara
cada célula normalizada com a preparação preservada. O hash comprova identidade
com a fonte histórica local; não foi fornecido um checksum assinado pelo Inep.
