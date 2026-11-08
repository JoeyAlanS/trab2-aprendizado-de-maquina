"""Publicar as curvas congeladas antes da abertura do teste final."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from publicar_checkpoint4 import COLORS, LABELS, summary_curves

from enem_base.evidence import PROVENANCE_KEYS, seal_run
from enem_base.final_selection import load_frozen
from enem_base.frozen_curves import validate_curves
from enem_base.provenance import runtime_metadata
from enem_base.study import load_study


def publish(config, root, output):
    if output.exists():
        raise FileExistsError("Preservar a publicação existente; indicar outra saída.")
    frozen = load_frozen(config, root)
    rows, inputs = validate_curves(config, root)
    summary = summary_curves(rows)
    output.mkdir(parents=True)
    rows.to_csv(output / "curvas_por_dobra.csv", index=False)
    summary.to_csv(output / "curvas_resumo.csv", index=False)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.16,
            "svg.fonttype": "none",
        }
    )
    footer = (
        "Fonte: Inep, ENEM 2023 · desenvolvimento, n=2.153.941 · teste reservado"
        "\nConfigurações congeladas após as buscas · faixas: média ± DP de três dobras (não IC)"
    )

    def save(fig, stem, rect):
        fig.get_layout_engine().set(rect=rect)
        fig.text(0.01, 0.02, footer, fontsize=8)
        for ext in ("png", "svg"):
            fig.savefig(output / f"{stem}.{ext}", dpi=300, bbox_inches="tight")
        plt.close(fig)

    fig, axes = plt.subplots(
        1,
        len(frozen["curve_models"]),
        figsize=(14, 5.8),
        sharey=True,
        layout="constrained",
        squeeze=False,
    )
    for ax, label in zip(axes.flat, frozen["curve_models"], strict=True):
        table = summary.loc[summary.model.eq(label)].sort_values("fraction")
        x = table.n_train_mean.to_numpy() / 1000
        for metric, color, style in (("rmse_train", "#2166ac", "--"), ("rmse", "#b2182b", "-")):
            mean, std = table[metric + "_mean"].to_numpy(), table[metric + "_std"].to_numpy()
            ax.plot(x, mean, style, marker="o", color=color)
            ax.fill_between(x, mean - std, mean + std, color=color, alpha=0.15)
        ax.set(
            title=LABELS[label],
            xlabel="Treino (milhares de participantes)",
            xticks=x,
            xticklabels=[f"{v:.0f}" for v in x],
        )
        ax.tick_params(axis="x", rotation=30)
    axes[0, 0].set_ylabel("RMSE (pontos) · menor é melhor")
    fig.suptitle("Curvas de aprendizado das configurações finais", fontsize=15)
    fig.legend(
        handles=[
            Line2D([], [], color="#2166ac", linestyle="--", label="Treino"),
            Line2D([], [], color="#b2182b", label="Validação"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.93),
        ncols=2,
        frameon=False,
    )
    save(fig, "curvas_rmse", (0, 0.15, 1, 0.66))
    fig, ax = plt.subplots(figsize=(10, 5.8), layout="constrained")
    for label in frozen["curve_models"]:
        table = summary.loc[summary.model.eq(label)].sort_values("fraction")
        x = table.fraction.to_numpy() * 100
        mean, std = table.gap_rmse_mean.to_numpy(), table.gap_rmse_std.to_numpy()
        ax.plot(x, mean, marker="o", color=COLORS[label], label=LABELS[label])
        ax.fill_between(x, mean - std, mean + std, color=COLORS[label], alpha=0.12)
    ax.axhline(0, color="#555555", linestyle="--", linewidth=1)
    ax.set(
        xlabel="Fração do treino da dobra (%)",
        ylabel="RMSE validação − RMSE treino (pontos)",
        xticks=[10, 25, 50, 75, 100],
    )
    ax.legend(frameon=False)
    fig.suptitle("Diferença entre treino e validação após as buscas", fontsize=14)
    save(fig, "lacuna_generalizacao", (0, 0.15, 1, 0.74))
    seal_run(
        output,
        {
            **runtime_metadata(),
            **{k: frozen[k] for k in PROVENANCE_KEYS},
            "status": "completed",
            "experiment_kind": "frozen_curves_publication",
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
