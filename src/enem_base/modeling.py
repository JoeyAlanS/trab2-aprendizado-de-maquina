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
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVR
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_limits

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
        "knn": pipeline(KNeighborsRegressor(n_neighbors=25, weights="distance", n_jobs=2)),
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
    config: StudyConfig, output: Path, models: tuple[str, ...] = DEFAULT_MODELS
) -> dict:
    if output.exists():
        raise FileExistsError("A comparação já existe; escolha um novo diretório.")
    catalog = model_catalog(config)
    if not models or len(models) != len(set(models)) or set(models) - set(catalog):
        raise ValueError(f"Modelos inválidos. Disponíveis: {sorted(catalog)}")
    frame, provenance = load_development(config)
    x, y = frame[config.features], frame[config.target].to_numpy(dtype=float)
    fold_labels = frame.validation_fold.to_numpy(dtype=int)
    output.mkdir(parents=True)
    manifest = {
        **runtime_metadata(),
        **provenance,
        "status": "running",
        "models": list(models),
        "features": config.features,
        "numeric_imputation": "median fitted within each fold",
        "categorical_encoding": "one-hot with explicit missing category; unknown ignored",
        "evaluated_set": "development_cv",
        "seed": 42,
        "n_splits": 3,
        "std_ddof": 0,
        "all_development_rows": True,
        "test_evaluated": False,
        "parameters": {name: estimator_spec(catalog[name]) for name in models},
    }
    write_json(output / "manifesto.json", manifest)
    records = []
    try:
        with threadpool_limits(limits=2):
            for name in models:
                for fold in range(3):
                    train = np.flatnonzero(fold_labels != fold)
                    validation = np.flatnonzero(fold_labels == fold)
                    estimator = clone(catalog[name])
                    started = time.perf_counter()
                    with warnings.catch_warnings(record=True) as captured:
                        warnings.simplefilter("always")
                        if name == "baseline":
                            estimator.fit(np.zeros((len(train), 1)), y[train])
                            predicted = estimator.predict(np.zeros((len(validation), 1)))
                        else:
                            estimator.fit(x.iloc[train], y[train])
                            predicted = estimator.predict(x.iloc[validation])
                    record = {
                        "experiment_id": f"inicial-{name}",
                        "row_type": "fold",
                        "model": name,
                        "hypothesis": "Comparação inicial do perfil tabular para estimar a nota CN",
                        "features_json": json.dumps(config.features),
                        "parameters_json": json.dumps(manifest["parameters"][name]),
                        "evaluated_set": "development_cv",
                        "fold": fold,
                        **regression_metrics(y[validation], predicted),
                        "elapsed_seconds": time.perf_counter() - started,
                        "n_train": len(train),
                        "n_evaluated": len(validation),
                        "warnings_json": json.dumps([str(w.message) for w in captured]),
                        **provenance,
                    }
                    records.append(record)
                    pd.DataFrame(records).to_csv(output / "experimentos.csv", index=False)
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
        pd.DataFrame(summary).sort_values("rmse_mean").to_csv(output / "resumo_cv.csv", index=False)
        from enem_base.exploration import plot_cv_summary

        plot_cv_summary(
            pd.DataFrame(summary),
            output / "comparacao_cv.png",
            synthetic=config.kind == "synthetic",
        )
        manifest["status"] = "completed"
        manifest["results"] = summary
        write_json(output / "manifesto.json", manifest)
    except Exception as error:
        manifest["status"] = "failed"
        manifest["failure_type"] = type(error).__name__
        write_json(output / "manifesto.json", manifest)
        raise
    return manifest
