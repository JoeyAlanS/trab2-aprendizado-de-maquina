"""Busca, congelamento, curva e avaliação final com evidências persistidas.

Nenhuma etapa inventa métricas. O teste só pode ser aberto depois de todas as
comparações exigidas, da seleção documentada e da curva do modelo escolhido.
"""

import json
import logging
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from sklearn import config_context
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV, ParameterGrid, PredefinedSplit
from threadpoolctl import threadpool_limits

from enem_base.evidence import (
    GROUP_FIELDS,
    PROVENANCE_KEYS,
    comparison_rows,
    group_errors,
    read_run,
    seal_run,
)
from enem_base.modeling import estimator_spec, model_catalog, regression_metrics
from enem_base.provenance import runtime_metadata, sha256_file, write_json
from enem_base.study import StudyConfig, load_development, verified_dataset
from enem_base.variants import variant_catalog

logger = logging.getLogger(__name__)
FRACTIONS = (0.1, 0.25, 0.5, 0.75, 1.0)


def current_provenance(config: StudyConfig) -> dict:
    _, source = verified_dataset(config)
    split = json.loads((config.splits / "manifesto.json").read_text(encoding="utf-8"))
    if (
        split["source_sha256"] != source["source_sha256"]
        or split["target"] != config.target
        or sha256_file(config.splits / "particoes.parquet") != split["partitions_sha256"]
    ):
        raise ValueError("Partições incompatíveis ou alteradas.")
    return {
        "source_sha256": source["source_sha256"],
        "splits_sha256": split["partitions_sha256"],
        "study_sha256": sha256_file(config.config_path),
        "dictionary_sha256": sha256_file(config.dictionary) if config.dictionary else None,
        "target": config.target,
        "n_development": split["development"],
        "test_evaluated": False,
    }


def initial_comparison(config, paths, provenance):
    tables, seen = [], set()
    for path in paths:
        rows, manifest = comparison_rows(path, provenance)
        if manifest["variant"] != "original" or seen.intersection(rows.model):
            raise ValueError(
                "Comparação inicial exige representação original e modelos sem repetição."
            )
        seen.update(rows.model)
        tables.append(rows)
    required = set(model_catalog(config))
    if seen != required:
        raise ValueError(f"Comparação inicial incompleta. Faltam: {sorted(required - seen)}")
    rows = pd.concat(tables, ignore_index=True)
    ranking = rows.loc[rows.model.ne("baseline")].groupby("model").rmse.mean().sort_values()
    return rows, ranking


def search_space(name):
    grids = {
        "linear": {
            "regressor__fit_intercept": [True, False],
            "regressor__tol": [1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8],
        },
        "ridge": {"regressor__alpha": np.logspace(-3, 3, 12).tolist()},
        "svm": {"regressor__C": [0.01, 0.1, 1.0, 10.0], "regressor__epsilon": [0.0, 0.1, 1.0]},
        "arvore": {
            "regressor__max_depth": [6, 10, 14, 18],
            "regressor__min_samples_leaf": [50, 100, 500],
        },
        "knn": {
            "regressor__n_neighbors": [5, 10, 25, 50, 75, 100],
            "regressor__weights": ["uniform", "distance"],
        },
        "bagging": {
            "regressor__n_estimators": [10, 20, 30],
            "regressor__max_samples": [0.5, 0.7],
            "regressor__estimator__max_depth": [6, 10],
        },
        "pasting": {
            "regressor__n_estimators": [10, 20, 30],
            "regressor__max_samples": [0.5, 0.7],
            "regressor__estimator__max_depth": [6, 10],
        },
        "random_forest": {
            "regressor__max_depth": [8, 12, 16],
            "regressor__max_features": [0.5, 0.8],
            "regressor__min_samples_leaf": [50, 100],
        },
        "boosting": {
            "regressor__learning_rate": [0.03, 0.1, 0.2],
            "regressor__n_estimators": [30, 60, 90, 120],
        },
        "stacking": {"final_estimator__alpha": np.logspace(-3, 3, 12).tolist()},
    }
    return grids[name]


def _start(output, provenance, kind, **extra):
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        **runtime_metadata(),
        **provenance,
        "status": "running",
        "evaluated_set": "development_cv",
        "experiment_kind": kind,
        **extra,
    }
    write_json(output / "manifesto.json", manifest)
    return manifest


def _failed(output, manifest, error):
    manifest.update(status="failed", failure_type=type(error).__name__, failure_message=str(error))
    write_json(output / "manifesto.json", manifest)


