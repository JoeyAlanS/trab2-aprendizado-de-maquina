"""Diagramar figuras do artigo a partir de resultados persistidos, sem treinar modelos."""

import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
CP = ROOT / "resultados/ciencias_natureza/checkpoint-6-2026-11-07"
TABLES = ROOT / "resultados/ciencias_natureza/checkpoint-5-2026-11-07/tabelas"
OUT = CP / "figuras"
OUT.mkdir(parents=True, exist_ok=True)
INPUTS = {}
LABELS = {
    "stacking": "Stacking",
    "svm": "SVM linear",
    "random_forest": "Random Forest",
    "knn": "KNN",
    "bagging": "Bagging",
    "pasting": "Pasting",
    "boosting": "Boosting",
    "baseline": "Média",
    "linear": "Linear",
    "ridge": "Ridge",
    "arvore": "Árvore",
}


def read(path):
    INPUTS[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path)


def table(name):
    return read(TABLES / f"{name}.csv")


def save(fig, name):
    for ax in fig.axes:
        ax.tick_params(labelsize=10)
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300)
    plt.close(fig)


for font in (ROOT / "tmp/fonts").glob("*.TTF"):
    font_manager.fontManager.addfont(font)
plt.rcParams.update(
    {
        "font.family": "Times New Roman",
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "legend.fontsize": 10,
        "svg.fonttype": "path",
    }
)
blue, orange = "#125b80", "#b04d15"

d = table("distribuicao_desenvolvimento")
fig, ax = plt.subplots(figsize=(6.3, 2.25), layout="constrained")
ax.bar(d.limite_inferior, d.n, width=25, align="edge", color=blue)
ax.set(xlabel="Nota de Ciências da Natureza (pontos)", ylabel="Participantes (mil)", xlim=(0, 1000))
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x / 1000:.0f}"))
ax.text(0.02, 0.92, "n = 2.153.941; zeros = 13.236", transform=ax.transAxes, va="top")
save(fig, "01_distribuicao")

cv = read(ROOT / "resultados/experimentos.csv")
cv = cv.query("row_type == 'summary' and variant == 'original'").sort_values("rmse")
fig, ax = plt.subplots(figsize=(6.3, 2.55), layout="constrained")
ax.errorbar(cv.rmse, np.arange(len(cv)), xerr=cv.rmse_std, fmt="o", color=blue, capsize=3)
ax.set(
    yticks=np.arange(len(cv)),
    yticklabels=[LABELS[m] for m in cv.model],
    xlabel="RMSE na validação (pontos); média ± DP",
    xlim=(75.5, 89),
)
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.2)
save(fig, "02_iniciais")

d = table("pca_variancia")
fig, ax = plt.subplots(figsize=(6.3, 2.3), layout="constrained")
for (model, fold), part in d.groupby(["model", "fold"]):
    ax.plot(
        part.component,
        part.cumulative_variance * 100,
        color=blue,
        alpha=0.6,
        label="Seis ajustes (curvas sobrepostas)" if model == "arvore" and fold == 0 else None,
    )
ax.axhline(80, color=orange, ls="--", label="Critério: 80%")
ax.axvline(45, color="black", ls=":", label="k = 45")
ax.set(
    xlabel="Número de componentes", ylabel="Variância acumulada (%)", xlim=(1, 235), ylim=(0, 101)
)
ax.legend(loc="lower right", frameon=False)
save(fig, "03_pca")

d = table("antes_depois")
fig, ax = plt.subplots(figsize=(6.3, 2.15), layout="constrained")
x = np.arange(len(d))
ax.plot(x, d.initial_rmse, "o", color=blue, ms=8, label="Antes")
ax.plot(x, d.selected_rmse, "x", color=orange, ms=8, label="Depois (receita escolhida)")
ax.set(xticks=x, xticklabels=[LABELS[m] for m in d.model], ylabel="RMSE médio (pontos)")
ax.legend(frameon=False, loc="lower right")
ax.grid(axis="y", alpha=0.2)
save(fig, "04_buscas")

