"""Conferir os 45 pontos reais e publicar as curvas do trio selecionado."""

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from enem_base.evidence import comparison_rows, read_run, seal_run
from enem_base.learning_curves import _point_context, read_point, validate_protocol
from enem_base.provenance import runtime_metadata, sha256_file, verify_sha256, write_json
from enem_base.selection import LABELS
from enem_base.study import load_study

METRICS = ("rmse", "mae", "r2", "rmse_train", "mae_train", "r2_train", "gap_rmse")
COLORS = {"stacking": "#087f8c", "svm": "#a65400", "random_forest": "#7b3a96"}


def validate_points(config, selection_path, root, checkpoint1):
    protocol = validate_protocol(config, selection_path, root)
    tables, inputs, comparisons = [], {}, []
    for name in protocol["selected_models"]:
        directory = root / name
        manifest = read_run(directory, protocol)
        if (
            manifest.get("experiment_kind") != "selected_learning_curves"
            or manifest.get("model") != name
            or manifest.get("completed_points") != 15
            or manifest.get("protocol_sha256") != sha256_file(root / "protocolo.json")
            or manifest.get("actual_parameters") != protocol["actual_parameters"][name]
        ):
            raise ValueError(f"Manifesto de curva incompatível: {name}")
        for section in ("point_assets", "fit_assets"):
            for relative, expected in manifest[section].items():
                asset = (directory / relative).resolve()
                if not asset.is_relative_to(directory.resolve()):
                    raise ValueError("Caminho de artefato fora da execução.")
                verify_sha256(asset, expected, "Artefato local alterado")
        rows = []
        for point in protocol["points"]:
            context = _point_context(root, name, point, protocol)
            path = directory / "pontos" / f"{point['key']}.json"
            saved = read_point(path, context)
            row = saved["record"]
            if (
                any(row[k] != v for k, v in point.items())
                or row["model"] != name
                or row["test_evaluated"] is not False
                or saved["fit"]["context"] != context
                or row["warning_count"] != len(json.loads(row["warnings_json"]))
            ):
                raise ValueError("Registro diverge de seu contexto.")
            fit_path = directory / "modelos_ajustados" / f"{point['key']}.pkl"
            verify_sha256(fit_path, saved["fit"]["sha256"], "Modelo ajustado alterado")
            rows.append(row)
        table = pd.DataFrame(rows)
        stored = pd.read_csv(directory / "curvas.csv")
        pd.testing.assert_frame_equal(table, stored, check_dtype=False, rtol=1e-12, atol=1e-12)
        numeric = table[[*METRICS, "fit_seconds", "score_seconds", "elapsed_seconds"]]
        if (
            not np.isfinite(numeric).all().all()
            or (table[["rmse", "mae", "rmse_train", "mae_train", "elapsed_seconds"]] < 0)
            .any()
            .any()
            or (table[["r2", "r2_train"]] > 1).any().any()
            or not np.allclose(table.gap_rmse, table.rmse - table.rmse_train, atol=1e-12)
        ):
            raise ValueError("Métricas inválidas ou lacunas inconsistentes.")
        original, reference = comparison_rows(checkpoint1 / name, protocol)
        if reference["parameters"][name] != protocol["reference_parameters"][name]:
            raise ValueError("Configuração de referência difere do Checkpoint 1.")
        full = table.loc[table.fraction.eq(1)].set_index("fold")
        original = original.set_index("fold")
        for fold in range(3):
            row = {"model": name, "fold": fold}
            for metric in ("rmse", "mae", "r2"):
                difference = float(full.loc[fold, metric] - original.loc[fold, metric])
                row[metric + "_checkpoint1"] = float(original.loc[fold, metric])
                row[metric + "_curve_100"] = float(full.loc[fold, metric])
                row[metric + "_difference"] = difference
                if abs(difference) > 1e-8:
                    raise ValueError(f"Ponto em 100% não reproduz CP1: {name}/{fold}/{metric}")
            comparisons.append(row)
        inputs[str(directory / "manifesto.json")] = sha256_file(directory / "manifesto.json")
        inputs[str(checkpoint1 / name / "manifesto.json")] = sha256_file(
            checkpoint1 / name / "manifesto.json"
        )
        tables.append(table)
    result = pd.concat(tables, ignore_index=True)
    if len(result) != 45 or result.duplicated(["model", "fold", "fraction"]).any():
        raise ValueError("São necessários 45 pontos distintos.")
    # Assegurar igualdade de composição, não apenas tamanhos iguais.
    group = result.groupby(["fold", "fraction"])
    if (
        not group[["train_ids_sha256", "validation_ids_sha256", "n_train", "n_validation"]]
        .nunique()
        .eq(1)
        .all()
        .all()
    ):
        raise ValueError("Os modelos não utilizaram os mesmos participantes.")
    return protocol, result, pd.DataFrame(comparisons), inputs


