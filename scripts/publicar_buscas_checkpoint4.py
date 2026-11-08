"""Tabelas e figuras das buscas já validadas, anteriores ao teste final."""

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from enem_base.evidence import PROVENANCE_KEYS, read_run, seal_run
from enem_base.final_selection import load_frozen
from enem_base.provenance import runtime_metadata, sha256_file
from enem_base.study import load_study
from enem_base.tuning import MODELS

LABELS = {
    "svm": "SVM linear",
    "linear": "Regressão linear",
    "ridge": "Ridge",
    "random_forest": "Random Forest",
    "stacking": "Stacking",
}


def publish(config, root, output):
    frozen = load_frozen(config, root)
    if output.exists():
        raise FileExistsError("Publicação existente; preservar e indicar outra saída.")
    source = root / "congelamento"
    inputs = {str(source / "manifesto.json"): sha256_file(source / "manifesto.json")}
    table = pd.read_csv(source / "antes_depois_buscas.csv").set_index("model")
    rankings = []
    for name in MODELS:
        directory = root / "buscas" / name
        read_run(directory, frozen)
        ranks = pd.read_csv(directory / "comparacao_configuracoes.csv")
        best = ranks.iloc[0]
        for column in ("rmse_std", "mae_mean", "mae_std", "r2_mean", "r2_std"):
            table.loc[name, "search_" + column] = best[column]
        rankings.append(ranks)
        inputs[str(directory / "manifesto.json")] = sha256_file(directory / "manifesto.json")
    table = table.sort_values("selected_rmse")
    output.mkdir(parents=True)
    table.to_csv(output / "antes_depois.csv")
    pd.concat(rankings, ignore_index=True).to_csv(output / "todas_configuracoes.csv", index=False)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
            "axes.grid": True,
            "grid.alpha": 0.16,
        }
    )
    footer = (
        "Fonte: Inep, ENEM 2023 · desenvolvimento, n=2.153.941 · três dobras nacionais"
        "\n12 configurações por modelo; teste não utilizado. "
        "Melhorias pequenas não demonstram relevância prática."
    )

    def save(fig, stem):
        fig.get_layout_engine().set(rect=(0, 0.18, 1, 0.72))
        fig.text(0.01, 0.025, footer, fontsize=8)
        for extension in ("png", "svg"):
            fig.savefig(output / f"{stem}.{extension}", dpi=300, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
    y = np.arange(len(table))
    ax.errorbar(
        table.best_search_rmse,
        y,
        xerr=table.search_rmse_std,
        fmt="o",
        color="#087f8c",
        capsize=4,
        label="Melhor da busca ± DP entre dobras",
    )
    ax.scatter(
        table.initial_rmse,
        y,
        marker="x",
        s=60,
        color="#a65400",
        label="Configuração inicial",
        zorder=3,
    )
    ax.set(
        yticks=y,
        yticklabels=[LABELS[n] for n in table.index],
        xlabel="RMSE (pontos) · menor é melhor",
    )
    ax.invert_yaxis()
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.92),
        ncols=2,
        frameon=False,
        fontsize=9,
    )
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    fig.suptitle("Antes e depois das buscas — comparação nacional", fontsize=14)
    save(fig, "comparacao_antes_depois")

    fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
    bars = ax.barh(y, table.improvement, color="#087f8c")
    ax.set(
        yticks=y,
        yticklabels=[LABELS[n] for n in table.index],
        xlabel="RMSE inicial − menor RMSE da busca (pontos)",
        xlim=(0, max(table.improvement) * 1.4),
    )
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    ax.bar_label(bars, labels=[f"{v:.3g}".replace(".", ",") for v in table.improvement], padding=5)
    fig.suptitle("Magnitude das mudanças após a busca", fontsize=14)
    save(fig, "magnitude_melhorias")
    seal_run(
        output,
        {
            **runtime_metadata(),
            **{k: frozen[k] for k in PROVENANCE_KEYS},
            "status": "completed",
            "experiment_kind": "search_publication",
            "test_evaluated": False,
            "evaluated_set": "development_cv",
            "inputs": inputs,
            "figures": 2,
            "visual_validation_pending": True,
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    publish(load_study(args.study), args.checkpoint, args.output)
