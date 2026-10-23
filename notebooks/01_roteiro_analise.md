# Exploração futura - executar depois de definir o alvo

1. Ler o manifesto das partições e verificar hash da fonte e IDs.
2. Selecionar somente `partition=development` e as features candidatas permitidas.
3. Interpretar o dicionário: categoria, ordinalidade, contagem, desconhecimento e ausência.
4. Descrever tipos, cobertura, categorias, distribuição do alvo e zeros.
5. Investigar relações que possam sustentar hipóteses, com n, fonte e limitações.
6. Registrar três features propostas e ao menos duas hipóteses adicionais de aprofundamento.
7. Definir faixas/grupos antes da avaliação final, sem olhar resultados do teste.
8. Encaminhar transformações e experimentos a funções reproduzíveis no pacote.

Não carregar o teste para escolher decisões, não calcular imputação no desenvolvimento
inteiro antes da CV e não fazer target encoding com a nota da própria linha.
