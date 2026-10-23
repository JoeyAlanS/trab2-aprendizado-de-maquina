# Boas práticas de desenvolvimento e dados

## Alterações e revisão

Manter funções com uma responsabilidade, nomes claros, docstrings nos contratos e
configuração fora da lógica. Evitar dependência do diretório pessoal, números de nota
fixados em código, `inplace=True` e alterações manuais nos dados preparados. Usar o
pacote instalado, sem `sys.path.append` em notebooks. Formatar com Ruff e executar testes
de contrato quando alterar leitura, tratamento, elegibilidade ou partições.

Os testes verificam efeitos relevantes: preservação da origem, zeros e códigos,
ausências explícitas, erros estruturais, integridade entre lotes, falha sem publicação,
separação das partições e aprendizado de transformações só no treino. Não usar testes
como substituto da conferência do dicionário nem como prova de desempenho nacional.

## Ambiente

Usar `.venv` de Python 3.13 e `requirements.txt`, que inclui o lock completo. O
`pyproject.toml` registra limites compatíveis; o lock registra a resolução validada.
Atualizar dependências de forma deliberada e revisar os resultados antes de substituir
o lock. Não instalar dependências globalmente para executar este projeto.

O script `scripts/verificar.ps1` executa lint, formato, testes e verificação de
dependências; encerra no primeiro erro. O workflow de CI repete esses checks em
Python 3.13 no Windows e Linux. Seu estado remoto ainda não foi verificado.

## Fonte e tratamento

Preservar raw. Versionar pequenos exemplos fictícios, contratos, código e metadados
aprovados; obter os arquivos grandes pelas instruções. Não registrar linhas de pessoas
em logs, notebooks ou erros. O `.gitignore` evita o versionamento automático de dados
locais; revisar o conteúdo real antes de qualquer publicação.

Não supor que número significa medida: município, alternativa e código de categoria
são textuais até confirmação semântica. Não aplicar regras universais de faixa 0-1000
a todas as notas sem evidência. Não remover valores extremos por o modelo errar neles.
Não converter desconhecimento em ausência ou valor ordinal sem justificativa.

Manter separadas limpeza determinística e transformação aprendida. Mediana, moda,
escalas, categorias raras, seleção, PCA, clusters e estatísticas por categoria devem
ser aprendidos no treino de cada dobra. Codificações supervisionadas precisam de
divisões internas para que a própria nota da linha não construa sua feature.

As saídas técnicas fictícias e resultados científicos têm identificação explícita.
Templates vazios não devem receber números de demonstração que possam parecer reais.

## Git e rastreabilidade

Mudanças pequenas e coerentes, commits com descrição do efeito, referência da fonte e
configuração associada. Antes de publicar, executar checks, inspecionar `git diff`,
conferir arquivos ignorados e conteúdo previsto para o commit. O hash da fonte e das
partições acompanha os experimentos; guardar também commit e estado de trabalho.
Estado Git sujo registrado não torna código não commitado recuperável: fazer commit
antes de usar resultados na entrega acadêmica. Esta fase não executa commit ou push.