def summarize(rows):
    records = []
    for (model, fraction), group in rows.groupby(["model", "fraction"], sort=False):
        if set(group.fold) != {0, 1, 2}:
            raise ValueError("Resumo exige as três dobras.")
        record = {
            "model": model,
            "label": LABELS[model],
            "fraction": fraction,
            "n_train_mean": float(group.n_train.mean()),
            "n_train_min": int(group.n_train.min()),
            "n_train_max": int(group.n_train.max()),
            "elapsed_seconds": float(group.elapsed_seconds.sum()),
            "warning_count": int(group.warning_count.sum()),
        }
        for metric in METRICS:
            record[metric + "_mean"] = float(group[metric].mean())
            record[metric + "_std"] = float(group[metric].std(ddof=0))
        records.append(record)
    return pd.DataFrame(records)


def plot_curves(summary, models, output, n_development):
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
            "axes.grid": True,
            "grid.alpha": 0.18,
        }
    )
    population = f"{n_development:,}".replace(",", ".")
    footer = (
        f"Fonte: Inep, ENEM 2023 · desenvolvimento, n={population} · teste reservado\n"
        "Faixas: média ± DP de três dobras (não IC) · configurações iniciais do Checkpoint 2"
    )

    def save(fig, stem, rect):
        fig.get_layout_engine().set(rect=rect)
        fig.text(0.01, 0.015, footer, fontsize=8)
        for extension in ("png", "svg"):
            fig.savefig(output / f"{stem}.{extension}", dpi=300, bbox_inches="tight")
        plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 5.6), sharey=True, layout="constrained")
    for ax, model in zip(axes, models, strict=True):
        rows = summary.loc[summary.model.eq(model)].sort_values("fraction")
        x = rows.n_train_mean.to_numpy() / 1000
        for metric, color, style in (("rmse_train", "#2166ac", "--"), ("rmse", "#b2182b", "-")):
            mean, std = rows[metric + "_mean"].to_numpy(), rows[metric + "_std"].to_numpy()
            ax.plot(x, mean, style, marker="o", color=color, linewidth=1.8, markersize=4)
            ax.fill_between(x, mean - std, mean + std, color=color, alpha=0.14)
        ax.set(title=LABELS[model], xlabel="Treino (milhares de participantes)")
        ax.set_xticks(x, [f"{v:,.0f}".replace(",", ".") for v in x], rotation=30)
    axes[0].set_ylabel("RMSE (pontos) · menor é melhor")
    fig.suptitle("Curvas de aprendizado — treino e validação", y=0.98, fontsize=15)
    fig.legend(
        handles=[
            Line2D([], [], color="#2166ac", linestyle="--", marker="o", label="Treino"),
            Line2D([], [], color="#b2182b", marker="o", label="Validação"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.93),
        ncols=2,
        frameon=False,
    )
    save(fig, "curvas_aprendizado_rmse", (0, 0.15, 1, 0.66))

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 5.6), layout="constrained")
    for ax, metric, label in zip(
        axes, ("rmse", "mae", "r2"), ("RMSE (pontos) ↓", "MAE (pontos) ↓", "R² ↑"), strict=True
    ):
        for model in models:
            rows = summary.loc[summary.model.eq(model)].sort_values("fraction")
            x = rows.fraction.to_numpy() * 100
            mean, std = rows[metric + "_mean"].to_numpy(), rows[metric + "_std"].to_numpy()
            ax.plot(x, mean, marker="o", color=COLORS[model], linewidth=1.8, markersize=4)
            ax.fill_between(x, mean - std, mean + std, color=COLORS[model], alpha=0.12)
        ax.set(xlabel="Fração do treino da dobra (%)", ylabel=label, xticks=x)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.3f}".replace(".", ",")))
    fig.suptitle("Comparação dos três modelos na validação", y=0.98, fontsize=15)
    fig.legend(
        handles=[Line2D([], [], color=COLORS[m], marker="o", label=LABELS[m]) for m in models],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.93),
        ncols=3,
        frameon=False,
    )
    save(fig, "comparacao_validacao", (0, 0.15, 1, 0.66))

    fig, ax = plt.subplots(figsize=(9.5, 5.8), layout="constrained")
    for model in models:
        rows = summary.loc[summary.model.eq(model)].sort_values("fraction")
        x = rows.fraction.to_numpy() * 100
        mean, std = rows.gap_rmse_mean.to_numpy(), rows.gap_rmse_std.to_numpy()
        ax.plot(x, mean, marker="o", color=COLORS[model], label=LABELS[model])
        ax.fill_between(x, mean - std, mean + std, color=COLORS[model], alpha=0.12)
    ax.axhline(0, color="#555555", linestyle="--", linewidth=0.9)
    ax.set(
        xlabel="Fração do treino da dobra (%)",
        ylabel="RMSE validação − RMSE treino (pontos)",
        title="Diferença entre treino e validação",
        xticks=x,
    )
    ax.legend(loc="best", frameon=True)
    save(fig, "lacuna_generalizacao", (0, 0.16, 1, 0.8))


