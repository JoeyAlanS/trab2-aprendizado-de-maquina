# Validação do frontend — 21/10/2026

Entrega local em Python 3.13.7, Streamlit 1.66.1 e Plotly 6.9.0. O dashboard
utiliza o snapshot oficial `resultados/ciencias_natureza/dashboard-v1/`.

## Verificações executadas

- `scripts/verificar.ps1`: **71 testes aprovados em 18,54 s**, Ruff sem erros,
  59 arquivos formatados e `pip check` sem dependências quebradas.
- Seis novos testes de contratos e interface em `tests/test_dashboard.py`, com
  fixtures fictícias temporárias. Os demais 65 testes existentes continuaram aprovados.
- AppTest adicional com o snapshot **oficial**: navegação nas quatro páginas,
  indicadores, gráficos/tabelas produzidos, filtro de Ceará, reset dos filtros e
  busca de renda/Q006 no dicionário. Nenhuma exceção nas páginas.
- Servidor local em `127.0.0.1:8501`; endpoint `/_stcore/health` respondeu `ok`.
- Snapshot lido com validação de hash de todos os ativos. Contagem, média, desvio
  amostral e zeros conciliados com a EDA oficial.

Evidência estruturada da execução com dados oficiais:
`resultados/ciencias_natureza/evidencias/frontend_verificacao.json`.

| Recorte | Participantes | Nota média CN | Desvio amostral | Notas zero |
|---|---:|---:|---:|---:|
| Desenvolvimento completo | 2.153.941 | 495,774199 | 87,921084 | 13.236 |
| Prova aplicada no Ceará | 139.838 | 482,657198 | 88,685282 | 835 |

O recorte do Ceará é uma verificação funcional; não define uma nova população
de pesquisa nem demonstra causalidade. A UF é a da aplicação da prova.

## Cobertura dos novos testes

1. Agregados reconciliados com notas originais das fixtures: contagens, médias
   ponderadas, desvio amostral, zeros e resultados por grupo/UF.
2. Rejeição de agregação que contenha participantes de teste ou alvo ausente.
3. Integridade dos ativos, ausência de IDs individuais e recusa de sobrescrita.
4. Interação dos filtros, combinação sem participantes, aviso e reset.
5. Navegação, seleção de dimensão/métrica, tabelas, controles de download e busca
   de dicionário com e sem resultados.
6. Fonte ausente: mensagem com orientação, sem indicadores fictícios.

## Limite da inspeção visual

A sessão de automação retornou inventário vazio de navegadores e aplicativos.
A tentativa de abrir o navegador integrado informou que ele não estava disponível;
a solicitação de abertura no painel do Codex ficou na fila. Por isso **não houve
inspeção visual real em desktop ou celular**, nem interação por teclado/touch ou
download pelo navegador. AppTest verifica execução e interações Python, sem
reproduzir layout, desenho final dos gráficos ou ações do navegador.

O tema usa recursos nativos, navegação Streamlit e cartões que se reorganizam em
linhas. Esse desenho foi preparado para tamanhos menores, mas a responsividade
visual ainda deve ser conferida no navegador. Roteiro manual:

- Abrir `http://127.0.0.1:8501`, percorrer as quatro páginas e conferir gráficos,
  rótulos e tabelas em uma janela ampla e em uma janela estreita.
- Aplicar UF, escola, sexo e treineiro; conferir o reset e uma combinação vazia.
- Alternar média/participantes, as dimensões e RMSE/MAE/R²; abrir as três dobras.
- Pesquisar Q006, ler as alternativas de renda e testar termo sem resultado.
- Usar Tab/Enter nos controles, abrir/fechar a barra lateral, baixar os CSVs e
  exportar uma figura PNG pela barra do gráfico.

## Escopo científico preservado

O painel consulta agregados do desenvolvimento e resultados de CV já executados.
Não treina modelos, não oferece previsões individuais e não avalia o teste.
As 538.486 linhas de teste permanecem reservadas. O snapshot registra
`test_evaluated=false`. Artigo, seleção final e etapas experimentais restantes
continuam descritos em `docs/andamento_ciencias_natureza.md`.