def search_models(config: StudyConfig, cv_paths: list[Path], output: Path) -> dict:
    provenance = current_provenance(config)
    _, ranking = initial_comparison(config, cv_paths, provenance)
    top = ranking.index[:3].tolist()
    frame, actual = load_development(config)
    if any(actual[k] != provenance[k] for k in PROVENANCE_KEYS):
        raise ValueError("A origem mudou antes da busca.")
    manifest = _start(
        output,
        provenance,
        "search",
        top_models=top,
        initial_ranking=ranking.to_dict(),
        scoring="neg_root_mean_squared_error",
        cv=3,
        seed=42,
        inputs={str(p): sha256_file(p / "manifesto.json") for p in cv_paths},
    )
    x, y = frame[config.features], frame[config.target].to_numpy(dtype=float)
    folds = PredefinedSplit(frame.validation_fold.to_numpy(dtype=int))
    best = []
    try:
        with threadpool_limits(limits=2), config_context(working_memory=64):
            for name in top:
                grid = search_space(name)
                if len(ParameterGrid(grid)) < 10:
                    raise ValueError("Cada busca deve ter ao menos dez configurações válidas.")
                estimator = model_catalog(config)[name]
                search = GridSearchCV(
                    estimator,
                    grid,
                    cv=folds,
                    n_jobs=1,
                    pre_dispatch=1,
                    refit=False,
                    scoring={
                        "rmse": "neg_root_mean_squared_error",
                        "mae": "neg_mean_absolute_error",
                        "r2": "r2",
                    },
                    return_train_score=True,
                    error_score="raise",
                )
                started = time.perf_counter()
                with warnings.catch_warnings(record=True) as captured:
                    warnings.simplefilter("always")
                    search.fit(x, y)
                elapsed = time.perf_counter() - started
                results = pd.DataFrame(search.cv_results_)
                if not np.isfinite(results.mean_test_rmse).all():
                    raise ValueError("A busca contém configurações sem métricas finitas.")
                index = int(np.argmax(results.mean_test_rmse.to_numpy()))
                parameters = results.iloc[index]["params"]
                results["params"] = results.params.map(lambda p: json.dumps(p, sort_keys=True))
                results.to_csv(output / f"busca_{name}.csv", index=False)
                record = {
                    "model": name,
                    "variant": "original",
                    "parameters": parameters,
                    "configurations": len(results),
                    "rmse": -float(results.iloc[index].mean_test_rmse),
                    "mae": -float(results.iloc[index].mean_test_mae),
                    "r2": float(results.iloc[index].mean_test_r2),
                    "rmse_std": float(results.iloc[index].std_test_rmse),
                    "mae_std": float(results.iloc[index].std_test_mae),
                    "r2_std": float(results.iloc[index].std_test_r2),
                    "elapsed_seconds": elapsed,
                    "warnings": [str(w.message) for w in captured],
                }
                best.append(record)
                write_json(output / "melhores.json", {"models": best})
                logger.info(
                    "Busca %s: %s configurações, RMSE %.4f", name, len(results), record["rmse"]
                )
        manifest.update(status="completed", best=best, spaces={n: search_space(n) for n in top})
        seal_run(output, manifest)
    except Exception as error:
        _failed(output, manifest, error)
        raise
    return manifest


