# %% [markdown]
# # Ciências da Natureza - resultados executados no desenvolvimento
# Este roteiro lê somente relatórios agregados. Não abre o teste nem refaz decisões.
# Execute os comandos oficiais do README antes deste arquivo.

# %%
import json
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parents[1]
results = root / "resultados/ciencias_natureza"
eda = json.loads((results / "eda-v1/diagnostico_desenvolvimento.json").read_text(encoding="utf-8"))
print("Alvo:", eda["target"], "| Desenvolvimento:", eda["rows"])
print("Teste avaliado:", eda["test_evaluated"])
print("Resumo da nota:\n" + pd.Series(eda["target_summary"]).to_string())
print("Ausências nas candidatas:\n" + pd.Series(eda["missing"]).to_string())

# %%
manifest = json.loads((results / "cv-inicial-v1/manifesto.json").read_text(encoding="utf-8"))
if manifest["status"] != "completed" or manifest["test_evaluated"]:
    raise ValueError("A comparação deve estar concluída e restrita ao desenvolvimento.")
summary = pd.read_csv(results / "cv-inicial-v1/resumo_cv.csv")
print("Validação cruzada inicial - três dobras; ddof=0")
print(summary.to_string(index=False))

# %% [markdown]
# A comparação inicial não escolhe ainda a solução final. Para a entrega completa,
# faltam outras famílias, engenharia/seleção, PCA, balanceamento, buscas, curva,
# aprofundamentos e a avaliação final do teste após congelar a solução.
# Diferenças por tipo de escola ou perfil descrevem associações da base, sem causalidade.
