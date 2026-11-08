"""Publicação derivada de execuções verificadas; nunca preenche métricas ausentes."""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from enem_base.dashboard import BIN_WIDTH, load_dashboard
from enem_base.evidence import PROVENANCE_KEYS, comparison_rows, read_run
from enem_base.modeling import regression_metrics
from enem_base.provenance import sha256_file, write_json


def validated_predictions(path: Path) -> tuple[pd.DataFrame, dict]:
    manifest = read_run(path, development=False)
    if (
        manifest.get("experiment_kind") != "final_test"
        or manifest.get("evaluated_set") != "test"
        or manifest.get("test_evaluated") is not True
    ):
        raise ValueError("São necessárias previsões da avaliação final registrada.")
    records = manifest.get("metrics", [])
    if len(records) != 3 or {r["model"] for r in records} != {"baseline", "linear", "final"}:
        raise ValueError("A avaliação final deve conter baseline, linear e solução final.")
    predictions = pd.read_csv(path / "previsoes_teste.csv", dtype={"registro_id": "string"})
    if (
        predictions.registro_id.isna().any()
        or predictions.registro_id.duplicated().any()
        or len(predictions) != manifest["n_test"]
    ):
        raise ValueError("IDs ou quantidade de previsões finais inválidos.")
    for record in records:
        if record["n_evaluated"] != len(predictions) or record["evaluated_set"] != "test":
            raise ValueError("População das métricas finais incompatível com as previsões.")
        metrics = regression_metrics(
            predictions.nota_observada, predictions[f"previsao_{record['model']}"]
        )
        if not all(
            np.isclose(value, record[key], rtol=1e-9, atol=1e-9) for key, value in metrics.items()
        ):
            raise ValueError("Métricas finais não correspondem às previsões persistidas.")
    return predictions, manifest


def export_experiments(runs: list[Path], output: Path, final: Path | None = None) -> dict:
    """Consolidar dobras e resumos; somente copiar previsões reais verificadas."""
    if output.exists():
        raise FileExistsError("A publicação já existe; escolha um novo diretório.")
    tables, sources = [], {}
    expected = None
    for path in runs:
        manifest = read_run(path, expected)
        expected = expected or manifest
        rows, manifest = comparison_rows(path, expected)
        tables.append(rows)
        for model, group in rows.groupby("model"):
            summary = group.iloc[0].to_dict()
            summary.update(
                row_type="summary",
                fold=None,
                std_ddof=0,
                n_train=None,
                n_evaluated=int(group.n_evaluated.sum()),
                elapsed_seconds=float(group.elapsed_seconds.sum()),
                diagnostics_json="{}",
                warnings_json="[]",
            )
            for metric in ("rmse", "mae", "r2"):
                summary[metric] = float(group[metric].mean())
                summary[metric + "_std"] = float(group[metric].std(ddof=0))
            summary["model"] = model
            tables.append(pd.DataFrame([summary]))
        sources[str(path)] = sha256_file(path / "manifesto.json")
    if not tables:
        raise ValueError("Informe pelo menos uma comparação concluída.")
    if final is not None:
        _, final_manifest = validated_predictions(final)
        if any(final_manifest[k] != expected[k] for k in PROVENANCE_KEYS):
            raise ValueError("O teste e as comparações usam proveniências diferentes.")
        tables.append(pd.read_csv(final / "experimentos.csv"))
        sources[str(final)] = sha256_file(final / "manifesto.json")
    table = pd.concat(tables, ignore_index=True)
    # O mesmo modelo pode existir em variantes diferentes, mas não a mesma avaliação duas vezes.
    if table.duplicated(["experiment_id", "row_type", "fold", "model"]).any():
        raise ValueError("Há experimentos duplicados entre as execuções selecionadas.")
    output.mkdir(parents=True)
    table.to_csv(output / "experimentos.csv", index=False)
    if final is not None:
        shutil.copyfile(final / "previsoes_teste.csv", output / "previsoes_teste.csv")
    manifest = {
        "status": "completed",
        "inputs": sources,
        "rows": len(table),
        "test_evaluated": final is not None,
        "pending": [] if final is not None else ["avaliação final e previsões reais de teste"],
        "assets": {p.name: sha256_file(p) for p in output.iterdir() if p.is_file()},
    }
    write_json(output / "manifesto.json", manifest)
    return manifest


