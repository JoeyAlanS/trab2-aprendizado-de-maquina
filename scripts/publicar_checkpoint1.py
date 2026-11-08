"""Validar as 21 avaliações e publicar apenas o checkpoint 1 concluído."""

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from enem_base.evidence import GROUP_FIELDS, comparison_rows
from enem_base.exports import export_experiments
from enem_base.modeling import estimator_spec, model_catalog
from enem_base.provenance import runtime_metadata, sha256_file, write_json
from enem_base.study import load_study
from enem_base.workflow import current_provenance

MODELS = ("svm", "knn", "bagging", "pasting", "random_forest", "boosting", "stacking")
LABELS = (
    "SVM linear",
    "KNN",
    "Bagging",
    "Pasting",
    "Random Forest",
    "Gradient Boosting",
    "Stacking",
)


def publish(config, root, output):
    if output.exists():
        raise FileExistsError("Publicação existente; preservar e escolher nova saída.")
    provenance = current_provenance(config)
    summaries, frames, band_rows, inputs = [], [], [], {}
    reference_folds = None
    reference_groups = None
    catalog = model_catalog(config)
    for name, label in zip(MODELS, LABELS, strict=True):
        path = root / name
        rows, manifest = comparison_rows(path, provenance)
        if (
            manifest["models"] != [name]
            or manifest["variant"] != "original"
            or manifest["features"] != config.features
            or manifest["parameters"][name] != estimator_spec(catalog[name])
            or not rows.test_evaluated.eq(False).all()
            or not np.isfinite(rows[["rmse", "mae", "r2", "elapsed_seconds"]]).all().all()
        ):
            raise ValueError(f"Rodada inválida ou diferente do catálogo registrado: {name}")
        folds = rows.set_index("fold")[["n_train", "n_evaluated"]].sort_index()
        if reference_folds is None:
            reference_folds = folds
        elif not folds.equals(reference_folds):
            raise ValueError(f"Os modelos não usam os mesmos tamanhos de dobras: {name}")
        row = {
            "model": name,
            "label": label,
            "n_development": provenance["n_development"],
            "n_splits": 3,
            "elapsed_seconds": float(rows.elapsed_seconds.sum()),
            "warning_count": sum(len(json.loads(x)) for x in rows.warnings_json),
        }
        stored = manifest["results"][0]
        for metric in ("rmse", "mae", "r2"):
            row[metric + "_mean"] = float(rows[metric].mean())
            row[metric + "_std"] = float(rows[metric].std(ddof=0))
            for suffix in ("_mean", "_std"):
                if not np.isclose(
                    row[metric + suffix], stored[metric + suffix], rtol=1e-10, atol=1e-10
                ):
                    raise ValueError(f"Resumo e dobras inconsistentes: {name}/{metric}")
        groups = pd.read_csv(path / "erros_grupos.csv")
        if set(groups.fold) != {0, 1, 2} or set(groups.model) != {name}:
            raise ValueError(f"Modelos/dobras inconsistentes nos grupos: {name}")
        counts = groups.set_index(["fold", "group", "category"]).n.sort_index()
        if not counts.index.is_unique:
            raise ValueError(f"Grupos duplicados: {name}")
        if reference_groups is None:
            reference_groups = counts
        elif not counts.equals(reference_groups):
            raise ValueError(f"Populações por faixa/grupo diferem entre modelos: {name}")
        for fold, group in groups.groupby("fold"):
            fold_row = rows.loc[rows.fold.eq(fold)].iloc[0]
            expected = fold_row.n_evaluated
            if set(group.group) != {"faixa_nota", *GROUP_FIELDS}:
                raise ValueError(f"Grupos ausentes: {name}, dobra {fold}")
            if not group.groupby("group").n.sum().eq(expected).all():
                raise ValueError(f"Contagens de grupos inconsistentes: {name}, dobra {fold}")
            for _, partitions in group.groupby("group"):
                pooled_rmse = np.sqrt(np.average(partitions.rmse**2, weights=partitions.n))
                pooled_mae = np.average(partitions.mae, weights=partitions.n)
                if not np.allclose(
                    [pooled_rmse, pooled_mae],
                    [fold_row.rmse, fold_row.mae],
                    rtol=1e-10,
                    atol=1e-10,
                ):
                    raise ValueError(f"Métricas dos grupos não recompõem a dobra: {name}/{fold}")
        for category, group in groups.loc[groups.group.eq("faixa_nota")].groupby("category"):
            band_rows.append(
                {
                    "model": name,
                    "label": label,
                    "score_band": category,
                    "n": int(group.n.sum()),
                    "rmse_pooled": float(np.sqrt(np.average(group.rmse**2, weights=group.n))),
                    "mae_pooled": float(np.average(group.mae, weights=group.n)),
                    "mean_residual": float(np.average(group.mean_residual, weights=group.n)),
                }
            )
        summaries.append(row)
        frames.append(rows)
        inputs[name] = sha256_file(path / "manifesto.json")
    if sum(len(rows) for rows in frames) != 21:
        raise ValueError("Checkpoint exige sete modelos e 21 avaliações por dobra.")
    export_experiments([root / name for name in MODELS], output)
    summary, bands = pd.DataFrame(summaries), pd.DataFrame(band_rows)
    summary.to_csv(output / "comparacao_sete_modelos.csv", index=False)
    bands.to_csv(output / "erros_por_faixa.csv", index=False)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, stem):
        fig.get_layout_engine().set(rect=(0, 0.09, 1, 0.91))
        fig.text(
            0.01,
            0.015,
            "Fonte: Inep, ENEM 2023 · desenvolvimento nacional · n=2.153.941 · teste reservado",
            fontsize=8,
        )
        for extension in ("png", "svg"):
            fig.savefig(output / f"{stem}.{extension}", dpi=220, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5), layout="constrained")
    ax.barh(summary.label, summary.rmse_mean, xerr=summary.rmse_std, color="#087f8c", capsize=4)
    ax.invert_yaxis()
    ax.set(
        xlabel="RMSE (pontos): média ± DP nas três dobras",
        ylabel="Algoritmo",
        title="Checkpoint 1 — sete algoritmos",
    )
    for index, row in summary.iterrows():
        ax.text(row.rmse_mean + 0.5, index, f"{row.rmse_mean:.3f}", va="center", fontsize=9)
    ax.set_xlim(0, summary.rmse_mean.max() * 1.13)
    save(fig, "comparacao_rmse")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), layout="constrained")
    for metric, label, ax in zip(("mae", "r2"), ("MAE (pontos)", "R²"), axes, strict=True):
        ax.barh(
            summary.label,
            summary[metric + "_mean"],
            xerr=summary[metric + "_std"],
            capsize=4,
            color="#087f8c",
        )
        ax.invert_yaxis()
        ax.set(xlabel=label, ylabel="Algoritmo", title="Média ± DP nas três dobras")
    save(fig, "metricas_complementares")

    fig, ax = plt.subplots(figsize=(10, 5.5), layout="constrained")
    for _, group in bands.groupby("model", sort=False):
        ax.plot(group.score_band, group.rmse_pooled, marker="o", label=group.label.iloc[0])
    sizes = bands.groupby("score_band").n.first()
    ax.set_xticks(
        range(len(sizes)),
        [f"{band}\nn=" + f"{n:,}".replace(",", ".") for band, n in sizes.items()],
    )
    ax.set(
        xlabel="Faixa da nota observada",
        ylabel="RMSE fora da dobra (pontos)",
        title="Erros no desenvolvimento — todas as validações reunidas",
    )
    ax.legend(loc="upper center", ncols=2, fontsize=8)
    save(fig, "erros_por_faixa")
    result = {
        **runtime_metadata(),
        **provenance,
        "publisher_sha256": sha256_file(Path(__file__)),
        "checkpoint": 1,
        "status": "completed",
        "validated_folds": 21,
        "std_ddof": 0,
        "inputs": inputs,
        "results": summaries,
        "next_checkpoint_started": False,
        "assets": {
            p.name: sha256_file(p)
            for p in output.iterdir()
            if p.is_file() and p.name != "checkpoint_validado.json"
        },
    }
    write_json(output / "checkpoint_validado.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = publish(load_study(args.study), args.runs, args.output)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