def freeze_solution(config, cv_paths, search_path, variant_paths, output):
    provenance = current_provenance(config)
    original_rows, ranking = initial_comparison(config, cv_paths, provenance)
    search = read_run(search_path, provenance)
    if (
        search.get("experiment_kind") != "search"
        or search.get("top_models") != ranking.index[:3].tolist()
    ):
        raise ValueError("A busca não corresponde aos três melhores regressores iniciais.")
    if len(search.get("best", [])) != 3 or any(r["configurations"] < 10 for r in search["best"]):
        raise ValueError("Resultados de busca incompletos.")
    candidates = [dict(record, source=str(search_path)) for record in search["best"]]
    # A busca pode piorar o resultado: preservar também todos os candidatos iniciais.
    for name, group in original_rows.loc[original_rows.model.ne("baseline")].groupby("model"):
        candidates.append(
            {
                "model": name,
                "variant": "original",
                "parameters": {},
                "rmse": float(group.rmse.mean()),
                "rmse_std": float(group.rmse.std(ddof=0)),
                "source": [str(path) for path in cv_paths],
            }
        )
    covered = {}
    for path in variant_paths:
        rows, manifest = comparison_rows(path, provenance)
        variant = manifest["variant"]
        covered.setdefault(variant, set()).update(rows.model)
        for name, group in rows.groupby("model"):
            if name != "baseline":
                candidates.append(
                    {
                        "model": name,
                        "variant": variant,
                        "parameters": {},
                        "rmse": float(group.rmse.mean()),
                        "rmse_std": float(group.rmse.std(ddof=0)),
                        "source": str(path),
                    }
                )
    required = {"engineered", "selected", "pca", "weighted", "without_socio", "without_uf"}
    if required - set(covered) or len(covered.get("pca", set()) - {"baseline"}) < 2:
        raise ValueError(
            "Faltam engenharia, seleção, PCA em dois regressores, pesos ou duas ablações."
        )
    if not all("ridge" in covered[name] for name in required - {"pca"}):
        raise ValueError("As comparações de representação/ponderação/ablação devem incluir Ridge.")
    selected = min(candidates, key=lambda r: (r["rmse"], r["model"], r["variant"]))
    catalog, _ = variant_catalog(config, selected["variant"])
    estimator = catalog[selected["model"]].set_params(**selected["parameters"])
    manifest = _start(output, provenance, "selection")
    solution = {
        "recipe": selected,
        "estimator": estimator_spec(estimator),
        "criterion": "Menor RMSE médio entre originais, buscas e variantes no desenvolvimento",
        "score_edges": [0, 400, 500, 600, 700, "+inf"],
        "group_fields": list(GROUP_FIELDS),
        "learning_fractions": list(FRACTIONS),
        "inputs": {
            str(p): sha256_file(p / "manifesto.json")
            for p in [*cv_paths, search_path, *variant_paths]
        },
    }
    write_json(output / "solution.json", solution)
    manifest.update(status="completed", selected=selected)
    seal_run(output, manifest)
    return manifest


def _solution(config, path, provenance):
    manifest = read_run(path, provenance)
    if manifest.get("experiment_kind") != "selection":
        raise ValueError("Exige solução congelada pelo comando freeze-solution.")
    solution = json.loads((path / "solution.json").read_text(encoding="utf-8"))
    recipe = solution["recipe"]
    catalog, _ = variant_catalog(config, recipe["variant"])
    estimator = catalog[recipe["model"]].set_params(**recipe["parameters"])
    if estimator_spec(estimator) != solution["estimator"]:
        raise ValueError("O estimador mudou depois do congelamento da solução.")
    return estimator, solution


def learning_curve(config, solution_path, output):
    frame, provenance = load_development(config)
    estimator, _ = _solution(config, solution_path, provenance)
    solution_hash = sha256_file(solution_path / "solution.json")
    manifest = _start(output, provenance, "learning_curve", solution_sha256=solution_hash)
    x, y = frame[config.features], frame[config.target].to_numpy(dtype=float)
    rows = []
    try:
        with threadpool_limits(limits=2), config_context(working_memory=64):
            for fold in range(3):
                labels = frame.validation_fold.to_numpy(dtype=int)
                training = np.random.RandomState(42).permutation(np.flatnonzero(labels != fold))
                validation = np.flatnonzero(labels == fold)
                for fraction in FRACTIONS:
                    indices = training[: max(1, int(len(training) * fraction))]
                    current = clone(estimator)
                    started = time.perf_counter()
                    current.fit(x.iloc[indices], y[indices])
                    train_metrics = regression_metrics(y[indices], current.predict(x.iloc[indices]))
                    val_metrics = regression_metrics(
                        y[validation], current.predict(x.iloc[validation])
                    )
                    rows.append(
                        {
                            "fold": fold,
                            "fraction": fraction,
                            "n_train": len(indices),
                            "n_evaluated": len(validation),
                            "rmse_train": train_metrics["rmse"],
                            **val_metrics,
                            "elapsed_seconds": time.perf_counter() - started,
                        }
                    )
                    pd.DataFrame(rows).to_csv(output / "curva.csv", index=False)
                    logger.info(
                        "Curva: dobra %s, %.0f%%, RMSE %.4f",
                        fold,
                        fraction * 100,
                        val_metrics["rmse"],
                    )
        manifest["status"] = "completed"
        seal_run(output, manifest)
    except Exception as error:
        _failed(output, manifest, error)
        raise
    return manifest