def generate_figures(
    dashboard: Path,
    comparisons: list[Path],
    output: Path,
    *,
    search: Path | None = None,
    curve: Path | None = None,
    final: Path | None = None,
) -> dict:
    """Gerar somente as figuras cujas evidências estão disponíveis."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if output.exists():
        raise FileExistsError("Figuras existentes; escolha nova saída.")
    data = load_dashboard(dashboard)
    runs = []
    expected = None
    for path in comparisons:
        manifest = read_run(path, expected)
        expected = expected or manifest
        rows, manifest = comparison_rows(path, expected)
        if any(
            manifest[key] != data.manifest[key]
            for key in ("source_sha256", "target", "n_development")
        ):
            raise ValueError("Histograma e modelos têm fonte, alvo ou população diferentes.")
        runs.append((path, rows, manifest))
    # Verificar todas as entradas antes de criar saída; etapas ausentes não são simuladas.
    search_manifest = read_run(search, expected) if search else None
    curve_manifest = read_run(curve, expected) if curve else None
    final_data = validated_predictions(final) if final else None
    if search_manifest and search_manifest.get("experiment_kind") != "search":
        raise ValueError("Manifesto de busca inválido.")
    if curve_manifest and curve_manifest.get("experiment_kind") != "learning_curve":
        raise ValueError("Manifesto de curva inválido.")
    if final_data:
        _, final_manifest = final_data
        if expected and any(final_manifest[k] != expected[k] for k in PROVENANCE_KEYS):
            raise ValueError("O teste e as comparações usam proveniências diferentes.")
        if final_manifest["source_sha256"] != data.manifest["source_sha256"]:
            raise ValueError("O teste e o histograma usam fontes diferentes.")
        if curve_manifest and (
            curve_manifest.get("solution_sha256") != final_manifest.get("solution_sha256")
        ):
            raise ValueError("A curva e o teste usam soluções diferentes.")
    output.mkdir(parents=True)
    generated, pending = [], []

    def save(fig, name, population):
        fig.get_layout_engine().set(rect=(0, 0.09, 1, 0.91))
        fig.text(0.01, 0.01, f"Fonte: Inep, ENEM 2023 · {population}", fontsize=8)
        fig.savefig(output / name, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        generated.append(name)

    histogram = data.cube.groupby("score_bin")["count"].sum()
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    ax.bar(
        histogram.index * BIN_WIDTH,
        histogram.values,
        width=BIN_WIDTH,
        align="edge",
        color="#087f8c",
    )
    ax.set(
        xlabel="Nota de Ciências da Natureza",
        ylabel="Participantes",
        title="Distribuição no desenvolvimento, incluindo notas zero",
    )
    ax.text(
        0.02,
        0.94,
        f"n = {data.manifest['n_development']:,}; zeros = {data.eda['zeros']:,}",
        transform=ax.transAxes,
    )
    save(
        fig,
        "distribuicao_nota_cn.png",
        "desenvolvimento; contagens observadas em intervalos de 25 pontos",
    )

    scores = []
    for _, rows, manifest in runs:
        for model, group in rows.groupby("model"):
            scores.append(
                (f"{model} / {manifest['variant']}", group.rmse.mean(), group.rmse.std(ddof=0))
            )
    if search_manifest:
        scores.extend(
            (f"{r['model']} / busca", r["rmse"], r["rmse_std"]) for r in search_manifest["best"]
        )
    if scores:
        scores.sort(key=lambda row: row[1])
        fig, ax = plt.subplots(figsize=(9, max(4, len(scores) * 0.35)), layout="constrained")
        ax.barh(
            [r[0] for r in scores],
            [r[1] for r in scores],
            xerr=[r[2] for r in scores],
            color="#087f8c",
        )
        ax.invert_yaxis()
        ax.set(
            xlabel="RMSE (pontos), média ± desvio entre 3 dobras",
            title="Comparações efetivamente executadas",
        )
        save(fig, "comparacao_modelos_busca.png", "validação cruzada no desenvolvimento")
    if search is None:
        pending.append("Comparação antes/depois das buscas nos três melhores")

    pca_rows = [r for _, rows, m in runs if m["variant"] == "pca" for r in rows.to_dict("records")]
    if pca_rows:
        fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
        for row in pca_rows:
            learned = json.loads(row["diagnostics_json"])
            if "pca_explained_variance_ratio" not in learned:
                continue
            values = np.cumsum(learned["pca_explained_variance_ratio"])
            ax.plot(
                np.arange(1, len(values) + 1),
                values,
                label=f"{row['model']} dobra {row['fold']}; k={learned['pca_components']}",
            )
        ax.axhline(0.8, linestyle="--", color="#e76f51")
        ax.set(
            xlabel="Componentes",
            ylabel="Variância acumulada",
            title="PCA ajustado no treino de cada dobra",
        )
        ax.legend(fontsize=7)
        save(fig, "pca_variancia_acumulada.png", "treino das dobras do desenvolvimento")
    else:
        pending.append("PCA ajustado em dois regressores")

    if curve:
        rows = pd.read_csv(curve / "curva.csv")
        fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
        for metric, label in [("rmse_train", "Treino"), ("rmse", "Validação")]:
            grouped = rows.groupby("fraction")[metric]
            ax.errorbar(
                rows.groupby("fraction").n_train.mean(),
                grouped.mean(),
                yerr=grouped.std(ddof=0),
                marker="o",
                label=label,
            )
        ax.set(
            xlabel="Participantes no treino da dobra",
            ylabel="RMSE (pontos)",
            title="Curva do modelo congelado",
        )
        ax.legend()
        save(fig, "curva_aprendizado.png", "média e desvio nas três dobras do desenvolvimento")
    else:
        pending.append("Curva de aprendizado do modelo final")

    if final_data:
        predictions, _ = final_data
        observed, predicted = predictions.nota_observada, predictions.previsao_final
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
        axes[0].hexbin(predicted, observed, gridsize=55, mincnt=1)
        low, high = min(observed.min(), predicted.min()), max(observed.max(), predicted.max())
        axes[0].plot([low, high], [low, high], "r--")
        axes[0].set(
            xlabel="Nota prevista", ylabel="Nota observada", title="Todos os participantes do teste"
        )
        axes[1].hexbin(predicted, observed - predicted, gridsize=55, mincnt=1)
        axes[1].axhline(0, color="red", linestyle="--")
        axes[1].set(xlabel="Nota prevista", ylabel="Observado − previsto", title="Resíduos")
        save(fig, "observado_vs_previsto_residuos.png", f"teste final, n={len(predictions):,}")
        groups = pd.read_csv(final / "erros_grupos.csv")
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
        for field, ax in zip(["faixa_nota", "TP_ESCOLA"], axes, strict=True):
            subset = groups.loc[groups.model.eq("final") & groups.group.eq(field)]
            labels = [f"{r.category}\n(n={r.n:,})" for r in subset.itertuples()]
            ax.bar(labels, subset.rmse, color="#087f8c")
            ax.set(ylabel="RMSE (pontos)", title=field)
            ax.tick_params(axis="x", labelsize=8)
        save(fig, "erros_faixa_e_grupos.png", "teste final; faixas definidas no desenvolvimento")
    else:
        pending.extend(
            [
                "Observado versus previsto e resíduos reais do teste",
                "Erros reais do teste por faixa e grupo",
            ]
        )
    manifest = {
        "status": "completed",
        "generated": generated,
        "pending": pending,
        "scientific_final_complete": not pending,
        "inputs": {
            str(p): sha256_file(p / "manifesto.json")
            for p in [dashboard, *comparisons, *[p for p in [search, curve, final] if p]]
        },
        "assets": {name: sha256_file(output / name) for name in generated},
    }
    write_json(output / "manifesto.json", manifest)
    return manifest
