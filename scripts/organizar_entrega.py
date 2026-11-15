"""Publicar a entrega a partir das execuções verificadas, sem treinar ou prever novamente."""

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from matplotlib import pyplot as plt

from enem_base.modeling import regression_metrics
from enem_base.provenance import sha256_file, write_json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "resultados/ciencias_natureza"
FINAL = BASE / "checkpoint-4-2026-11-07"
INITIAL = ROOT / "resultados/publicacao-checkpoint-1-2026-11-06/experimentos.csv"
KEYS = ["source_sha256", "splits_sha256", "study_sha256", "dictionary_sha256", "target"]
MODELS = {
    "baseline",
    "linear",
    "ridge",
    "arvore",
    "svm",
    "knn",
    "bagging",
    "pasting",
    "random_forest",
    "boosting",
    "stacking",
}
PREPARATION = {
    "numeric": "Q005: mediana, indicador de ausência e StandardScaler ajustados no treino",
    "categorical": "39 campos: ausência explícita e OneHotEncoder(handle_unknown='ignore')",
    "leakage_control": "Transformações reaprendidas somente no treino de cada dobra",
}
DERIVED = {"COMPUTADORES_POR_MORADOR", "ACESSO_DIGITAL", "ESCOLARIDADE_PAIS_MAX"}
HYPOTHESES = {
    "engineered": "Recursos por morador, acesso digital e escolaridade reduzem o RMSE?",
    "selected": "Selecionar 75% dos atributos codificados preserva ou melhora o erro?",
    "pca": "Preservar 80% da variância com PCA mantém a informação preditiva?",
    "weighted": "Ponderar faixas raras do alvo melhora o desempenho sem piorar o erro global?",
    "without_socio": "Retirar o questionário socioeconômico aumenta o erro do Ridge?",
    "without_uf": "Retirar a UF de aplicação aumenta o erro do Ridge?",
}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def preparation(variant, features, model):
    if model == "baseline":
        return encoded({"used_X": False, "target": "média somente do alvo do treino"})
    numeric = [x for x in features if x == "Q005" or x in DERIVED]
    return encoded(
        {
            "variant": variant,
            "numeric_columns": numeric,
            "numeric": "mediana + indicador + StandardScaler no treino"
            if numeric
            else "sem numéricas",
            "categorical_columns": [x for x in features if x not in numeric],
            "categorical": "ausência explícita + one-hot; categorias desconhecidas ignoradas",
            "engineering": "três fórmulas em variants.py"
            if variant in {"engineered", "selected"}
            else None,
            "selection": "f_regression, 75%, somente no treino" if variant == "selected" else None,
            "pca": "centrado, 80% da variância, somente no treino" if variant == "pca" else None,
            "weights": "inverso da frequência de 10 faixas do treino"
            if variant == "weighted"
            else None,
            "leakage_control": PREPARATION["leakage_control"],
        }
    )


def summaries(frame):
    """Média/DP populacional das três dobras; nunca resumir o teste como CV."""
    first = frame.iloc[0].to_dict()
    first.update(row_type="summary", fold=None, std_ddof=0, warnings_json="[]")
    for metric in ["rmse", "mae", "r2", "rmse_train", "mae_train", "r2_train"]:
        if metric in frame:
            first[metric] = frame[metric].mean()
            first[metric + "_std"] = frame[metric].std(ddof=0)
    for name in ["elapsed_seconds", "fit_seconds", "score_seconds", "n_train", "n_evaluated"]:
        if name in frame:
            first[name] = frame[name].mean()
    # Participantes/tamanhos e tempos por dobra continuam nas linhas fold.
    if "origin" in frame:
        first["origin"] = encoded(sorted(set(frame.origin.astype(str))))
    return first


