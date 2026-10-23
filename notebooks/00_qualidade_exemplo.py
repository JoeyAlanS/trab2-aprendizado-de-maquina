# %% [markdown]
# # Diagnóstico técnico - dados inteiramente fictícios
# Execute primeiro: python -m enem_base prepare --config configs/exemplo.toml
# Este roteiro verifica importação e qualidade. Não representa uma análise do ENEM.

# %%
import json
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parents[1]
output = root / "dados/processed/exemplo-v1"
manifest = json.loads((output / "manifesto.json").read_text(encoding="utf-8"))
if manifest.get("synthetic") is not True:
    raise ValueError("Este roteiro só aceita a demonstração fictícia.")
report = json.loads((output / "qualidade.json").read_text(encoding="utf-8"))
data = pd.concat(
    [pd.read_parquet(output / p["file"]) for p in manifest["parts"]], ignore_index=True
)

# %%
print("DADOS FICTÍCIOS - nenhuma nota alvo selecionada")
print(data.dtypes.to_string())
print("Ausências:\n" + pd.Series(report["missing"]).to_string())
print("Categorias fictícias:\n" + data["categoria"].value_counts(dropna=False).to_string())
print("Linhas preservadas:", len(data), "| Removidas:", report["rows_removed"])
print("Alvo:", manifest["target"], "| Modelos treinados:", manifest["models_trained"])

# %% [markdown]
# A interpretação aqui é operacional: células ausentes permanecem ausentes, códigos
# permanecem textuais e o pipeline preserva as 12 linhas. Nenhuma associação é inferida.