d = table("curvas_resumo")
fig, axes = plt.subplots(3, 1, figsize=(6.3, 4.8), sharex=True, layout="constrained")
for ax, model in zip(axes, ["stacking", "svm", "random_forest"], strict=True):
    part = d[d.model == model].sort_values("fraction")
    for col, color, label, marker in [
        ("rmse_train", blue, "Treino", "o"),
        ("rmse", orange, "Validação", "s"),
    ]:
        x = part.n_train_mean.to_numpy() / 1e6
        y, sd = part[f"{col}_mean"].to_numpy(), part[f"{col}_std"].to_numpy()
        ax.plot(x, y, marker=marker, color=color, label=label, ms=4)
        ax.fill_between(x, y - sd, y + sd, color=color, alpha=0.17)
    ax.set(title=LABELS[model], ylabel="RMSE (pontos)")
    ax.grid(alpha=0.2)
axes[0].legend(frameon=False, ncol=2, loc="upper right")
axes[-1].set_xlabel("Participantes no treino de cada dobra (milhões)")
save(fig, "05_curvas")

p = read(
    ROOT
    / "resultados/ciencias_natureza/checkpoint-4-2026-11-07/avaliacao_final/previsoes_teste.csv"
)
assert len(p) == 538486 and p.previsao_stacking.notna().all()
y, pred = p.nota_observada.to_numpy(), p.previsao_stacking.to_numpy()
fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.8), layout="constrained")
h = axes[0].hexbin(y, pred, gridsize=45, mincnt=1, bins="log", cmap="viridis")
axes[0].plot([0, 1000], [0, 1000], "--", color=orange, lw=1.2, label="Identidade")
axes[0].set(xlabel="Nota observada", ylabel="Nota prevista", xlim=(0, 1000), ylim=(0, 1000))
axes[0].legend(frameon=False, loc="upper left")
axes[1].hexbin(pred, y - pred, gridsize=45, mincnt=1, cmap="viridis", norm=h.norm)
axes[1].axhline(0, color=orange, ls="--", lw=1.2)
axes[1].set(xlabel="Nota prevista", ylabel="Resíduo (observada - prevista)")
fig.colorbar(h, ax=axes, label="Participantes por célula", shrink=0.8, pad=0.02)
save(fig, "06_diagnostico_teste")

d = table("erros_grupos").query("model == 'stacking'")
fig, axes = plt.subplots(2, 1, figsize=(6.3, 3.5), layout="constrained")
for ax, group, categories, names in [
    (
        axes[0],
        "faixa_nota",
        ["[0,400)", "[400,500)", "[500,600)", "[600,700)", "[700,+inf)"],
        ["[0,400)", "[400,500)", "[500,600)", "[600,700)", "≥700"],
    ),
    (axes[1], "TP_ESCOLA", ["1", "2", "3"], ["Não respondeu", "Pública", "Privada"]),
]:
    part = d[d.group == group].set_index("category").loc[categories]
    ax.bar(np.arange(len(part)), part.rmse, color=blue, width=0.55)
    ticklabels = [
        label + "\nn=" + f"{int(n):,}".replace(",", ".")
        for label, n in zip(names, part.n, strict=True)
    ]
    ax.set(xticks=np.arange(len(part)), xticklabels=ticklabels, ylabel="RMSE (pontos)")
    for i, value in enumerate(part.rmse):
        ax.text(i, value + 3, f"{value:.2f}".replace(".", ","), ha="center", fontsize=10)
    ax.set_ylim(0, max(part.rmse) * 1.27)
    ax.set_title("Faixa da nota observada" if group == "faixa_nota" else "Tipo de escola informado")
save(fig, "07_grupos")
(CP / "entradas_figuras.json").write_text(json.dumps(INPUTS, indent=2) + "\n")
print("Sete figuras PNG/SVG geradas exclusivamente de resultados persistidos.")
