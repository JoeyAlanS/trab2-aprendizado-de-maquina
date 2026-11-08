"""Checkpoint 2: seleção rastreável entre os sete algoritmos do Checkpoint 1.

Reutiliza métricas reais por dobra. Não ajusta modelos, não executa buscas e não
carrega alvos ou preditores do teste. Referências externas ao escopo não entram
na seleção solicitada.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from enem_base.evidence import PROVENANCE_KEYS, comparison_rows, read_run, seal_run
from enem_base.modeling import estimator_spec, model_catalog
from enem_base.provenance import runtime_metadata, sha256_file, verify_sha256, write_json
from enem_base.study import StudyConfig
from enem_base.workflow import current_provenance

LABELS = {
    "svm": "SVM linear",
    "knn": "KNN",
    "bagging": "Bagging",
    "pasting": "Pasting",
    "random_forest": "Random Forest",
    "boosting": "Gradient Boosting",
    "stacking": "Stacking",
}
REFERENCE_LABELS = {
    "baseline": "Média (baseline)",
    "linear": "Regressão linear",
    "ridge": "Ridge",
    "arvore": "Árvore de decisão",
}
ORDER = ["rmse_mean", "mae_mean", "r2_mean", "model"]
ASCENDING = [True, True, False, True]
POLICY = {
    "scope": "seven_algorithms_from_checkpoint_1",
    "eligible_models": list(LABELS),
    "primary_metric": "rmse_mean",
    "direction": "minimize",
    "exact_tie_breakers": ["mae_mean ascending", "r2_mean descending", "model ascending"],
    "round_before_ranking": False,
    "n_selected": 3,
    "std_ddof": 0,
    "timing_used_for_selection": False,
    "statistical_significance_test_performed": False,
}


def _summary(rows, name, label):
    result = {
        "model": name,
        "label": label,
        "n_splits": len(rows),
        "n_development": int(rows.n_evaluated.sum()),
        "elapsed_seconds": float(rows.elapsed_seconds.sum()),
        "warning_count": sum(len(json.loads(w)) for w in rows.warnings_json),
    }
    if not np.isfinite(rows[["rmse", "mae", "r2", "elapsed_seconds"]]).all().all():
        raise ValueError(f"Métricas não finitas: {name}")
    for metric in ("rmse", "mae", "r2"):
        result[metric + "_mean"] = float(rows[metric].mean())
        result[metric + "_std"] = float(rows[metric].std(ddof=0))
    return result


def _validated_checkpoint(config, checkpoint, provenance):
    marker = json.loads((checkpoint / "checkpoint.json").read_text(encoding="utf-8"))
    if (
        marker.get("status") != "completed"
        or marker.get("checkpoint") != 1
        or marker.get("validated_folds") != 21
        or marker.get("test_evaluated") is not False
        or set(marker.get("models", [])) != set(LABELS)
    ):
        raise ValueError("O Checkpoint 1 precisa estar concluído e validado.")
    publication = checkpoint / Path(marker["publication"]).name
    verify_sha256(
        publication / "checkpoint_validado.json",
        marker["publication_sha256"],
        "Publicação do Checkpoint 1 alterada",
    )
    verify_sha256(
        checkpoint / "verificacao_final.json",
        marker["validation_sha256"],
        "Validação do Checkpoint 1 alterada",
    )
    validation = json.loads((checkpoint / "verificacao_final.json").read_text(encoding="utf-8"))
    published = json.loads((publication / "checkpoint_validado.json").read_text(encoding="utf-8"))
    if (
        validation.get("status") != "passed"
        or published.get("status") != "completed"
        or published.get("test_evaluated") is not False
        or any(published.get(k) != provenance[k] for k in PROVENANCE_KEYS)
    ):
        raise ValueError("Validação ou proveniência do Checkpoint 1 incompatível.")
    for name, digest in published["assets"].items():
        if Path(name).name != name:
            raise ValueError("Caminho inválido na publicação.")
        verify_sha256(publication / name, digest, "Artefato do Checkpoint 1 alterado")

    table = pd.read_csv(publication / "comparacao_sete_modelos.csv").set_index("model")
    if len(table) != 7 or not table.index.is_unique or set(table.index) != set(LABELS):
        raise ValueError("A comparação publicada deve conter exatamente os sete algoritmos.")
    catalog, summaries, folds, inputs = model_catalog(config), [], [], {}
    sizes = None
    for name, label in LABELS.items():
        path = checkpoint / name
        verify_sha256(path / "manifesto.json", published["inputs"][name], "Modelo alterado")
        rows, manifest = comparison_rows(path, provenance)
        specification = estimator_spec(catalog[name])
        if (
            manifest["models"] != [name]
            or manifest["variant"] != "original"
            or manifest["features"] != config.features
            or manifest["parameters"][name] != specification
            or not rows.test_evaluated.eq(False).all()
            or any(json.loads(p) != specification for p in rows.parameters_json)
        ):
            raise ValueError(f"Configuração incompatível com a comparação registrada: {name}")
        counts = rows.set_index("fold")[["n_train", "n_evaluated"]].sort_index()
        if sizes is not None and not counts.equals(sizes):
            raise ValueError("Os algoritmos devem usar os mesmos tamanhos de dobras.")
        sizes = counts
        summary = _summary(rows, name, label)
        for key, value in summary.items():
            if isinstance(value, (int, float)) and not np.isclose(
                value, table.loc[name, key], rtol=1e-12, atol=1e-12
            ):
                raise ValueError(f"Resumo publicado difere das dobras: {name}/{key}")
        summaries.append(summary)
        folds.append(rows[["model", "fold", "rmse", "mae", "r2", "n_train", "n_evaluated"]])
        inputs[str(path / "manifesto.json")] = sha256_file(path / "manifesto.json")
    inputs[str(checkpoint / "checkpoint.json")] = sha256_file(checkpoint / "checkpoint.json")
    inputs[str(publication / "checkpoint_validado.json")] = marker["publication_sha256"]
    return pd.DataFrame(summaries), pd.concat(folds, ignore_index=True), inputs


def select_checkpoint2(
    config: StudyConfig, checkpoint: Path, output: Path, references: Path | None = None
) -> dict:
    if output.exists():
        raise FileExistsError("Seleção existente; preservar e escolher outra saída.")
    provenance = current_provenance(config)
    summary, folds, inputs = _validated_checkpoint(config, checkpoint, provenance)
    ranking = summary.sort_values(ORDER, ascending=ASCENDING).reset_index(drop=True)
    ranking.insert(0, "rank", np.arange(1, len(ranking) + 1))
    ranking["selected"] = ranking["rank"].le(3)
    ranking["rmse_gap_to_best"] = ranking.rmse_mean - ranking.rmse_mean.iloc[0]
    selected = ranking.head(3).model.tolist()
    metrics_top = {
        metric: summary.sort_values(metric + "_mean", ascending=metric != "r2")
        .head(3)
        .model.tolist()
        for metric in ("rmse", "mae", "r2")
    }
    ranked_folds, top_by_fold = [], {}
    for fold, rows in folds.groupby("fold", sort=True):
        rows = rows.sort_values(["rmse", "mae", "r2", "model"], ascending=ASCENDING).copy()
        rows["rank_in_fold"] = np.arange(1, len(rows) + 1)
        ranked_folds.append(rows)
        top_by_fold[str(int(fold))] = rows.head(3).model.tolist()
    fourth = ranking.iloc[3]
    boundary = folds.loc[folds.model.eq(fourth.model), ["fold", "rmse"]].rename(
        columns={"rmse": "rmse_best_excluded"}
    )
    differences = folds.loc[folds.model.isin(selected)].merge(boundary, on="fold", validate="m:1")
    differences["best_excluded_model"] = fourth.model
    differences["rmse_advantage_over_best_excluded"] = (
        differences.rmse_best_excluded - differences.rmse
    )

    reference_summary = pd.DataFrame()
    if references is not None:
        reference_rows, reference_manifest = comparison_rows(references, provenance)
        if reference_manifest["variant"] != "original" or set(reference_rows.model) != set(
            REFERENCE_LABELS
        ):
            raise ValueError("As referências devem ser baseline, linear, Ridge e árvore originais.")
        reference_summary = pd.DataFrame(
            [_summary(g, n, REFERENCE_LABELS[n]) for n, g in reference_rows.groupby("model")]
        )
        inputs[str(references / "manifesto.json")] = sha256_file(references / "manifesto.json")

    output.mkdir(parents=True)
    manifest = {
        **runtime_metadata(),
        **provenance,
        "checkpoint": 2,
        "status": "running",
        "experiment_kind": "model_selection",
        "evaluated_set": "development_cv",
        "policy": POLICY,
        "inputs": inputs,
        "n_models_compared": 7,
        "n_folds_verified": len(folds),
        "trained_new_models": False,
        "hyperparameter_search_completed": False,
        "final_solution_selected": False,
        "next_checkpoint_started": False,
    }
    write_json(output / "manifesto.json", manifest)
    try:
        ranking.to_csv(output / "ranking_sete_modelos.csv", index=False)
        ranking.head(3).to_csv(output / "tres_selecionados.csv", index=False)
        pd.concat(ranked_folds, ignore_index=True).to_csv(
            output / "ranking_por_dobra.csv", index=False
        )
        differences.to_csv(output / "margens_por_dobra.csv", index=False)
        catalog = model_catalog(config)
        selection = {
            **provenance,
            "policy": POLICY,
            "selected_models": selected,
            "features": config.features,
            "variant": "original",
            "parameters": {name: estimator_spec(catalog[name]) for name in selected},
            "results": ranking.head(3).to_dict("records"),
            "configuration_stage": "initial_comparison_before_hyperparameter_search",
            "top_three_by_metric": metrics_top,
            "top_three_by_fold": top_by_fold,
            "same_order_in_all_folds": all(v == selected for v in top_by_fold.values()),
            "best_excluded_model": fourth.model,
            "cutoff_gap_rmse": float(fourth.rmse_mean - ranking.iloc[2].rmse_mean),
        }
        write_json(output / "selecionados.json", selection)
        if not reference_summary.empty:
            reference_summary.to_csv(output / "referencias_fora_do_escopo.csv", index=False)
            expanded = pd.concat([summary, reference_summary], ignore_index=True)
            expanded = expanded.loc[expanded.model.ne("baseline")].sort_values(
                ORDER, ascending=ASCENDING
            )
            expanded.insert(0, "rank_expanded_catalog", np.arange(1, len(expanded) + 1))
            expanded["eligible_in_checkpoint2"] = expanded.model.isin(LABELS)
            expanded.to_csv(output / "diagnostico_catalogo_ampliado.csv", index=False)
            manifest["expanded_catalog_diagnostic_top3"] = expanded.head(3).model.tolist()
        _plot_selection(ranking, folds, output, provenance["n_development"])
        manifest.update(status="completed", selected_models=selected, selection=selection)
        seal_run(output, manifest)
    except Exception as error:
        manifest.update(status="failed", error_type=type(error).__name__, error=str(error))
        write_json(output / "manifesto.json", manifest)
        raise
    return manifest


def load_selection(config: StudyConfig, path: Path) -> dict:
    """Contrato para as próximas etapas: verificar e usar o trio já selecionado."""
    manifest = read_run(path, current_provenance(config))
    selection = json.loads((path / "selecionados.json").read_text(encoding="utf-8"))
    ranking = pd.read_csv(path / "ranking_sete_modelos.csv")
    expected = ranking.sort_values(ORDER, ascending=ASCENDING).head(3).model.tolist()
    if (
        manifest.get("experiment_kind") != "model_selection"
        or manifest.get("checkpoint") != 2
        or selection.get("policy") != POLICY
        or manifest.get("policy") != POLICY
        or len(ranking) != 7
        or set(ranking.model) != set(LABELS)
        or selection.get("selected_models") != expected
        or manifest.get("selected_models") != expected
        or selection.get("test_evaluated") is not False
        or selection.get("features") != config.features
        or selection.get("variant") != "original"
        or any(selection.get(k) != manifest[k] for k in PROVENANCE_KEYS)
    ):
        raise ValueError("Contrato de seleção inconsistente.")
    for name in expected:
        if selection["parameters"][name] != estimator_spec(model_catalog(config)[name]):
            raise ValueError(f"Configuração inicial mudou após a seleção: {name}")
    return selection


def _plot_selection(ranking, folds, output, n_development):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, name):
        fig.get_layout_engine().set(rect=(0, 0.15, 1, 0.85))
        fig.text(
            0.01,
            0.015,
            "Fonte: Inep, ENEM 2023 · desenvolvimento, n="
            + f"{n_development:,}".replace(",", ".")
            + " · teste reservado · DP entre três dobras, não intervalo de confiança",
            fontsize=8,
        )
        for ext in ("png", "svg"):
            fig.savefig(output / f"{name}.{ext}", dpi=300, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5.8), layout="constrained")
    for i, row in ranking.iterrows():
        color = "#087f8c" if row.selected else "#777777"
        ax.errorbar(row.rmse_mean, i, xerr=row.rmse_std, fmt="o", color=color, capsize=4)
        value = f"{row.rmse_mean:.3f} ± {row.rmse_std:.3f}".replace(".", ",")
        ax.text(row.rmse_mean + row.rmse_std + 0.05, i, value, va="center", fontsize=9)
    ax.set_yticks(range(len(ranking)), [f"{r.rank}. {r.label}" for r in ranking.itertuples()])
    ax.invert_yaxis()
    ax.set(
        xlabel="RMSE (pontos): média ± DP; menor é melhor",
        ylabel="Posição entre os sete algoritmos",
        title="Checkpoint 2 — seleção pelo desempenho no desenvolvimento",
        xlim=(ranking.rmse_mean.min() - 0.2, ranking.rmse_mean.max() + 0.8),
    )
    ax.grid(axis="x", alpha=0.2)
    fig.legend(
        handles=[
            Line2D([], [], marker="o", color="#087f8c", linestyle="", label="Selecionado"),
            Line2D([], [], marker="o", color="#777777", linestyle="", label="Demais modelos"),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.065),
        ncols=2,
    )
    save(fig, "ranking_sete_modelos")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), layout="constrained")
    colors = ("#087f8c", "#b95018", "#764b94")
    for i, row in ranking.head(3).iterrows():
        axes[0].errorbar(row.rmse_mean, i, xerr=row.rmse_std, fmt="o", capsize=5, color=colors[i])
        actual = folds.loc[folds.model.eq(row.model)].sort_values("fold")
        axes[1].plot(actual.fold + 1, actual.rmse, "o-", label=row.label, color=colors[i])
    axes[0].set_yticks(range(3), ranking.head(3).label)
    axes[0].invert_yaxis()
    axes[0].set(xlabel="RMSE (pontos)", ylabel="Modelo", title="Média ± DP das três dobras")
    axes[1].set(
        xlabel="Dobra de validação",
        ylabel="RMSE (pontos)",
        title="Desempenho em cada dobra",
        xticks=[1, 2, 3],
    )
    for ax in axes:
        ax.grid(alpha=0.2)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.065), ncols=3)
    save(fig, "comparacao_tres_modelos")
