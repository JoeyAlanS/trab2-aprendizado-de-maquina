# Interpretação das variáveis - conferência de 2023

Dicionário oficial efetivamente obtido do pacote do Inep em 21/10/2026.
Cópia sem alteração: `referencias/dicionario-enem2023.xlsx`.
Aba: `MICRODADOS_ENEM_2023`. SHA-256:
`1411ad89784f7f960dc1c1fc13b0d22eee696e2613cb762072665fa547ae6cf6`.

O extrato `referencias/dicionario_enem2023.json` preserva descrição, tipo declarado,
tamanho e alternativas das **76 colunas**, correspondentes ao cabeçalho do CSV.
Foram removidos somente espaços externos dos nomes/rótulos na representação JSON;
o arquivo oficial foi preservado. O código verifica as candidatas contra esse extrato
e rejeita categorias não previstas nas alternativas enumeradas do desenvolvimento.

## Escolhas da representação inicial

- **NU_NOTA_CN:** nota de Ciências da Natureza. Somente y; nunca X.
- **NU_INSCRICAO:** número de controle mascarado da publicação. Texto, preservado
  para controle/partições; não é preditor. NU_ANO é constante de edição.
- **Q005:** número de moradores, incluindo o participante, com alternativas 1 a 20.
  Única candidata numérica da representação inicial. Conferir valores antes do ajuste.
- **Q001/Q002:** escolaridade dos responsáveis. A-G representam níveis; H significa
  "Não sei". Inicialmente categóricas, sem converter H em nível ou imputar conhecimento.
- **Q003/Q004:** grupos de ocupação, com A-E e F = "Não sei". One-hot, sem distância
  numérica entre grupos. **Q004 está rotulada como "Numérica" no campo Tipo do dicionário,
  embora suas alternativas sejam A-F**; a interpretação usa as alternativas e o CSV,
  preservando o tipo declarado no extrato para rastrear essa inconsistência.
- **Q006:** faixas de renda A-Q; A = nenhuma renda, Q = faixa superior aberta.
  Não foi transformada em renda monetária aproximada nem confundida com dado ausente.
- **Q022/Q024:** quantidade de celulares/computadores em alternativas A-E; E significa
  quatro ou mais. Não tratar o limite inferior 4 como contagem exata sem justificativa.
- **Q025:** acesso à internet; A = não, B = sim. Não é uma medida de qualidade do acesso.
- **TP_ESCOLA:** 1 = não respondeu, 2 = pública, 3 = privada. O valor 1 é alternativa
  observada, não célula ausente. Comparações de nota entre grupos não estabelecem efeito causal.
- **TP_COR_RACA:** 0 = não declarado e 6 = não dispõe da informação são alternativas
  distintas. A análise não infere capacidade individual nem interpreta associação como causa.
- **TP_LINGUA:** 0 = inglês, 1 = espanhol. Representa a opção, não proficiência.
- **SG_UF_PROVA:** localização de aplicação da prova, sem inferir residência.
- **Campos escolares:** manter ausências e medir cobertura; o arquivo não fornece
  identificador individual de escola. Não extrapolar para escolas inéditas.

## Exclusões da entrada

Todas as notas, competências da redação, respostas, gabaritos, presença e situação
da redação ficam fora de X. Códigos de prova ficam bloqueados sem justificativa de
perfil disponível no momento da previsão. Identificador e ano servem somente a controle.
Nomes e códigos territoriais redundantes não são usados juntos. A primeira representação
usa UF de prova, não municípios, sem remover participantes de nenhuma região.

## Fonte e limitações

O Leia-me oficial, pp. 6-9, confirma o questionário de 25 perguntas e o CSV delimitado
por ponto e vírgula. O modelo simplificado de divulgação exclui informações de residência,
identificador de escola e alguns registros por critérios de proteção da publicação.
Essas exclusões são da fonte publicada e não foram realizadas pelo projeto. A base
nacional do enunciado é o arquivo disponibilizado pelo Inep; não equivale a todos os
inscritos possíveis ou a toda a população brasileira.
