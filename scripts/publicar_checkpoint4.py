"""Publicar métricas e gráficos do teste realmente executado, sem ajustar modelos."""

import argparse
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from enem_base.evidence import PROVENANCE_KEYS, read_run, seal_run
from enem_base.final_evaluation import validate_final_results
from enem_base.final_selection import load_frozen
from enem_base.frozen_curves import validate_curves
from enem_base.provenance import runtime_metadata, sha256_file
from enem_base.study import load_study

LABELS = {
    "stacking": "Stacking",
    "svm": "SVM linear",
    "random_forest": "Random Forest",
    "baseline": "Baseline (média)",
    "linear_reference": "Linear de referência",
    "academic_solution": "Solução acadêmica",
}
COLORS = {
    "stacking": "#087f8c",
    "svm": "#a65400",
    "random_forest": "#7b3a96",
    "baseline": "#888888",
    "linear_reference": "#3566a0",
    "academic_solution": "#c74545",
}


def summary_curves(rows):
    records = []
    for (model, fraction), group in rows.groupby(["model", "fraction"], sort=False):
        record = {"model": model, "fraction": fraction, "n_train_mean": group.n_train.mean()}
        for metric in ("rmse", "mae", "r2", "rmse_train", "mae_train", "r2_train", "gap_rmse"):
            record[metric + "_mean"] = group[metric].mean()
            record[metric + "_std"] = group[metric].std(ddof=0)
        records.append(record)
    return pd.DataFrame(records)


