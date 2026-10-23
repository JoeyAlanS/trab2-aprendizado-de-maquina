# Dados preparados

`enem2023-v1/` contém a importação nacional aprovada de 21/10/2026: 3.933.955 linhas,
76 colunas e 79 partes. O manifesto da **ingestão** permanece neutro quanto ao alvo e
registra `models_trained=false` porque essa etapa apenas prepara dados. O alvo de
pesquisa está em `configs/ciencias_natureza.toml` e os treinamentos efetivamente
executados estão em `resultados/ciencias_natureza/cv-inicial-v1/manifesto.json`.

Uma subpasta por execução aprovada: partes `part-00000.parquet`, `qualidade.json` e
`manifesto.json`. Usar nomes novos e contratos TOML versionados. Não editar Parquet
manualmente. Saídas e temporários não são versionados automaticamente.

Para ler o dataset com pandas, selecionar **somente** os arquivos `*.parquet`, pois
o diretório também contém JSON. Em escala nacional, ler apenas as colunas necessárias
ou usar `pyarrow.dataset` com lista explícita das partes, sem concatenar tudo por rotina.

`exemplo-v1/` é fictício. Sua validação não demonstra desempenho na base nacional.