def build_tables():
    initial = pd.read_csv(INITIAL)
    initial["stage"] = np.where(initial.variant.eq("original"), "comparacao_inicial", "variantes")
    initial["source_path"] = str(INITIAL.relative_to(ROOT))
    initial["time_scope"] = "tempo registrado na execução original; ver diagnostics_json"
    original = initial.query("variant == 'original' and row_type == 'fold'")
    assert set(original.model) == MODELS
    assert original.groupby("model").size().eq(3).all()
    initial["preparation_json"] = initial.apply(
        lambda r: preparation(r.variant, json.loads(r.features_json), r.model), axis=1
    )
    original_means = original.groupby("model").rmse.mean()
    for model, mean in original_means.items():
        mask = initial.variant.eq("original") & initial.model.eq(model)
        initial.loc[mask, "hypothesis"] = (
            "Usar a média do treino como referência sem features."
            if model == "baseline"
            else f"O regressor {model} reduz o erro em relação à média nas mesmas dobras?"
        )
        initial.loc[mask, "conclusion"] = (
            f"Referência: RMSE médio {mean:.6f}; aprende apenas a média do treino."
            if model == "baseline"
            else f"RMSE médio {mean:.6f}; redução de "
            f"{original_means['baseline'] - mean:.6f} pontos ante a média. "
            "Não demonstra significância das diferenças entre regressores."
        )
    for variant in HYPOTHESES:
        mask = initial.variant.eq(variant)
        initial.loc[mask, "hypothesis"] = HYPOTHESES[variant]
        for model in initial.loc[mask, "model"].unique():
            group_mask = mask & initial.model.eq(model)
            mean = initial.loc[group_mask & initial.row_type.eq("fold"), "rmse"].mean()
            delta = mean - original_means[model]
            direction = "aumentou" if delta > 0 else "reduziu"
            initial.loc[group_mask, "conclusion"] = (
                f"RMSE médio {direction} {abs(delta):.6f} pontos ante o mesmo modelo original. "
                "Comparação descritiva nas mesmas dobras; sem teste de significância."
            )
    provenance = initial.iloc[0][KEYS].to_dict()
    features = initial.loc[
        initial.variant.eq("original") & initial.model.eq("stacking"), "features_json"
    ].iloc[0]
    initial.loc[initial.model.eq("baseline"), "features_json"] = "[]"
    records = initial.to_dict("records")
    protocol = read(FINAL / "protocolo_buscas.json")
    for model in ["stacking", "ridge", "linear", "svm", "random_forest"]:
        directory = FINAL / "buscas" / model
        folds = pd.read_csv(directory / "metricas_dobras.csv")
        ranking = pd.read_csv(directory / "comparacao_configuracoes.csv").set_index("candidate_id")
        for candidate, group in folds.groupby("candidate_id", sort=True):
            values = []
            for row in group.to_dict("records"):
                fit = read(
                    directory
                    / "modelos_ajustados"
                    / f"config-{candidate:02d}-dobra-{row['fold']}.json"
                )
                row.update(
                    **provenance,
                    stage="busca",
                    row_type="fold",
                    variant="original",
                    experiment_id=f"busca-{model}-{candidate:02d}",
                    evaluated_set="development_cv",
                    test_evaluated=False,
                    features_json=features,
                    preparation_json=encoded(PREPARATION),
                    hypothesis="Ajustar hiperparâmetros reduz o RMSE no desenvolvimento?",
                    tuning_parameters_json=row["parameters_json"],
                    parameters_json=encoded(protocol["candidates"][model][candidate]["estimator"]),
                    n_evaluated=row["n_validation"],
                    fit_seconds=fit["elapsed_this_fit_seconds"],
                    elapsed_seconds=fit["elapsed_this_fit_seconds"],
                    time_scope="ajuste da dobra; reuso de bases/cache documentado",
                    gridsearch_mean_fit_seconds=ranking.loc[candidate, "mean_fit_time"],
                    gridsearch_mean_score_seconds=ranking.loc[candidate, "mean_score_time"],
                    source_path=str((directory / "metricas_dobras.csv").relative_to(ROOT)),
                    conclusion=(
                        "Comparar média/DP no desenvolvimento; "
                        "ganhos pequenos não provam relevância."
                    ),
                )
                values.append(row)
            records.extend(values)
            records.append(summaries(pd.DataFrame(values)))
    recipes = read(FINAL / "congelamento/receitas.json")["recipes"]
    for stage, parent in [
        ("curva_inicial", BASE / "checkpoint-3-2026-11-06"),
        ("curva_final", FINAL / "curvas_finais"),
    ]:
        for model in ["stacking", "svm", "random_forest"]:
            path = parent / model / "curvas.csv"
            frame = pd.read_csv(path)
            params = (
                recipes[model]
                if stage == "curva_final"
                else json.loads(original.loc[original.model.eq(model), "parameters_json"].iloc[0])
            )
            frame["stage"] = stage
            frame["row_type"] = "fold"
            frame["variant"] = "original"
            frame["evaluated_set"] = "development_cv"
            frame["n_evaluated"] = frame.n_validation
            frame["hypothesis"] = (
                "Como erros de treino/validação variam com a quantidade de treino?"
            )
            frame["features_json"] = features
            frame["preparation_json"] = encoded(PREPARATION)
            frame["parameters_json"] = encoded(params)
            frame["source_path"] = str(path.relative_to(ROOT))
            frame["time_scope"] = (
                "custos registrados no ponto, com reuso identificado; "
                "sem novo ajuste nesta publicação"
            )
            frame["conclusion"] = (
                "Diagnóstico no desenvolvimento; não demonstra generalização para outro ano."
            )
            if "elapsed_seconds" not in frame:
                frame["elapsed_seconds"] = frame.fit_seconds + frame.score_seconds
            for key, value in provenance.items():
                frame[key] = value
            for fraction, group in frame.groupby("fraction", sort=True):
                group = group.copy()
                group["experiment_id"] = f"{stage}-{model}-{fraction:g}"
                records.extend(group.to_dict("records"))
                records.append(summaries(group))
    test = pd.read_csv(FINAL / "avaliacao_final/experimentos.csv")
    test["stage"] = "teste_final"
    test["source_path"] = str((FINAL / "avaliacao_final/experimentos.csv").relative_to(ROOT))
    test["hypothesis"] = "Avaliar as receitas já congeladas nos mesmos participantes reservados."
    test["preparation_json"] = encoded(PREPARATION)
    test.loc[test.model.eq("baseline"), "preparation_json"] = preparation(
        "original", [], "baseline"
    )
    test.loc[test.model.eq("baseline"), "features_json"] = "[]"
    test["time_scope"] = (
        "ajuste no desenvolvimento completo e predição no teste; custos não isolados de hardware"
    )
    test["conclusion"] = (
        "Resultado final descritivo; não usar para reabrir seleção ou hiperparâmetros."
    )
    records.extend(test.to_dict("records"))
    all_rows = pd.DataFrame(records)
    assert len(all_rows) == 437
    assert len(all_rows.query("evaluated_set == 'test'")) == 5
    for key in KEYS:
        assert all_rows[key].nunique() == 1
    assert np.isfinite(all_rows[["rmse", "mae", "r2", "elapsed_seconds"]]).all().all()
    return all_rows


