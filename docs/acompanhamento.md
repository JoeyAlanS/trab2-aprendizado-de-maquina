# Acompanhamento e auditoria final - ENEM 2023

Joey Alan de Freitas Solis e Paulo Henrico

Universidade de Fortaleza (Unifor) - Professor Tulio

Revisão de 7 de novembro de 2026. Este documento registra desenvolvimento, execuções conferidas e limites da validação. Não comprova apresentação oral, submissão no AVA ou compilação dentro de uma conta do Overleaf.

## 1 Objetivo e metodologia

Estimar NU_NOTA_CN a partir de quarenta atributos de perfil socioeconômico, escolar e demográfico, comparando sete famílias de regressão. A fonte nacional contém 3.933.955 linhas e 76 colunas. Foram mantidos os 2.692.427 alvos observados, incluindo 16.547 notas zero. As 1.241.528 ausências de alvo não foram imputadas.

A divisão 80/20, semente 42, reserva 538.486 participantes para teste. Os 2.153.941 restantes usam três dobras de validação cruzada, iguais para os modelos. Transformações são ajustadas no treino de cada dobra; identificadores, presença, notas e resultados de outras avaliações ficam fora dos preditores. O teste foi aberto somente após seleção e congelamento das receitas.

Os dois ZIPs entregues pelo usuário estão em dados/raw/. Os arquivos passaram por CRC; o ZIP nacional e o CSV coincidem com os hashes históricos. A comparação de todas as células normalizadas do CSV com os 79 Parquets existentes foi aprovada. O complemento de competências da redação está preservado, sem integração à matriz de atributos.

## 2 Checkpoints e entregáveis

| Etapa | Resultado confirmado |
|---|---|
| 1 - Modelos | Sete algoritmos, três dobras nacionais cada; 21 avaliações |
| 2 - Seleção | Stacking, SVM linear e Random Forest entre os sete; critério RMSE |
| 3 - Curvas iniciais | Três modelos, cinco tamanhos e três dobras; 45 pontos |
| 4 - Busca e teste | 60 configurações, 180 avaliações CV, 45 pontos finais e teste de cinco modelos |
| 5 - Visualizações | Coleção de 17 gráficos PNG/SVG, 14 tabelas e galeria local |
| 6 - Artigo e fonte | Artigo com resultados reais; fonte original reconciliada integralmente |
| 7 - Entrega atual | Pitch em roteiro, acompanhamento e artigo em LaTeX; PDFs compilados localmente e pacote Overleaf |

O pedido atual dispensa slides. O pitch é um roteiro oral com divisão nominal das falas, duração planejada de doze minutos, tabela de consulta e perguntas/respostas. Ensaio, apresentação, prazos e submissão permanecem sob responsabilidade da equipe.

## 3 Todos os experimentos previstos foram executados?

Sim, há evidências completas das etapas científicas previstas. Isso não significa que todos os algoritmos foram aplicados ao conjunto de teste. A matriz abaixo explicita o que foi executado e conferido.

| Tipo de execução | Quantidade e cobertura | Conferência realizada nesta revisão |
|---|---|---|
| Sete algoritmos solicitados | 7 modelos x 3 dobras = 21 avaliações | Manifestos, hashes, métricas finitas, três dobras e cobertura nacional |
| Referências iniciais | Média, linear, Ridge e árvore; 12 avaliações | Mesmos critérios e partições; 2.153.941 validações por modelo somadas |
| Variantes e hipóteses | 21 avaliações; engenharia, seleção, PCA em dois modelos, ponderação e duas ablações | Resultados por dobra e identidades das fontes |
| Busca de parâmetros | 5 modelos x 12 configurações x 3 dobras = 180 avaliações | Métricas recompostas das previsões persistidas; comparação com GridSearchCV |
| Curvas iniciais | 3 modelos x 5 tamanhos x 3 dobras = 45 pontos | Cobertura, arquivos de pontos e hashes dos ajustes |
| Curvas finais | 45 pontos das receitas congeladas | Identidade dos parâmetros/subconjuntos, integridade e reprodução da CV em 100% |
| Teste final | 5 modelos; 538.486 participantes iguais por modelo | RMSE, MAE, R² e 260 registros por grupo recompostos das previsões |

Os sete algoritmos são SVM linear, KNN, Bagging, Pasting, Random Forest, Gradient Boosting e Stacking. O conjunto de teste recebeu apenas Stacking, SVM linear, Random Forest, média e linear de referência. KNN, Bagging, Pasting, Boosting, Ridge e árvore isolada não tiveram teste final, conforme o escopo fixado; não se deve ampliar a seleção depois de consultar o teste.

As curvas finais não representam 45 ajustes totalmente novos. Trinta pontos de SVM/Random Forest reaproveitaram configurações idênticas do Checkpoint 3. Doze pontos do Stacking reutilizaram modelos de base com novo combinador treinado sobre previsões fora da dobra interna; três pontos usaram o treino completo das dobras já calculado nas buscas. A origem de cada ponto está registrada. A revisão não treinou novos modelos nem produziu novas previsões do teste.

## 4 Resultados e interpretação

