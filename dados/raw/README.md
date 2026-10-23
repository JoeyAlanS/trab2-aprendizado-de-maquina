# Dados originais

Esta pasta recebe os originais. Não editar, limpar nem salvar saídas sobre eles.
Arquivos locais ficam fora do Git. O exemplo fictício versionado está em `exemplos/`.

## Obter ENEM 2023

1. Acessar o [portal oficial do Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).
2. Escolher **Microdados do Enem 2023**, o pacote principal listado na seção 2023.
   Não substituir pelo complemento com notas detalhadas de avaliadores.
3. Baixar o pacote, registrar data, URL final, tamanho e SHA-256. Guardar seu Leia-me e
   dicionário de 2023. Conferir o pacote recebido antes de interpretar variáveis.
4. Extrair manualmente para área local apropriada e manter o arquivo nacional
   `MICRODADOS_ENEM_2023.csv` nesta pasta. Não editar o CSV. A coleta fornecida não
   extrai ZIPs automaticamente.
5. Conferir separador e codificação com o arquivo/dicionário e revisar o TOML.
   `latin-1` e `;` estão preparados como parâmetros iniciais; a fonte ainda não foi
   processada. Não confiar apenas em uma leitura sem erro para validar a codificação.
6. Executar a preparação. O diagnóstico exige 3.933.955 linhas e 76 colunas do enunciado.
   Divergências bloqueiam a saída e precisam ser investigadas, inclusive eventual
   atualização do pacote oficial. Não utilizar uma amostra como fonte principal.

Para copiar um CSV já obtido, preservando-o, use a coleta local explícita:

```powershell
.\.venv\Scripts\python.exe -m enem_base collect --source "CAMINHO_DO_CSV_OBTIDO" --destination dados/raw/MICRODADOS_ENEM_2023.csv
```

`--source` também aceita URL HTTPS explícita; `--max-bytes` limita o tamanho e
`--sha256` compara um digest esperado, se disponível de fonte confiável. Sem digest
esperado, o hash é calculado para rastreabilidade e não comprova autenticidade externa.
O comando de demonstração não acessa a rede. Uma fonte existente nunca é sobrescrita.
O manifesto `.source.json` deve ser guardado junto ao arquivo coletado.

Em **21/10/2026**, o pacote nacional foi obtido pelo endereço oficial, verificado por
CRC do ZIP e extraído sem alterar a fonte. O manifesto local `enem2023.source.json`
registra os hashes; uma cópia de metadados fica em `docs/referencias/fonte_enem2023.json`.
O arquivo CSV tem 1.777.162.429 bytes. O andamento da importação e os resultados
verificados estão em `docs/andamento_ciencias_natureza.md`.

O dicionário foi conferido e preservado; ver `docs/dicionario_ciencias_natureza.md`.
A rotina `fetch-enem` automatiza a obtenção e extração para esta edição, usando trava
contra execução simultânea. O comando genérico `collect` continua sem extrair ZIPs.