def export_columns():
    source = pq.read_schema(ROOT / "dados/processed/enem2023-v1/part-00000.parquet").names
    rows = []
    variants = [
        "original",
        "engineered",
        "selected",
        "pca",
        "weighted",
        "without_socio",
        "without_uf",
    ]
    for variant in variants:
        folder = "cv-recuperado-v2" if variant == "original" else variant + "-v2"
        manifest = read(BASE / folder / "manifesto.json")
        for name in source:
            state = "entrada" if name in manifest["features"] else "fora_de_X"
            role = {
                "NU_INSCRICAO": "controle; nunca preditor",
                "NU_NOTA_CN": "alvo; nunca preditor",
            }
            rows.append(
                dict(
                    variant=variant,
                    fold=None,
                    column=name,
                    scope="coluna_fonte",
                    action=state,
                    reason=role.get(name, "seleção explícita do protocolo"),
                )
            )
        for name in set(manifest["features"]) - set(source):
            rows.append(
                dict(
                    variant=variant,
                    fold=None,
                    column=name,
                    scope="engenharia",
                    action="criada",
                    reason="fórmula em src/enem_base/variants.py",
                )
            )
    selected = pd.read_csv(BASE / "selected-v2/experimentos.csv")
    for row in selected.query("row_type == 'fold'").itertuples():
        for name in json.loads(row.diagnostics_json)["selected_features"]:
            rows.append(
                dict(
                    variant="selected",
                    fold=row.fold,
                    column=name,
                    scope="coluna_codificada",
                    action="selecionada",
                    reason="SelectPercentile(f_regression, percentile=75) no treino da dobra",
                )
            )
    return pd.DataFrame(rows).sort_values(["variant", "scope", "fold", "column"])