def _load_final_test(config):
    dataset, _ = verified_dataset(config)
    partitions = pd.read_parquet(config.splits / "particoes.parquet")
    selected = partitions.loc[partitions.partition.eq("test"), [config.identifier]]
    predicate = ds.field(config.identifier).isin(selected[config.identifier].tolist())
    frame = dataset.to_table(
        columns=[config.identifier, config.target, *config.features],
        filter=predicate,
    ).to_pandas(categories=list(config.categorical))
    frame = selected.merge(frame, on=config.identifier, how="left", validate="one_to_one")
    if frame[config.target].isna().any():
        raise ValueError("Teste contém participante sem alvo observado.")
    for name in config.numeric:
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype("Float64")
    return frame


def evaluate_final(config, solution_path, curve_path, output):
    development, provenance = load_development(config)
    estimator, solution = _solution(config, solution_path, provenance)
    curve = read_run(curve_path, provenance)
    solution_hash = sha256_file(solution_path / "solution.json")
    if (
        curve.get("experiment_kind") != "learning_curve"
        or curve.get("solution_sha256") != solution_hash
    ):
        raise ValueError("A curva não corresponde à solução congelada.")
    points = pd.read_csv(curve_path / "curva.csv")
    if len(points) != 15 or set(zip(points.fold, points.fraction, strict=True)) != {
        (f, p) for f in range(3) for p in FRACTIONS
    }:
        raise ValueError("Curva incompleta: são necessários cinco tamanhos em três dobras.")
    if output.exists():
        raise FileExistsError("Avaliação existente; não sobrescrever resultados.")
    # Trava persistente por partição: falha exige investigação, nunca nova avaliação silenciosa.
    lock = config.splits / "avaliacao_final.json"
    with lock.open("x", encoding="utf-8") as stream:
        json.dump(
            {
                "status": "started",
                "output": str(output.resolve()),
                "solution_sha256": solution_hash,
            },
            stream,
        )
    manifest = _start(output, provenance, "final_test", solution_sha256=solution_hash)
    manifest.update(test_evaluated=True, evaluated_set="test", recipe=solution["recipe"])
    write_json(output / "manifesto.json", manifest)
    try:
        test = _load_final_test(config)
        predicted = test[
            [config.identifier, config.target, *[n for n in GROUP_FIELDS if n in test]]
        ].copy()
        predicted = predicted.rename(
            columns={config.identifier: "registro_id", config.target: "nota_observada"}
        )
        x, y = development[config.features], development[config.target].to_numpy(dtype=float)
        x_test = test[config.features]
        catalog = model_catalog(config)
        records, groups = [], []
        with threadpool_limits(limits=2), config_context(working_memory=64):
            for name, model in [
                ("baseline", catalog["baseline"]),
                ("linear", catalog["linear"]),
                ("final", estimator),
            ]:
                started = time.perf_counter()
                if name == "baseline":
                    model.fit(np.zeros((len(y), 1)), y)
                    values = model.predict(np.zeros((len(test), 1)))
                else:
                    model.fit(x, y)
                    values = model.predict(x_test)
                predicted[f"previsao_{name}"] = values
                records.append(
                    {
                        "experiment_id": f"{output.name}-test-{name}",
                        "model": name,
                        "row_type": "test_final",
                        "variant": solution["recipe"]["variant"] if name == "final" else "original",
                        "features_json": json.dumps(
                            variant_catalog(config, solution["recipe"]["variant"])[1]
                            if name == "final"
                            else config.features
                        ),
                        **provenance,
                        "test_evaluated": True,
                        "evaluated_set": "test",
                        "n_train": len(development),
                        "n_evaluated": len(test),
                        **regression_metrics(test[config.target], values),
                        "elapsed_seconds": time.perf_counter() - started,
                        "parameters_json": json.dumps(estimator_spec(model)),
                    }
                )
                groups.extend(group_errors(test, values, config.target, name))
        predicted.to_csv(output / "previsoes_teste.csv", index=False)
        pd.DataFrame(records).to_csv(output / "experimentos.csv", index=False)
        pd.DataFrame(groups).to_csv(output / "erros_grupos.csv", index=False)
        manifest.update(status="completed", n_test=len(test), metrics=records)
        seal_run(output, manifest)
        write_json(
            lock,
            {
                "status": "completed",
                "output": str(output.resolve()),
                "solution_sha256": solution_hash,
            },
        )
    except Exception as error:
        _failed(output, manifest, error)
        write_json(
            lock,
            {
                "status": "failed",
                "output": str(output.resolve()),
                "failure_type": type(error).__name__,
            },
        )
        raise
    return manifest
