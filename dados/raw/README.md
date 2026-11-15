# Dados originais

Obter **ENEM 2023** no [portal de microdados do Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
O projeto usa o pacote nacional `microdados_enem_2023.zip`, não uma amostra regional.

Na raiz do repositório, em uma instalação nova:

```bash
.venv/bin/python -m enem_base fetch-enem --raw dados/raw
```

O comando baixa por HTTPS, confere o CRC, extrai o CSV e a documentação e registra
os hashes. Não sobrescreve manifestos existentes. Se o ZIP já foi obtido, colocá-lo
nesta pasta com o mesmo nome antes de executar o comando.

| Arquivo | Bytes | SHA-256 da fonte utilizada |
|---|---:|---|
| microdados_enem_2023.zip | 549.511.687 | `19512b7e29c9c8e940554396969722081341caa275c245a6c9d2d559c5d13a0a` |
| MICRODADOS_ENEM_2023.csv | 1.777.162.429 | `c8b1fae0a97b6ac826d950d16696efa3d89c133b0165128aadd2997c2315b666` |
| competencias_redacao_enem_2023.zip | 377.423.159 | `db3118c5908645a92d95e81a02b8474c561daf852602abf459d8952becf40a34` |

CSV nacional: separador `;`, codificação Latin-1, 3.933.955 linhas e 76 colunas.
Os hashes identificam os arquivos usados, sem alegar checksum assinado pelo Inep.
Preservar os originais; todas as transformações são geradas por código em outra pasta.

O complemento de competências de redação foi preservado, mas **não foi unido ao
conjunto de treinamento**. Resultados de redação e de outras provas não são entradas.
Ele não é necessário para reproduzir a modelagem de Ciências da Natureza.

Os arquivos grandes são locais e ignorados pelo Git. Uma transferência incompleta
`.part` ou uma trava abandonada não constitui fonte válida.
A preparação usa `configs/enem2023.toml`. A conferência integral do CSV com todos
os Parquets pode ser repetida sem treinamento, escolhendo uma saída nova:

```bash
.venv/bin/python scripts/validar_fontes_2023.py --output tmp/conferencia-fontes.json
```