def complete_comparison(experiments):
    table = experiments.query("stage == 'comparacao_inicial' and row_type == 'summary'")
    table = table.sort_values("rmse")
    table[
        ["model", "rmse", "rmse_std", "mae", "mae_std", "r2", "r2_std", "elapsed_seconds"]
    ].to_csv(ROOT / "resultados/comparacao_modelos.csv", index=False)
    labels = {
        "baseline": "Média (baseline)",
        "linear": "Regressão linear",
        "ridge": "Ridge",
        "arvore": "Árvore de decisão",
        "svm": "SVM linear",
        "knn": "KNN",
        "bagging": "Bagging",
        "pasting": "Pasting",
        "random_forest": "Random Forest",
        "boosting": "Gradient Boosting",
        "stacking": "Stacking",
    }
    with plt.rc_context({"font.size": 15, "svg.fonttype": "none"}):
        fig, ax = plt.subplots(figsize=(11, 5.8))
        y = np.arange(len(table))
        colors = ["#087f8c" if i < 3 else "#566575" for i in y]
        ax.barh(y, table.rmse, color=colors, height=0.65)
        ax.errorbar(table.rmse, y, xerr=table.rmse_std, fmt="none", ecolor="#151f2c", capsize=3)
        ax.set(
            yticks=y,
            yticklabels=[labels[x] for x in table.model],
            xlabel="RMSE médio ± DP nas três dobras (pontos; menor é melhor)",
            xlim=(0, 100),
        )
        ax.invert_yaxis()
        for i, row in enumerate(table.itertuples()):
            ax.text(
                row.rmse + 0.8, i, f"{row.rmse:.3f}".replace(".", ","), va="center", fontsize=13
            )
        ax.spines[["top", "right"]].set_visible(False)
        ax.xaxis.grid(True, alpha=0.15)
        ax.set_axisbelow(True)
        fig.suptitle("Comparação completa dos modelos obrigatórios", fontsize=16, y=0.98)
        fig.text(
            0.02,
            0.025,
            "Fonte: Inep, ENEM 2023. Desenvolvimento: 2.153.941 participantes.\n"
            "Mesmas partições; DP populacional (ddof=0). Teste reservado fora desta comparação.",
            fontsize=9,
        )
        fig.tight_layout(rect=(0, 0.09, 1, 0.95))
        for extension in ["png", "svg"]:
            fig.savefig(ROOT / f"resultados/figuras/18_comparacao_completa.{extension}", dpi=300)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()
    args.verification = args.verification.resolve()
    verification = read(args.verification / "auditoria_experimentos.json")
    if verification["status"] != "passed" or verification["new_training"]:
        raise ValueError("Conferência independente das execuções não aprovada.")
    inputs = [
        INITIAL,
        args.verification / "auditoria_experimentos.json",
        FINAL / "avaliacao_final/experimentos.csv",
        FINAL / "avaliacao_final/previsoes_teste.csv",
    ]
    experiments = build_tables()
    experiments.to_csv(ROOT / "resultados/experimentos.csv", index=False)
    export_columns().to_csv(ROOT / "resultados/colunas.csv", index=False)
    predictions = pd.read_csv(inputs[-1], dtype={"registro_id": "string"})
    partitions = pd.read_parquet(ROOT / "dados/splits/ciencias-natureza-v1/particoes.parquet")
    expected = partitions.loc[partitions.partition.eq("test"), "NU_INSCRICAO"].astype(str)
    assert predictions.registro_id.is_unique and len(predictions) == len(expected) == 538486
    assert set(predictions.registro_id) == set(expected)
    for row in experiments.query("stage == 'teste_final'").itertuples():
        scores = regression_metrics(
            predictions.nota_observada, predictions[f"previsao_{row.model}"]
        )
        for name, actual in scores.items():
            np.testing.assert_allclose(actual, getattr(row, name), rtol=0, atol=1e-9)
    # Preservar bytes e todas as colunas já aprovadas, inclusive os grupos de análise.
    shutil.copyfile(inputs[-1], ROOT / "resultados/previsoes_teste.csv")
    figures = ROOT / "resultados/figuras"
    figures.mkdir(exist_ok=True)
    source = BASE / "checkpoint-5-2026-11-07/figuras"
    images = sorted([*source.glob("*.png"), *source.glob("*.svg")])
    assert len(images) == 34
    for path in images:
        shutil.copyfile(path, figures / path.name)
    table_source = BASE / "checkpoint-5-2026-11-07/tabelas"
    table_output = ROOT / "resultados/tabelas"
    table_output.mkdir(exist_ok=True)
    tables = sorted(table_source.glob("*.csv"))
    for path in tables:
        shutil.copyfile(path, table_output / path.name)
    complete_comparison(experiments)
    inputs += [ROOT / p for p in sorted(set(experiments.source_path))]
    inputs += [source / x.name for x in images]
    inputs += tables
    outputs = [
        ROOT / "resultados" / name
        for name in [
            "experimentos.csv",
            "colunas.csv",
            "previsoes_teste.csv",
            "comparacao_modelos.csv",
        ]
    ]
    outputs += [figures / x.name for x in images]
    outputs += [table_output / x.name for x in tables]
    outputs += [figures / f"18_comparacao_completa.{ext}" for ext in ["png", "svg"]]
    write_json(
        ROOT / "resultados/manifesto_entrega.json",
        {
            "status": "passed",
            "new_training": False,
            "new_test_predictions": False,
            "experiment_rows": len(experiments),
            "test_rows": len(predictions),
            "stages": experiments.groupby(["stage", "row_type"])
            .size()
            .rename("rows")
            .reset_index()
            .to_dict("records"),
            "inputs": {str(p.relative_to(ROOT)): sha256_file(p) for p in inputs},
            "outputs": {str(p.relative_to(ROOT)): sha256_file(p) for p in outputs},
            "large_local_files": ["resultados/previsoes_teste.csv"],
        },
    )
    print(
        f"Entrega conferida: {len(experiments)} registros; "
        f"{len(predictions)} previsões; 18 figuras PNG/SVG."
    )


if __name__ == "__main__":
    main()