def publish(config, selection, root, checkpoint1, output):
    if output.exists():
        raise FileExistsError("Publicação existente; preservar e escolher outra saída.")
    protocol, rows, comparisons, inputs = validate_points(config, selection, root, checkpoint1)
    summary = summarize(rows)
    changes = []
    for name in protocol["selected_models"]:
        points = summary.loc[summary.model.eq(name)].set_index("fraction")
        changes.append(
            {
                "model": name,
                "label": LABELS[name],
                "rmse_reduction_10_to_100": float(
                    points.loc[0.1, "rmse_mean"] - points.loc[1, "rmse_mean"]
                ),
                "rmse_reduction_75_to_100": float(
                    points.loc[0.75, "rmse_mean"] - points.loc[1, "rmse_mean"]
                ),
                "gap_10": float(points.loc[0.1, "gap_rmse_mean"]),
                "gap_100": float(points.loc[1, "gap_rmse_mean"]),
                "fit_and_score_seconds": float(points.elapsed_seconds.sum()),
            }
        )
    output.mkdir(parents=True)
    rows.to_csv(output / "curvas_por_dobra.csv", index=False)
    summary.to_csv(output / "curvas_resumo.csv", index=False)
    comparisons.to_csv(output / "reproducao_checkpoint1.csv", index=False)
    pd.DataFrame(changes).to_csv(output / "evolucao_modelos.csv", index=False)
    plot_curves(summary, protocol["selected_models"], output, protocol["n_development"])
    write_json(
        output / "validacao_numerica.json",
        {
            "status": "passed",
            "actual_points": len(rows),
            "models": protocol["selected_models"],
            "same_train_and_validation_ids": True,
            "validated_source_manifests": inputs,
            "all_full_training_points_match_checkpoint1": True,
            "full_training_metric_absolute_tolerance": 1e-8,
            "max_full_training_metric_difference": float(
                comparisons[[m + "_difference" for m in ("rmse", "mae", "r2")]]
                .abs()
                .to_numpy()
                .max()
            ),
            "warnings": int(rows.warning_count.sum()),
            "test_evaluated": False,
            "hyperparameter_search_completed": False,
            "std_ddof": 0,
        },
    )
    manifest = {
        **runtime_metadata(),
        **{
            k: protocol[k]
            for k in (
                "source_sha256",
                "splits_sha256",
                "study_sha256",
                "dictionary_sha256",
                "target",
                "n_development",
                "test_evaluated",
            )
        },
        "status": "completed",
        "checkpoint": 3,
        "experiment_kind": "learning_curve_publication",
        "evaluated_set": "development_cv",
        "models": protocol["selected_models"],
        "validated_points": len(rows),
        "protocol_sha256": sha256_file(root / "protocolo.json"),
        "inputs": inputs,
        "visual_validation_pending": True,
        "publisher_sha256": sha256_file(Path(__file__)),
    }
    seal_run(output, manifest)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("study", "selection", "root", "checkpoint1", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    table = publish(
        load_study(args.study), args.selection, args.root, args.checkpoint1, args.output
    )
    print(
        table[["model", "fraction", "rmse_train_mean", "rmse_mean", "gap_rmse_mean"]].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