def publish(config, root, output):
    if output.exists():
        raise FileExistsError("Preservar a publicação anterior; indicar outra saída.")
    frozen = load_frozen(config, root)
    metrics = validate_final_results(config, root)
    curves, inputs = validate_curves(config, root)
    final = root / "avaliacao_final"
    manifest = read_run(final, frozen, development=False)
    predictions = pd.read_csv(final / "previsoes_teste.csv")
    groups = pd.read_csv(final / "erros_grupos.csv", dtype={"category": "string"})
    output.mkdir(parents=True)
    primary = frozen["primary_models"]
    summary = summary_curves(curves)
    summary.to_csv(output / "curvas_resumo.csv", index=False)
    curves.to_csv(output / "curvas_por_dobra.csv", index=False)
    metrics.to_csv(output / "comparacao_teste.csv", index=False)
    comparison = metrics.copy()
    for metric in ("rmse", "mae", "r2"):
        comparison[metric + "_cv_mean"] = comparison.model.map(
            {k: v[metric + "_mean"] for k, v in frozen["recipes"].items()}
        )
        comparison[metric + "_cv_std"] = comparison.model.map(
            {k: v[metric + "_std"] for k, v in frozen["recipes"].items()}
        )
    comparison.to_csv(output / "validacao_e_teste.csv", index=False)
    groups.to_csv(output / "erros_grupos.csv", index=False)
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
    population = f"{len(predictions):,}".replace(",", ".")
    footer = (
        f"Fonte: Inep, ENEM 2023 · teste reservado, n={population}"
        + " · configurações escolhidas apenas no desenvolvimento"
    )

    def save(fig, stem, note=footer, rect=(0, 0.12, 1, 0.8)):
        fig.get_layout_engine().set(rect=rect)
        fig.text(0.01, 0.02, note, fontsize=8)
        for extension in ("png", "svg"):
            fig.savefig(output / f"{stem}.{extension}", dpi=300, bbox_inches="tight")
        plt.close(fig)

    ordered = metrics.set_index("model").loc[
        primary + [m for m in metrics.model if m not in primary]
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 6), layout="constrained")
    for ax, metric, title in zip(
        axes, ("rmse", "mae", "r2"), ("RMSE (pontos) ↓", "MAE (pontos) ↓", "R² ↑"), strict=True
    ):
        bars = ax.barh(
            np.arange(len(ordered)), ordered[metric], color=[COLORS[m] for m in ordered.index]
        )
        ax.set(
            yticks=np.arange(len(ordered)),
            yticklabels=[LABELS[m] for m in ordered.index],
            xlabel=title,
        )
        ax.invert_yaxis()
        for bar, value in zip(bars, ordered[metric], strict=True):
            precision = 6 if metric == "r2" else 3
            ax.text(
                max(0, value) + ordered[metric].max() * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.{precision}f}".replace(".", ","),
                va="center",
                ha="left",
                fontsize=9,
            )
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
        ax.set_xlim(min(0, ordered[metric].min() * 1.2), ordered[metric].max() * 1.2)
    fig.suptitle("Desempenho no teste nacional — trio e referências", fontsize=15)
    save(fig, "comparacao_teste")

    fig, ax = plt.subplots(figsize=(9, 5.5), layout="constrained")
    x = np.arange(len(primary))
    selected = comparison.set_index("model").loc[primary]
    for offset, values, label, color in (
        (-0.18, selected.rmse_cv_mean, "Validação cruzada (média ± DP)", "#3566a0"),
        (0.18, selected.rmse, "Teste reservado", "#087f8c"),
    ):
        bars = ax.bar(
            x + offset,
            values,
            width=0.36,
            label=label,
            color=color,
            yerr=selected.rmse_cv_std if offset < 0 else None,
            capsize=4,
        )
        ax.bar_label(
            bars, labels=[f"{v:.3f}".replace(".", ",") for v in values], padding=6, fontsize=9
        )
    ax.set(
        xticks=x,
        xticklabels=[LABELS[m] for m in primary],
        ylabel="RMSE (pontos) · menor é melhor",
        ylim=(0, max(selected.rmse.max(), selected.rmse_cv_mean.max()) * 1.18),
    )
    ax.legend(loc="upper center", ncols=2, fontsize=9)
    fig.suptitle("Validação e teste das configurações congeladas", fontsize=14)
    save(
        fig,
        "validacao_versus_teste",
        footer + "\nDP entre três dobras; não representa intervalo de confiança.",
    )

    fig, axes = plt.subplots(
        1,
        len(frozen["curve_models"]),
        figsize=(14, 5.8),
        sharey=True,
        layout="constrained",
        squeeze=False,
    )
    for ax, model in zip(axes.flat, frozen["curve_models"], strict=True):
        rows = summary.loc[summary.model.eq(model)].sort_values("fraction")
        sizes = rows.n_train_mean.to_numpy() / 1000
        for metric, color, style in (("rmse_train", "#3566a0", "--"), ("rmse", "#bd3c38", "-")):
            mean, std = rows[metric + "_mean"].to_numpy(), rows[metric + "_std"].to_numpy()
            ax.plot(sizes, mean, style, marker="o", color=color)
            ax.fill_between(sizes, mean - std, mean + std, color=color, alpha=0.15)
        ax.set(title=LABELS[model], xlabel="Treino (milhares de participantes)", xticks=sizes)
        ax.tick_params(axis="x", rotation=30)
    axes[0, 0].set_ylabel("RMSE (pontos)")
    fig.suptitle("Curvas das configurações finais — antes de abrir o teste", fontsize=14)
    fig.legend(
        handles=[
            Line2D([], [], color="#3566a0", linestyle="--", label="Treino"),
            Line2D([], [], color="#bd3c38", label="Validação"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.93),
        ncols=2,
        frameon=False,
    )
    save(
        fig,
        "curvas_configuracoes_finais",
        "Fonte: Inep, ENEM 2023 · desenvolvimento, n=2.153.941"
        "\nFaixas: média ± DP de três dobras (não IC); "
        "mesmos subconjuntos cumulativos do Checkpoint 3.",
        rect=(0, 0.16, 1, 0.64),
    )

    observed = predictions.nota_observada.to_numpy()
    fig, axes = plt.subplots(
        1, 3, figsize=(15, 5.6), sharex=True, sharey=True, layout="constrained"
    )
    limit = max(observed.max(), *(predictions[f"previsao_{m}"].max() for m in primary)) * 1.03
    lower = min(0, *(predictions[f"previsao_{m}"].min() for m in primary))
    collections = []
    for ax, model in zip(axes, primary, strict=True):
        hexagons = ax.hexbin(
            observed,
            predictions[f"previsao_{model}"],
            gridsize=75,
            bins="log",
            mincnt=1,
            cmap="viridis",
            rasterized=True,
            extent=(lower, limit, lower, limit),
        )
        collections.append(hexagons)
        ax.plot(
            [lower, limit],
            [lower, limit],
            "--",
            color="#b53434",
            linewidth=1,
            label="Previsão perfeita",
        )
        ax.set(
            title=LABELS[model],
            xlabel="Nota observada (pontos)",
            xlim=(lower, limit),
            ylim=(lower, limit),
        )
        ax.legend(fontsize=8, loc="upper left")
    norm = LogNorm(vmin=1, vmax=max(float(h.get_array().max()) for h in collections))
    for ax, hexagons in zip(axes, collections, strict=True):
        hexagons.set_norm(norm)
        fig.colorbar(hexagons, ax=ax, label="Participantes por célula (log)", shrink=0.85)
    axes[0].set_ylabel("Nota prevista (pontos)")
    fig.suptitle("Notas observadas e previstas — todos os participantes do teste", fontsize=14)
    save(fig, "observado_versus_previsto")

    residuals = {m: observed - predictions[f"previsao_{m}"].to_numpy() for m in primary}
    bins = np.linspace(
        min(v.min() for v in residuals.values()), max(v.max() for v in residuals.values()), 101
    )
    fig, axes = plt.subplots(
        1, 3, figsize=(14, 5.5), sharex=True, sharey=True, layout="constrained"
    )
    for ax, model in zip(axes, primary, strict=True):
        ax.hist(residuals[model], bins=bins, color=COLORS[model], alpha=0.85, label="Participantes")
        ax.axvline(0, color="#222222", linestyle="--", linewidth=1, label="Erro zero")
        ax.set(title=LABELS[model], xlabel="Resíduo: observada − prevista (pontos)")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Número de participantes")
    fig.suptitle("Distribuição dos resíduos no teste nacional", fontsize=14)
    save(fig, "distribuicao_residuos")

    axis_labels = {
        "faixa_nota": "Faixa da nota observada (pontos)",
        "TP_ESCOLA": "Tipo de escola (código TP_ESCOLA)",
        "SG_UF_PROVA": "UF de aplicação da prova",
        "Q006": "Renda familiar (categoria Q006)",
    }
    group_titles = {
        "faixa_nota": "Erro no teste por faixa da nota observada",
        "TP_ESCOLA": "Erro no teste por tipo de escola (TP_ESCOLA)",
        "SG_UF_PROVA": "Erro no teste por UF de aplicação da prova",
        "Q006": "Erro no teste por renda familiar (Q006)",
    }
    for field, axis_label in axis_labels.items():
        subset = groups.loc[groups.group.eq(field) & groups.model.isin(primary)]
        categories = sorted(subset.category.unique())
        if field == "faixa_nota":
            categories = ["[0,400)", "[400,500)", "[500,600)", "[600,700)", "[700,+inf)"]
        fig, ax = plt.subplots(
            figsize=(12 if len(categories) > 10 else 9, 5.8), layout="constrained"
        )
        for model in primary:
            values = subset.loc[subset.model.eq(model)].set_index("category").reindex(categories)
            if values.rmse.isna().any():
                raise ValueError("Categorias de erro incompletas.")
            ax.plot(
                np.arange(len(categories)),
                values.rmse,
                marker="o",
                markersize=4,
                label=LABELS[model],
                color=COLORS[model],
            )
        counts = subset.loc[subset.model.eq(primary[0])].set_index("category").reindex(categories).n
        ticks = (
            [
                f"{c}\nn={format(int(n), ',').replace(',', '.')}"
                for c, n in zip(categories, counts, strict=True)
            ]
            if len(categories) <= 5
            else categories
        )
        ax.set(
            xticks=np.arange(len(categories)),
            xticklabels=ticks,
            xlabel=axis_label,
            ylabel="RMSE (pontos)",
        )
        ax.tick_params(axis="x", rotation=45 if len(categories) > 10 else 0)
        ax.legend(ncols=3, loc="upper center", fontsize=9)
        fig.suptitle(group_titles[field], fontsize=14)
        save(
            fig,
            "erros_" + field.lower(),
            footer + "\nGrupos observacionais; contagens e métricas completas em erros_grupos.csv. "
            "Não implica causalidade.",
            rect=(0, 0.18, 1, 0.72),
        )
    inputs[str(final / "manifesto.json")] = sha256_file(final / "manifesto.json")
    inputs[str(root / "congelamento" / "manifesto.json")] = sha256_file(
        root / "congelamento" / "manifesto.json"
    )
    seal_run(
        output,
        {
            **runtime_metadata(),
            **{k: frozen[k] for k in PROVENANCE_KEYS},
            "status": "completed",
            "test_evaluated": True,
            "evaluated_set": "test",
            "experiment_kind": "checkpoint4_publication",
            "inputs": inputs,
            "figures": len(list(output.glob("*.png"))),
            "visual_validation_pending": True,
            "primary_observed_winner": manifest["primary_observed_winner"],
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    publish(load_study(args.study), args.checkpoint, args.output)
