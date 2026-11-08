"""Catálogo obrigatório e comparação inicial nas dobras persistidas.

Nenhuma rotina deste módulo carrega ou avalia o conjunto de teste.
"""

import json
import logging
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from sklearn import config_context
from sklearn.base import BaseEstimator, clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (
    BaggingRegressor,
    GradientBoostingRegressor,
    RandomForestRegressor,
    StackingRegressor,
)
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVR
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_limits

from enem_base.neighbors import ExactProfileKNeighborsRegressor
from enem_base.preprocessing import build_preprocessor
from enem_base.provenance import runtime_metadata, write_json
from enem_base.study import StudyConfig, load_development

logger = logging.getLogger(__name__)
DEFAULT_MODELS = ("baseline", "linear", "ridge", "arvore")


def estimator_spec(value):
    """Descrição JSON completa, sem truncamento ou endereços de funções em memória."""
    if isinstance(value, BaseEstimator):
        return {
            "class": f"{type(value).__module__}.{type(value).__qualname__}",
            "parameters": {
                key: estimator_spec(item) for key, item in value.get_params(deep=False).items()
            },
        }
    if isinstance(value, np.generic):
        return estimator_spec(value.item())
    if isinstance(value, dict):
        return {str(key): estimator_spec(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [estimator_spec(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return {"special_float": str(value)}
    if callable(value):
        return {"callable": f"{value.__module__}.{value.__qualname__}"}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return {"class": f"{type(value).__module__}.{type(value).__qualname__}", "repr": repr(value)}


def model_catalog(config: StudyConfig) -> dict:
    def pipeline(regressor):
        return Pipeline(
            [
                (
                    "preparation",
                    build_preprocessor(
                        list(config.numeric),
                        list(config.categorical),
                        identifier=config.identifier,
                        target=config.target,
                    ),
                ),
                ("regressor", regressor),
            ]
        )

    tree = DecisionTreeRegressor(max_depth=8, min_samples_leaf=100, random_state=42)
    catalog = {
        "baseline": DummyRegressor(strategy="mean"),
        "linear": pipeline(LinearRegression(tol=1e-6)),
        "ridge": pipeline(Ridge(alpha=1.0, solver="lsqr", tol=1e-5)),
        "svm": pipeline(LinearSVR(random_state=42, dual="auto", max_iter=5000, tol=1e-3)),
        "arvore": pipeline(
            DecisionTreeRegressor(max_depth=12, min_samples_leaf=100, random_state=42)
        ),
        "knn": pipeline(
            ExactProfileKNeighborsRegressor(n_neighbors=25, weights="distance", n_jobs=2)
        ),
        "bagging": pipeline(
            BaggingRegressor(
                estimator=tree,
                n_estimators=20,
                max_samples=0.7,
                bootstrap=True,
                random_state=42,
                n_jobs=2,
            )
        ),
        "pasting": pipeline(
            BaggingRegressor(
                estimator=tree,
                n_estimators=20,
                max_samples=0.7,
                bootstrap=False,
                random_state=42,
                n_jobs=2,
            )
        ),
        "random_forest": pipeline(
            RandomForestRegressor(
                n_estimators=30,
                max_depth=12,
                min_samples_leaf=100,
                max_features=0.8,
                random_state=42,
                n_jobs=2,
            )
        ),
        "boosting": pipeline(
            GradientBoostingRegressor(
                n_estimators=60, max_depth=2, min_samples_leaf=100, random_state=42
            )
        ),
    }
    # Cada base conserva o seu próprio Pipeline nas dobras internas do stacking.
    catalog["stacking"] = StackingRegressor(
        estimators=[("linear", clone(catalog["linear"])), ("arvore", clone(catalog["arvore"]))],
        final_estimator=Ridge(alpha=1.0),
        cv=KFold(3, shuffle=True, random_state=42),
        n_jobs=1,
    )
    return catalog


def regression_metrics(observed, predicted) -> dict:
    observed, predicted = np.asarray(observed, dtype=float), np.asarray(predicted, dtype=float)
    if (
        observed.shape != predicted.shape
        or observed.ndim != 1
        or not len(observed)
        or not np.isfinite(observed).all()
        or not np.isfinite(predicted).all()
    ):
        raise ValueError("Métricas exigem vetores finitos, não vazios e da mesma dimensão.")
    return {
        "rmse": float(root_mean_squared_error(observed, predicted)),
        "mae": float(mean_absolute_error(observed, predicted)),
        "r2": float(r2_score(observed, predicted))
        if len(observed) > 1 and np.var(observed)
        else None,
    }


def compare_models(
    config: StudyConfig,
    output: Path,
    models: tuple[str, ...] = DEFAULT_MODELS,
    *,
    variant: str = "original",
    resume: bool = False,
) -> dict:
    if output.exists() and not resume:
        raise FileExistsError("A comparação já existe; escolha um novo diretório.")
    from enem_base.checkpointing import run_lock

    with run_lock(output):
        return _compare_models(config, output, models, variant=variant, resume=resume)


def _compare_models(config, output, models, *, variant, resume):
    from enem_base.checkpointing import (
        atomic_json,
        identifiers_digest,
        load_fold,
        prediction_blocks,
        save_fold,
    )
    from enem_base.evidence import PROVENANCE_KEYS, group_errors, read_run, seal_run
    from enem_base.variants import fitted_diagnostics, variant_catalog

    catalog, feature_names = variant_catalog(config, variant)
    if not models or len(models) != len(set(models)) or set(models) - set(catalog):
        raise ValueError(f"Modelos inválidos. Disponíveis: {sorted(catalog)}")
    frame, provenance = load_development(config)
    # O scanner nacional não precisa manter buffers de leitura durante o treinamento.
    pa.default_memory_pool().release_unused()
    x, y = frame[config.features], frame[config.target].to_numpy(dtype=float)
    fold_labels = frame.validation_fold.to_numpy(dtype=int)
    previous = None
    if output.exists():
        if not resume:
            raise FileExistsError("A comparação já existe.")
        previous = json.loads((output / "manifesto.json").read_text(encoding="utf-8"))
        if (
            previous.get("models") != list(models)
            or previous.get("variant") != variant
            or previous.get("test_evaluated") is not False
            or any(previous.get(k) != provenance[k] for k in PROVENANCE_KEYS)
            or previous["parameters"] != {n: estimator_spec(catalog[n]) for n in models}
        ):
            raise ValueError("A retomada exige as mesmas fontes, partições, modelos e parâmetros.")
        if previous["status"] == "completed":
            return read_run(output, provenance)
    output.mkdir(parents=True, exist_ok=resume)
    manifest = {
        **runtime_metadata(),
        **provenance,
        "status": "running",
        "models": list(models),
        "features": feature_names,
        "variant": variant,
        "experiment_kind": "comparison",
        "numeric_imputation": "median fitted within each fold",
        "categorical_encoding": "one-hot with explicit missing category; unknown ignored",
        "evaluated_set": "development_cv",
        "seed": 42,
        "n_splits": 3,
        "std_ddof": 0,
        "all_development_rows": True,
        "test_evaluated": False,
        "parameters": {name: estimator_spec(catalog[name]) for name in models},
        "execution": {
            "threadpool_limit": 2,
            "working_memory_mib": 64,
            "knn_prediction_batch_rows": 2048,
            "knn_search": (
                "ExactProfileKNeighborsRegressor; binary exhaustive search "
                "plus numeric distance; no subsampling"
            ),
        },
    }
    if previous:
        for package, version in previous["dependencies"].items():
            if manifest["dependencies"].get(package) != version:
                raise ValueError(f"Dependência mudou antes da retomada: {package}")
        history = output / "retomadas"
        attempt = len(list(history.glob("*.json"))) + 1
        atomic_json(history / f"antes-{attempt:03d}.json", previous)
        manifest["resumed_from_status"] = previous["status"]
        manifest["resume_attempt"] = attempt
    legacy_records, legacy_groups = [], pd.DataFrame()
    if previous and not list((output / "dobras").glob("*.json")):
        if (output / "experimentos.csv").exists():
            legacy = pd.read_csv(output / "experimentos.csv")
            if legacy.duplicated(["model", "fold"]).any():
                raise ValueError("A execução parcial tem dobras duplicadas.")
            legacy_records = legacy.astype(object).where(legacy.notna(), None).to_dict("records")
            legacy_groups = pd.read_csv(output / "erros_grupos.csv")
    atomic_json(output / "manifesto.json", manifest)
    records = []
    groups = []
    try:
        with threadpool_limits(limits=2), config_context(working_memory=64):
            for name in models:
                estimator = None
                for fold in range(3):
                    train = np.flatnonzero(fold_labels != fold)
                    validation = np.flatnonzero(fold_labels == fold)
                    context = {
                        **provenance,
                        "model": name,
                        "fold": fold,
                        "variant": variant,
                        "parameters": manifest["parameters"][name],
                        "dependencies": manifest["dependencies"],
                        "implementation": {
                            k: v
                            for k, v in manifest["source_code_sha256"].items()
                            if Path(k).name
                            in {"preprocessing.py", "neighbors.py", "variants.py", "study.py"}
                        },
                        "train_ids_sha256": identifiers_digest(
                            frame.iloc[train][config.identifier]
                        ),
                        "validation_ids_sha256": identifiers_digest(
                            frame.iloc[validation][config.identifier]
                        ),
                    }
                    fold_path = output / "dobras" / f"{name}-{fold}.json"
                    preserved = None
                    if fold_path.exists():
                        preserved = load_fold(fold_path, context)
                    else:
                        old = [
                            r for r in legacy_records if r["model"] == name and r["fold"] == fold
                        ]
                        if old:
                            old_groups = legacy_groups.loc[
                                legacy_groups.model.eq(name) & legacy_groups.fold.eq(fold)
                            ]
                            preserved = (
                                old[0],
                                old_groups.astype(object)
                                .where(old_groups.notna(), None)
                                .to_dict("records"),
                            )
                    if preserved:
                        record, fold_groups = preserved
                        if (
                            record["n_train"] != len(train)
                            or record["n_evaluated"] != len(validation)
                            or record["evaluated_set"] != "development_cv"
                            or record["row_type"] != "fold"
                            or record["model"] != name
                            or record["fold"] != fold
                            or record["test_evaluated"] is not False
                            or any(record[k] != provenance[k] for k in PROVENANCE_KEYS)
                            or json.loads(record["parameters_json"]) != manifest["parameters"][name]
                            or not np.isfinite(
                                [record[k] for k in ("rmse", "mae", "r2", "elapsed_seconds")]
                            ).all()
                            or not fold_groups
                            or not pd.DataFrame(fold_groups)
                            .groupby("group")
                            .n.sum()
                            .eq(len(validation))
                            .all()
                        ):
                            raise ValueError(f"Dobra parcial inconsistente: {name}/{fold}")
                        if not fold_path.exists():
                            save_fold(fold_path, context, record, fold_groups)
                        records.append(record)
                        groups.extend(fold_groups)
                        logger.info("Preservando %s, dobra %s, já concluída", name, fold)
                        continue
                    estimator = clone(catalog[name])
                    started = time.perf_counter()
                    cached_prediction_seconds = prior_fit_seconds = 0.0
                    reused_blocks = 0
                    logger.info(
                        "Iniciando %s, dobra %s: %s treino, %s validação",
                        name,
                        fold,
                        len(train),
                        len(validation),
                    )
                    with warnings.catch_warnings(record=True) as captured:
                        warnings.simplefilter("always")
                        if name == "baseline":
                            estimator.fit(np.zeros((len(train), 1)), y[train])
                            predicted = estimator.predict(np.zeros((len(validation), 1)))
                        else:
                            estimator.fit(x.iloc[train], y[train])
                            if name == "knn":
                                fit_seconds = time.perf_counter() - started
                                predicted = np.empty(len(validation), dtype=float)
                                blocks = prediction_blocks(
                                    estimator,
                                    x.iloc[validation],
                                    frame.iloc[validation][config.identifier],
                                    output / "predicoes_parciais" / f"dobra-{fold}",
                                    context,
                                    fit_seconds,
                                )
                                for (
                                    start,
                                    stop,
                                    values,
                                    reused,
                                    saved_seconds,
                                    saved_prior_fit_seconds,
                                ) in blocks:
                                    prior_fit_seconds = saved_prior_fit_seconds
                                    predicted[start:stop] = values
                                    if reused:
                                        cached_prediction_seconds += saved_seconds
                                        reused_blocks += 1
                                    logger.info(
                                        "KNN dobra %s: %s/%s previsões reais; bloco reutilizado=%s",
                                        fold,
                                        stop,
                                        len(validation),
                                        reused,
                                    )
                            else:
                                predicted = estimator.predict(x.iloc[validation])
                    record = {
                        "experiment_id": f"{output.name}-{variant}-{name}",
                        "row_type": "fold",
                        "model": name,
                        "hypothesis": "Comparação inicial do perfil tabular para estimar a nota CN",
                        "features_json": json.dumps(feature_names),
                        "preparation_json": json.dumps({"variant": variant}),
                        "variant": variant,
                        "parameters_json": json.dumps(manifest["parameters"][name]),
                        "evaluated_set": "development_cv",
                        "fold": fold,
                        **regression_metrics(y[validation], predicted),
                        "elapsed_seconds": time.perf_counter()
                        - started
                        + cached_prediction_seconds
                        + prior_fit_seconds,
                        "prediction_blocks_reused": reused_blocks,
                        "n_train": len(train),
                        "n_evaluated": len(validation),
                        "warnings_json": json.dumps([str(w.message) for w in captured]),
                        "diagnostics_json": json.dumps(fitted_diagnostics(estimator)),
                        "conclusion": "Métricas observadas; comparar média e variação das dobras.",
                        **provenance,
                    }
                    fold_groups = group_errors(
                        frame.iloc[validation], predicted, config.target, name, fold
                    )
                    save_fold(fold_path, context, record, fold_groups)
                    records.append(record)
                    groups.extend(fold_groups)
                    for filename, values in [
                        ("erros_grupos.csv", groups),
                        ("experimentos.csv", records),
                    ]:
                        temporary = output / (filename + ".tmp")
                        pd.DataFrame(values).to_csv(temporary, index=False, lineterminator="\n")
                        temporary.replace(output / filename)
                    logger.info(
                        "%s, dobra %s: RMSE %.3f; %.1f s; avisos=%s",
                        name,
                        fold,
                        record["rmse"],
                        record["elapsed_seconds"],
                        len(captured),
                    )
                del estimator
        results = pd.DataFrame(records)
        results.to_csv(output / "experimentos.csv", index=False)
        summary = []
        for name, group in results.groupby("model", sort=False):
            row = {
                "model": name,
                "evaluated_set": "development_cv",
                "n_splits": 3,
                "elapsed_seconds": float(group.elapsed_seconds.sum()),
                "std_ddof": 0,
                "warning_count": int(sum(len(json.loads(v)) for v in group.warnings_json)),
            }
            for metric in ("rmse", "mae", "r2"):
                values = group[metric].dropna()
                row[metric + "_mean"] = float(values.mean()) if len(values) else None
                row[metric + "_std"] = float(values.std(ddof=0)) if len(values) else None
            summary.append(row)
        pd.DataFrame(summary).sort_values("rmse_mean").to_csv(
            output / "resumo_cv.csv", index=False, lineterminator="\n"
        )
        from enem_base.exploration import plot_cv_summary

        plot_cv_summary(
            pd.DataFrame(summary),
            output / "comparacao_cv.png",
            synthetic=config.kind == "synthetic",
        )
        manifest["status"] = "completed"
        manifest["results"] = summary
        pd.DataFrame(groups).to_csv(output / "erros_grupos.csv", index=False)
        seal_run(output, manifest)
    except Exception as error:
        manifest["status"] = "failed"
        manifest["failure_type"] = type(error).__name__
        write_json(output / "manifesto.json", manifest)
        raise
    return manifest
