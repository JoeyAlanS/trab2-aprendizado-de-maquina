"""Análise dos resultados publicados. Células # %% podem ser abertas em Jupyter/VS Code.

Não lê microdados individuais, não treina e não reabre o conjunto de teste.
"""

# %% Carregar as tabelas agregadas da entrega
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
experiments = pd.read_csv(ROOT / "resultados/experimentos.csv")

# %% Comparação inicial: todos os modelos obrigatórios, mesmos participantes
initial = experiments.query("stage == 'comparacao_inicial' and row_type == 'summary'")
print(
    initial[["model", "rmse", "rmse_std", "mae", "r2"]].sort_values("rmse").to_string(index=False)
)
print(
    "\nTrio do catálogo completo:",
    initial.query("model != 'baseline'").nsmallest(3, "rmse").model.tolist(),
)

# %% Hipóteses de representação, comparáveis somente no desenvolvimento
variants = experiments.query("stage == 'variantes' and row_type == 'summary'")
print("\nVariantes:")
print(variants[["model", "variant", "rmse", "rmse_std"]].to_string(index=False))

# %% Teste final: resultado único, não média de dobras
final = experiments.query("stage == 'teste_final'")
print("\nTeste reservado (receitas já congeladas):")
print(
    final[["model", "n_evaluated", "rmse", "mae", "r2"]].sort_values("rmse").to_string(index=False)
)
print("\nFiguras: resultados/figuras/. Galeria: apresentacao/index.html")
