# Decisões e pendências

Atualização em **21/10/2026**: o usuário definiu **Ciências da Natureza e suas Tecnologias**.
Alvo: **NU_NOTA_CN**. O registro da fase inicial, de 16/10/2026, permanece no relatório
de validação da fase 1. A restrição de manter o alvo indefinido foi superada por essa
instrução explícita; não implica escolha automática dos resultados ou da solução final.

Contrato da pesquisa: `configs/ciencias_natureza.toml`. Pergunta inicial:
"Em que medida o perfil socioeconômico, escolar e demográfico permite estimar a nota
de Ciências da Natureza no ENEM 2023?" A análise avalia associações, sem conclusão causal.

## Decisões técnicas desta base

| Decisão | Motivo | Reversão/adaptação |
|---|---|---|
| Python 3.13, ambiente `.venv`, pacote `src/` | Isolamento e importações consistentes em testes e CLI | Atualizar versão e regenerar lock com validação |
| TOML e caminhos relativos à raiz declarada | Evitar caminhos pessoais na configuração | Novo TOML versionado por execução |
| CSV inicialmente textual e conversão explícita | Preservar códigos e não interpretar categorias como quantidades | Confrontar tipos com dicionário |
| Fonte imutável; Parquet em lotes | Preservação, compressão e acesso posterior por colunas | Alterar formato com medição e registro |
| Não remover, imputar, balancear ou limitar notas na importação | Decisões dependem de significado, hipótese e protocolo | Implementar no estágio adequado, nunca silenciosamente |
| Erro em identificadores repetidos, ausentes e números inválidos | Evitar partições ambíguas e correções escondidas | Investigar e documentar regra específica antes de tratar |
| Bloqueio conservador de códigos de prova em X | Sem justificativa de perfil na fase atual | Revisar apenas com evidência do dicionário e contexto de previsão |
| Exemplo fictício de 12 linhas, sem nota alvo | Validar mecanismos sem escolher área de pesquisa | Não usar como amostra do ENEM nem resultado científico |
| Pré-processador numérico/categórico apenas como fábrica | Reutilização e ajuste por dobra | Escolher imputação/codificação a partir do desenvolvimento |

## Escolhas que permanecem abertas

| Escolha | Possibilidades registradas | Evidência necessária |
|---|---|---|
| Nota alvo (definida) | Ciências da Natureza, NU_NOTA_CN | Informação direta do usuário em 21/10/2026 |
| Pergunta de pesquisa | Relação entre blocos de perfil e nota; efeito de representações; erros por grupo | Objetivo específico e hipótese testável após alvo |
| Features originais | Demografia, situação escolar, contexto da escola, localização, língua, Q001-Q025 | Significado, disponibilidade, cobertura e risco de vazamento |
| Categorias e desconhecimento | One-hot, codificação ordinal justificada, categoria própria para desconhecido | Dicionário e comparação no desenvolvimento |
| Imputação | Mediana, moda, constante ou alternativa justificada | Ausências e efeitos por dobra; nunca no alvo |
| Três features novas | Razões, contagens ou interações; nenhuma fórmula escolhida | Hipótese, unidades, limites e denominadores |
| Fontes externas | Nenhuma; indicador municipal/escolar de 2023, se pertinente | Fonte, ano, território, chave única e cobertura |
| PCA | Bloco numérico ou codificado; PCA ou IncrementalPCA | Escala, memória, variância do treino e dois regressores |
| Balanceamento | Pesos, over/undersampling adequados à regressão | Faixas/pesos definidos dentro do treino e comparação do mesmo regressor |
| Erros por grupo | UF, renda, tipo de escola ou outro perfil permitido | Escolha no desenvolvimento, n e limitações |
| Zeros | Manter por padrão; eventual experimento apenas no treino | Mesma validação/teste incluindo zeros e justificativa |
| Dois aprofundamentos | Ablação de blocos; categorias; localização; custo/complexidade; interação | Duas hipóteses adicionais além das exigências mínimas |

Não escolher features com base no teste. Não tratar associação como causalidade nem
inferir capacidade individual. Município de prova e município da escola têm significados
próprios; nenhum deles deve ser renomeado como residência.

## Registro para a próxima fase

Preencher antes de executar a análise científica:

- Equipe e responsáveis: **a preencher**.
- Nota alvo atribuída e evidência da atribuição: **NU_NOTA_CN, usuário em 21/10/2026**.
- Pergunta, hipótese e justificativa: **ver `pesquisa_ciencias_natureza.md`**.
- Arquivo oficial, data de obtenção, edição e SHA-256: **a preencher**.
- Dicionário consultado, versão e mapeamento de colunas: **a preencher**.
- IDs das partições, hash, semente e localização: **a preencher**.
- Variáveis excluídas, criadas e selecionadas, com motivo: **a preencher**.
- Estratégias, faixas e grupos definidos no desenvolvimento: **a preencher**.
- Prazos do AVA: **a consultar**.

Cada mudança metodológica deverá registrar data, hipótese, configuração, código e
resultado, inclusive sem melhoria. As outras notas permanecem excluídas das entradas.