| Modelo no teste | RMSE | MAE | R² |
|---|---|---|---|
| Stacking | 76,190 | 55,325 | 0,2497 |
| Linear de referência | 76,517 | 55,616 | 0,2433 |
| SVM linear | 76,622 | 55,538 | 0,2412 |
| Random Forest | 76,658 | 55,821 | 0,2405 |
| Média do treino | 87,959 | 66,285 | aproximadamente zero |

Fonte: previsões persistidas dos microdados Inep/ENEM 2023. Métricas em 538.486 participantes; RMSE e MAE em pontos. O teste é separado da validação cruzada usada para selecionar receitas.

O Stacking reduz o RMSE da média em 13,38%. Sua vantagem sobre a linear é pequena e precisa ser ponderada frente ao custo observado. Os resultados do trio são próximos entre CV e teste, mas isso não comprova generalização para outro ENEM. As buscas produziram ganhos mínimos; não foram calculados testes de significância ou intervalos de confiança.

As curvas mostram gaps finais de RMSE de aproximadamente 0,193, 0,007 e 0,400 para Stacking, SVM e Random Forest. Não há sobreajuste acentuado nesses tamanhos, mas R² baixo isoladamente não demonstra subajuste. O menor treino da curva já tem cerca de 143.596 participantes.

Os erros são maiores nos extremos: no Stacking, RMSE de 154,31 abaixo de 400 e 160,74 a partir de 700. Notas baixas são superestimadas e altas são subestimadas em média. Engenharia trouxe ganho pequeno; seleção e PCA pioraram as configurações avaliadas. A ponderação do Ridge piorou o RMSE global para 125,202, embora tenha reduzido erros de extremos na validação. As duas ablações aumentaram o erro, sustentando contribuição preditiva do bloco socioeconômico e da UF, sem interpretação causal.

## 5 Testes de software e verificações técnicas

A suíte existente foi executada nesta revisão: 81 testes aprovados, sem falhas, em 11,44 segundos. Esses testes usam fixtures técnicas de unidade/integração e não constituem experimentos científicos com a população nacional. Não foram criados novos arquivos de testes nem substituídas métricas reais por resultados de fixtures.

| Área da suíte existente | Testes aprovados |
|---|---|
| Ingestão | 19 |
| Pré-processamento | 13 |
| Dashboard | 11 |
| Estudo e modelos | 9 |
| Configuração e CLI | 7 |
| Partições | 7 |
| Aquisição e integração | 6 |
| Relações entre atributos | 5 |
| Download oficial | 4 |
| Total | 81 |

Comando executado: .venv/bin/python -m pytest -q, com relatório JUnit em resultados/ciencias_natureza/checkpoint-7-2026-11-07/pytest.xml. A auditoria científica foi executada por scripts/auditar_entrega.py e grava cobertura_execucoes.csv, validacao_buscas.json, validacao_teste.json e auditoria_experimentos.json no mesmo diretório.

Lint, verificação de formatação e compatibilidade das dependências locais foram aprovados. O ambiente numérico foi mantido; a revisão da entrega não alterou os módulos de treinamento. As fontes LaTeX foram compiladas localmente e os PDFs renderizados para inspeção visual. O pacote foi preparado para importação no Overleaf, com instruções de compilador e arquivo principal.

## 6 Limites do que foi validado

Não foram executados teste temporal em outra edição, validação externa, inferência causal, teste de significância, ensaio oral cronometrado ou apresentação. Também não se declara compilação dentro de uma conta Overleaf: a evidência é a compilação local das fontes fornecidas. A suíte foi executada no Linux deste ambiente; execução Windows depende da automação remota e deve ser consultada separadamente.

Os testes do dashboard verificam componentes existentes e não substituem uma nova inspeção visual interativa de todo o navegador nesta revisão. Há registros históricos de verificações do frontend, mas não foram apresentados como se tivessem sido repetidos agora. A rastreabilidade do experimento usa arquivos reais persistidos e hashes; os hashes locais não são uma assinatura emitida pelo Inep.

## 7 Dificuldades, soluções e organização

A ausência inicial dos originais foi resolvida com a incorporação dos ZIPs fornecidos e comparação integral do CSV. O custo do KNN foi tratado por busca exata compacta, conferida contra distâncias de referência. Interrupções de execução motivaram persistência por dobra e bloco, com retomada condicionada à mesma fonte e configuração. Resultados negativos foram mantidos, como a piora global da ponderação.

A limpeza retirou versões preliminares e pacotes duplicados da área ativa de entrega, preservando um arquivo histórico e o inventário de remoções. Dados originais, banco, partições, modelos ajustados e previsões reais permanecem locais. Arquivos grandes ou individuais não integram o commit; os resultados agregados, código, fontes LaTeX, PDFs e evidências verificáveis são publicados no repositório.

A revisão das alterações precede o commit e o push. A identificação do commit e a confirmação de sincronização com o remoto devem ser consultadas no histórico Git e no relato final da entrega, sem antecipar sucesso antes da operação.

## 8 Referências e próximos passos

Dados oficiais: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem

Repositório: https://github.com/JoeyAlanS/trab2-aprendizado-de-maquina

Importação no Overleaf: https://docs.overleaf.com/managing-projects-and-files/uploading-a-project

As referências científicas completas estão no artigo. Para a equipe, faltam ensaiar as falas, conferir o prazo no AVA e realizar a apresentação/submissão. A duração de doze minutos é planejada, não aferida em ensaio.
